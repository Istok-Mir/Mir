from __future__ import annotations
from typing import  Any, Dict, Generic, List, Optional, TypeVar, Union
import asyncio
import json

from lsp.capabilities import ServerCapability
from sublime_plugin import sublime
import datetime

from .dotted_dict import DottedDict
from .types import ErrorCodes, LSPAny
from .lsp_requests import LspRequest, LspNotification

StringDict = Dict[str, Any]
PayloadLike = Union[List[StringDict], StringDict, None]
CONTENT_LENGTH = 'Content-Length: '
ENCODING = "utf-8"


class Error(Exception):
    def __init__(self, code: ErrorCodes, message: str) -> None:
        super().__init__(message)
        self.code = code

    def to_lsp(self) -> StringDict:
        return {"code": self.code, "message": super().__str__()}

    @classmethod
    def from_lsp(cls, d: StringDict) -> 'Error':
        return Error(d["code"], d["message"])

    def __str__(self) -> str:
        return f"{super().__str__()} ({self.code})"


def make_response(request_id: Any, params: PayloadLike) -> StringDict:
    return {"jsonrpc": "2.0", "id": request_id, "result": params}


def make_error_response(request_id: Any, err: Error) -> StringDict:
    return {"jsonrpc": "2.0", "id": request_id, "error": err.to_lsp()}


def make_notification(method: str, params: PayloadLike) -> StringDict:
    return {"jsonrpc": "2.0", "method": method, "params": params}


def make_request(method: str, request_id: Any, params: PayloadLike) -> StringDict:
    return {"jsonrpc": "2.0", "method": method, "id": request_id, "params": params}


class StopLoopException(Exception):
    pass


def create_message(payload: PayloadLike) :
    body = json.dumps(
        payload,
        check_circular=False,
        ensure_ascii=False,
        separators=(",", ":")).encode(ENCODING)
    return (
        f"Content-Length: {len(body)}\r\n".encode(ENCODING),
        "Content-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n".encode(ENCODING),
        body
    )


class MessageType:
    error = 1
    warning = 2
    info = 3
    log = 4


class Request():
    def __init__(self) -> None:
        self.cv = asyncio.Condition()
        self.result: Optional[PayloadLike] = None
        self.error: Optional[Error] = None

    async def on_result(self, params: PayloadLike) -> None:
        self.result = params
        async with self.cv:
            self.cv.notify()

    async def on_error(self, err: Error) -> None:
        self.error = err
        async with self.cv:
            self.cv.notify()

def content_length(line: bytes) -> Optional[int]:
    if line.startswith(b'Content-Length: '):
        _, value = line.split(b'Content-Length: ')
        value = value.strip()
        try:
            return int(value)
        except ValueError:
            raise ValueError("Invalid Content-Length header: {}".format(value))
    return None


class ServerCapabilities(DottedDict):
    def has(self, server_capability: ServerCapability) -> bool:
        value = self.get(server_capability)
        return value is not False and value is not None

    def register(
        self,
        server_capability: ServerCapability,
        options: dict[str, Any]
    ) -> None:
        capability = self.get(server_capability)
        if isinstance(capability, str):
            msg = f"{server_capability} is already registered. Skipping."
            print(msg)
            return
        self.set(server_capability, options)

    def unregister(
        self,
        server_capability: ServerCapability,
    ) -> None:
        capability = self.get(server_capability)
        if not isinstance(capability, str):
            msg = f"{server_capability} is not a string. Skipping."
            print(msg)
            return
        self.remove(server_capability)


