from __future__ import annotations
from typing import  Any, Dict, Generic, List, Optional, TypeVar, Union, cast
import asyncio
import json

from event_loop import run_future
from lsp.capabilities import ServerCapability
from sublime_plugin import sublime
import datetime

from .dotted_dict import DottedDict
from .types import ErrorCodes, LSPAny, LogMessageParams, MessageType, RegistrationParams
from .lsp_requests import LspRequest, LspNotification
from .capabilities import client_capabilities, method_to_capability


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

class CommmunicationLogs:
    def __init__(self, name: str):
        self.name = name
        self.logs: list[str] = []
        self.panel = sublime.active_window().create_output_panel(name)

    def append(self, log: str):
        self.logs.append(log)
        self.panel.run_command("append", {
            'characters': log + '\n\n'
        })
        self.panel.clear_undo_stack()

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
        self.communcation_logs = CommmunicationLogs(name)

        # respond to server requests and notifications
        self.on_request('workspace/configuration', workspace_configuration)
        self.on_request('client/registerCapability', register_capability)
        self.on_notification('window/logMessage', on_log_message)

    async def start(self):
        try:
            self.process = await asyncio.create_subprocess_shell(
                self.cmd,
                stdout=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
            )
            asyncio.get_event_loop().create_task(self.run_forever())

            folders = sublime.active_window().folders()
            root_folder = folders[0] if folders else ''
            initialize_result = await self.send.initialize({
                'processId': self.process.pid,
                'rootUri': 'file://' + root_folder,
                'rootPath': root_folder,
                'workspaceFolders': [{'name': 'OLSP', 'uri': 'file://' + root_folder}],
                'capabilities': client_capabilities,
                'initializationOptions': {'completionDisableFilterText': True, 'disableAutomaticTypingAcquisition': False, 'locale': 'en', 'maxTsServerMemory': 0, 'npmLocation': '', 'plugins': [], 'preferences': {'allowIncompleteCompletions': True, 'allowRenameOfImportPath': True, 'allowTextChangesInNewFiles': True, 'autoImportFileExcludePatterns': [], 'disableSuggestions': False, 'displayPartsForJSDoc': True, 'excludeLibrarySymbolsInNavTo': True, 'generateReturnInDocTemplate': True, 'importModuleSpecifierEnding': 'auto', 'importModuleSpecifierPreference': 'shortest', 'includeAutomaticOptionalChainCompletions': True, 'includeCompletionsForImportStatements': True, 'includeCompletionsForModuleExports': True, 'includeCompletionsWithClassMemberSnippets': True, 'includeCompletionsWithInsertText': True, 'includeCompletionsWithObjectLiteralMethodSnippets': True, 'includeCompletionsWithSnippetText': True, 'includePackageJsonAutoImports': 'auto', 'interactiveInlayHints': True, 'jsxAttributeCompletionStyle': 'auto', 'lazyConfiguredProjectsFromExternalProject': False, 'organizeImportsAccentCollation': True, 'organizeImportsCaseFirst': False, 'organizeImportsCollation': 'ordinal', 'organizeImportsCollationLocale': 'en', 'organizeImportsIgnoreCase': 'auto', 'organizeImportsNumericCollation': False, 'providePrefixAndSuffixTextForRename': True, 'provideRefactorNotApplicableReason': True, 'quotePreference': 'auto', 'useLabelDetailsInCompletionEntries': True}, 'tsserver': {'fallbackPath': '', 'logDirectory': '', 'logVerbosity': 'off', 'path': '', 'trace': 'off', 'useSyntaxServer': 'auto'}}
            })
            self.capabilities.assign(cast(dict, initialize_result['capabilities']))
            self.notify.initialized({})
        except Exception as e:
            print('Error when creating the subprocess:', e)

    def stop(self):
        run_future(self.shutdown())
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
                     {"type": MessageType.Info, "message": message})

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
        self.communcation_logs.append(f'Send notification "{method}"\nParams: {sublime.encode_value(params)}')
        self._send_payload_sync(
            make_notification(method, params))

    def send_response(self, request_id: Any, params: PayloadLike) -> None:
        asyncio.get_event_loop().create_task(self._send_payload(
            make_response(request_id, params)))

    def send_error_response(self, request_id: Any, err: Error) -> None:
        self.communcation_logs.append(f'Send error response ({request_id})\n{err}')
        asyncio.get_event_loop().create_task(self._send_payload(
            make_error_response(request_id, err)))

    async def send_request(self, method: str, params: Optional[dict] = None):
        request = Request()
        request_id = self.request_id
        self.request_id += 1
        self._response_handlers[request_id] = request
        start_of_req = datetime.datetime.now()
        async with request.cv:
            self.communcation_logs.append(f'Sending request "{method}" ({request_id})\nParams: {sublime.encode_value(params)}')
            await self._send_payload(make_request(method, request_id, params))
            await request.cv.wait()
        end_of_req = datetime.datetime.now()
        duration = round((end_of_req-start_of_req).total_seconds(), 2)
        if isinstance(request.error, Error):
            self.communcation_logs.append(f'Recieved error response "{method}" ({request_id}) - {duration}s\n{request.error}')
            raise request.error
        self.communcation_logs.append(f'Recieved response "{method}" ({request_id}) - {duration}s\n{request.result}')
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
            self.communcation_logs.append(f'Received request "{method}" ({request_id})\nParams: {sublime.encode_value(params)}')
            res = await handler(OnRequestPayload(self, params))
            self.communcation_logs.append(f'Sending response "{method}" ({request_id})\n{sublime.encode_value(res)}')
            self.send_response(request_id, res)
        except Error as ex:
            self.send_error_response(request_id, ex)
        except Exception as ex:
            self.send_error_response(request_id, Error(ErrorCodes.InternalError, str(ex)))

    async def _notification_handler(self, response: StringDict) -> None:
        method = response.get("method", "")
        params = response.get("params")
        handler = self.on_notification_handlers.get(method)
        self.communcation_logs.append(f'Received notification "{method}"\nParams: {sublime.encode_value(params)}')
        if not handler:
            self._log(f"unhandled {method}")
            return
        try:
            handler(OnNotificationPayload(self, params))
        except asyncio.CancelledError:
            return
        except Exception as ex:
            if not self._received_shutdown:
                self.send_notification("window/logMessage", {"type": MessageType.Error, "message": str(ex)})


T = TypeVar('T')
class OnRequestPayload(Generic[T]):
    def __init__(self, server: LanguageServer, params: T) -> None:
        self.server =server
        self.params =params

T = TypeVar('T')
class OnNotificationPayload(Generic[T]):
    def __init__(self, server: LanguageServer, params: T) -> None:
        self.server =server
        self.params =params


def on_log_message(payload: OnNotificationPayload[LogMessageParams]):
    message_type = {
        MessageType.Error: 'Error',
        MessageType.Warning: 'Warning',
        MessageType.Info: 'Info',
        MessageType.Debug: 'Debug',
        MessageType.Log: 'Log',
    }.get(payload.params.get('type', MessageType.Log))
    print(f"{message_type}: {payload.params.get('message')}")

async def workspace_configuration(payload: OnRequestPayload):
    return []

async def register_capability(payload: OnRequestPayload[RegistrationParams]):
    params = payload.params
    registrations = params["registrations"]
    for registration in registrations:
        capability_path = method_to_capability(registration["method"])
        options = registration.get("registerOptions")
        if not isinstance(options, dict):
            options = {}
        payload.server.capabilities.register(capability_path, options)