class LanguageServer:
    def __init__(self, name: str, cmd: str) -> None:
        self.name = name
        self.send = LspRequest(self.send_request)
        self.notify = LspNotification(self.send_notification)
        self.capabilities = ServerCapabilities()

        self.cmd = cmd
        self.process = None
        self._received_shutdown = False

        self.request_id = 1
        self._response_handlers: Dict[Any, Request] = {}
        self.on_request_handlers = {}
        self.on_notification_handlers = {}
        self.logs = []

    async def start(self):
        try:
            self.process = await asyncio.create_subprocess_shell(
                self.cmd,
                stdout=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            print('Error when creating the subprocess:', e)
        asyncio.get_event_loop().create_task(self.run_forever())

    def stop(self):
        if self.process:
            self.process.kill()

    async def shutdown(self):
        await self.send.shutdown()
        self._received_shutdown = True
        self.notify.exit()
        if self.process and self.process.stdout:
            self.process.stdout.set_exception(StopLoopException())

    def _log(self, message: str) -> None:
        self.send_notification("window/logMessage",
                     {"type": MessageType.info, "message": message})

    async def run_forever(self) -> bool:
        try:
            while self.process and self.process.stdout and not self.process.stdout.at_eof():
                line = await self.process.stdout.readline()
                if not line:
                    continue
                try:
                    num_bytes = content_length(line)
                except ValueError:
                    continue
                if num_bytes is None:
                    continue
                while line and line.strip():
                    line = await self.process.stdout.readline()
                if not line:
                    continue
                body = await self.process.stdout.readexactly(num_bytes)
                asyncio.get_event_loop().create_task(self._handle_body(body))
        except(BrokenPipeError, ConnectionResetError, StopLoopException):
            pass
        return self._received_shutdown

    async def _handle_body(self, body: bytes) -> None:
        try:
            await self._receive_payload(json.loads(body))
        except IOError as ex:
            self._log(f"malformed {ENCODING}: {ex}")
        except UnicodeDecodeError as ex:
            self._log(f"malformed {ENCODING}: {ex}")
        except json.JSONDecodeError as ex:
            self._log(f"malformed JSON: {ex}")

    async def _receive_payload(self, payload: StringDict) -> None:
        try:
            if "method" in payload:
                if "id" in payload:
                    await self._request_handler(payload)
                else:
                    await self._notification_handler(payload)
            elif "id" in payload:
                await self._response_handler(payload)
            else:
                self._log(f"Unknown payload type: {payload}")
        except Exception as err:
            self._log(f"Error handling server payload: {err}")

    def send_notification(self, method: str, params: Optional[dict] = None):
        self.logs.append(f'{method} notification | client -> {self.name}\nParams: {sublime.encode_value(params)}')
        self._send_payload_sync(
            make_notification(method, params))

    def send_response(self, request_id: Any, params: PayloadLike) -> None:
        asyncio.get_event_loop().create_task(self._send_payload(
            make_response(request_id, params)))

    def send_error_response(self, request_id: Any, err: Error) -> None:
        self.logs.append(f'Error response ({request_id}) | client -> {self.name}\nReason: {err}')
        asyncio.get_event_loop().create_task(self._send_payload(
            make_error_response(request_id, err)))

    async def send_request(self, method: str, params: Optional[dict] = None):
        request = Request()
        request_id = self.request_id
        self.request_id += 1
        self._response_handlers[request_id] = request
        start_of_req = datetime.datetime.now()
        async with request.cv:
            self.logs.append(f'{method} request ({request_id}) | client -> {self.name}\nParams: {sublime.encode_value(params)}')
            await self._send_payload(make_request(method, request_id, params))
            await request.cv.wait()
        if isinstance(request.error, Error):
            self.logs.append(f'{method} error response ({request_id}) | {self.name} -> client\nReason:\n{request.error}')
            raise request.error
        end_of_req = datetime.datetime.now()
        self.logs.append(f'{method} response ({request_id}) - {round((end_of_req-start_of_req).total_seconds(), 2)}s | {self.name} -> client \n{request.result}')
        print('logs', "\n\n".join(self.logs))
        return request.result

    def _send_payload_sync(self, payload: StringDict) -> None:
        if not self.process or not self.process.stdin:
            return
        msg = create_message(payload)
        try:
            self.process.stdin.writelines(msg)
        except Exception as e:
            print('Error while writing:', e)

    async def _send_payload(self, payload: StringDict) -> None:
        if not self.process or not self.process.stdin:
            return
        msg = create_message(payload)
        try:
            self.process.stdin.writelines(msg)
            await self.process.stdin.drain()
        except Exception as e:
            print('Error while writing:', e)

    def on_request(self, method: str, cb):
        self.on_request_handlers[method] = cb

    def on_notification(self, method: str, cb):
        self.on_notification_handlers[method] = cb

    async def _response_handler(self, response: StringDict) -> None:
        request = self._response_handlers.pop(response["id"])
        if "result" in response and "error" not in response:
            await request.on_result(response["result"])
        elif "result" not in response and "error" in response:
            await request.on_error(Error.from_lsp(response["error"]))
        else:
            await request.on_error(Error(ErrorCodes.InvalidRequest, ''))

    async def _request_handler(self, response: StringDict) -> None:
        method = response.get("method", "")
        params = response.get("params")
        request_id = response.get("id")
        handler = self.on_request_handlers.get(method)
        if not handler:
            self.send_error_response(request_id, Error(
                    ErrorCodes.MethodNotFound, "method '{}' not handled on client.".format(method)))
            return
        try:
            self.logs.append(f'{method} request ({request_id}) | {self.name} -> client\nParams: {sublime.encode_value(params)}')
            res = await handler(OnRequestPayload(self, params))
            self.logs.append(f'{method} response ({request_id}) | client -> {self.name}\n{sublime.encode_value(res)}')
            self.send_response(request_id, res)
        except Error as ex:
            self.send_error_response(request_id, ex)
        except Exception as ex:
            self.send_error_response(request_id, Error(ErrorCodes.InternalError, str(ex)))

    async def _notification_handler(self, response: StringDict) -> None:
        method = response.get("method", "")
        params = response.get("params")
        handler = self.on_notification_handlers.get(method)
        self.logs.append(f'{method} notification | {self.name} -> client\nParams: {sublime.encode_value(params)}')
        if not handler:
            self._log(f"unhandled {method}")
            return
        try:
            handler(params)
        except asyncio.CancelledError:
            return
        except Exception as ex:
            if not self._received_shutdown:
                self.send_notification("window/logMessage", {"type": MessageType.error, "message": str(ex)})

T = TypeVar('T')
class OnRequestPayload(Generic[T]):
    def __init__(self, server: LanguageServer, params: T) -> None:
        self.server =server
        self.params =params
