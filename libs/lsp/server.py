from __future__ import annotations
import os

from .server_request_and_notification_handlers import attach_server_request_and_notification_handlers
from .capabilities import CLIENT_CAPABILITIES, ServerCapabilities
from .lsp_requests import LspRequest, LspNotification, Request
from .types import DidChangeTextDocumentParams, ErrorCodes, MessageType
from ..event_loop import run_future
from .communcation_logs import CommmunicationLogs, format_payload
from .view_to_lsp import file_name_to_uri, get_view_uri
from pathlib import Path
from sublime_plugin import sublime
from typing import  Any, Callable, Dict, Literal, Optional, TypedDict, cast
from typing_extensions import NotRequired
from wcmatch.glob import BRACE
from .dotted_dict import DottedDict
from wcmatch.glob import globmatch
from wcmatch.glob import GLOBSTAR
import asyncio
import datetime
import json
import shutil
from .diagnostic_collection import DiagnosticCollection
from .types import TextDocumentContentChangeEvent, LSPAny

ENCODING = "utf-8"


class Error(Exception):
    def __init__(self, code: ErrorCodes, message: str) -> None:
        super().__init__(message)
        self.code = code

    def to_lsp(self) -> dict:
        return {"code": self.code, "message": super().__str__()}

    @classmethod
    def from_lsp(cls, d: dict) -> 'Error':
        return Error(d["code"], d["message"])

    def __str__(self) -> str:
        return f"{super().__str__()} ({self.code})"


def make_response(request_id: Any, params: Any) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": params}


def make_error_response(request_id: Any, err: Error) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": err.to_lsp()}


def make_notification(method: str, params: Any) -> dict:
    if params is None:
        return {"jsonrpc": "2.0", "method": method }
    return {"jsonrpc": "2.0", "method": method, "params": params}


def make_request(method: str, request_id: Any, params: Any) -> dict:
    if params is None:
        return {"jsonrpc": "2.0", "method": method, "id": request_id }
    return {"jsonrpc": "2.0", "method": method, "id": request_id, "params": params}


class StopLoopException(Exception):
    pass


def create_message(payload: Any) :
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

def content_length(line: bytes) -> Optional[int]:
    if line.startswith(b'Content-Length: '):
        _, value = line.split(b'Content-Length: ')
        value = value.strip()
        try:
            return int(value)
        except ValueError:
            raise ValueError("Invalid Content-Length header: {}".format(value))
    return None


class ActivationEvents(TypedDict):
    selector: str | Literal['*']
    on_uri: NotRequired[list[str]]
    '''
    If specified the server will only start for the given uri.
    and will shutdown as soon as the last view that matches the uri is closed.
    '''
    workspace_contains: NotRequired[list[str]] # todo: implement


def is_applicable_view(view: sublime.View, activation_events: ActivationEvents) -> bool:
        selector = activation_events['selector']
        if selector == '*':
            return True
        matches_selector = view.match_selector(0,selector)
        if not matches_selector:
            return False
        on_uri = activation_events.get('on_uri')
        if on_uri:
            matches_on_uri = matches_activation_event_on_uri(view, activation_events)
            if not matches_on_uri:
                return False
        return True


def matches_activation_event_on_uri(view: sublime.View, activation_events: ActivationEvents) -> bool:
    on_uri = activation_events.get('on_uri')
    if on_uri:
        uri = get_view_uri(view)
        for uri_pattern in on_uri:
            if not globmatch(uri, uri_pattern, flags=GLOBSTAR | BRACE):
                return False
        return True
    return False


class NotificationHandler(TypedDict):
    method: str
    cb: Callable[[dict|None],None]


def register_language_server(server: LanguageServer):
    from .manage_servers import ManageServers
    if server.name in [s.name for s in ManageServers.language_servers_pluguins]:
        print(f'register_language_server {server.name} is skipped because it was already registred.')
        return
    ManageServers.language_servers_pluguins.append(server)


def unregister_language_server(server: LanguageServer):
    from .manage_servers import ManageServers
    [s.stop() for servers in ManageServers.language_servers_per_window.values() for s in servers if s.name == server.name]
    ManageServers.language_servers_pluguins = [s for s in ManageServers.language_servers_pluguins if s.name != server.name]


class LanguageServer:
    name: str
    cmd: str
    activation_events: ActivationEvents

    @classmethod
    def setup(cls):
        if not hasattr(cls, 'name'):
            raise Exception(f'Specify a `name` static property for {cls.__name__}.')
        if not hasattr(cls, 'cmd'):
            raise Exception(f'Specify a `cmd` static property` for {cls.__name__}.')
        if not hasattr(cls, 'activation_events'):
            raise Exception(f'Specify a `activation_events` static property` for {cls.__name__}.')
        register_language_server(cls)

    @classmethod
    def cleanup(cls):
        unregister_language_server(cls)

    def before_initialize(self):
        ...

    def __init__(self) -> None:
        self.status: Literal['off', 'initializing','ready'] = 'off'
        self.send = LspRequest(self.send_request)
        self.notify = LspNotification(self.send_notification)
        self.capabilities = ServerCapabilities()
        self.view: sublime.View = sublime.View(-1)
        self.settings = DottedDict()
        self.initialization_options = DottedDict()
        self.diagnostics = DiagnosticCollection()
        self._process = None
        self._received_shutdown = False

        self.pending_changes: dict[int, DidChangeTextDocumentParams] = {}
        self.request_id = 1
        # equests sent from client
        self._response_handlers: Dict[Any, Request] = {}
        self._cache_responses: Dict[str, Request] = {}
        # requests and notifications sent from server
        self.on_request_handlers = {}
        self.on_notification_handlers: list[NotificationHandler] = []
        # logs
        self._communcation_logs: CommmunicationLogs = CommmunicationLogs(self.name)
        attach_server_request_and_notification_handlers(self)

    async def start(self, view: sublime.View):
        self.view = view
        self.settings.update(view.settings().to_dict())
        window = view.window()
        if not window:
            raise Exception('A window must exists now')
        self._communcation_logs = CommmunicationLogs(self.name, window)

        self.before_initialize()
        try:
            self.status = 'initializing'
            if not shutil.which(self.cmd.split()[0]):
                raise RuntimeError(f"Command not found: {self.cmd}")
            self._process = await asyncio.create_subprocess_shell(
                self.cmd,
                stdout=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            run_future(self._run_forever())

            folders = window.folders() if window else []
            first_foder = folders[0] if folders else ''
            first_folder_uri = file_name_to_uri(first_foder)
            initialize_result = await self.send.initialize({
                'processId': self._process.pid,
                'workspaceFolders': [{'name': Path(f).name, 'uri':file_name_to_uri(f)} for f in folders],
                'rootUri': first_folder_uri,  # @deprecated in favour of `workspaceFolders`
                'rootPath': first_foder,  # @deprecated in favour of `rootUri`.
                'capabilities': CLIENT_CAPABILITIES,
                'initializationOptions': self.initialization_options.get()
            }).result
            self.capabilities.assign(cast(dict, initialize_result['capabilities']))
            self.notify.initialized({})
            self.status = 'ready'

            def update_settings_on_change():
                self.settings.update(view.settings().to_dict())
                self.notify.workspace_did_change_configuration({'settings': {}}) # https://github.com/microsoft/language-server-protocol/issues/567#issuecomment-420589320

            self.view.settings().add_on_change('', update_settings_on_change)
            self.notify.workspace_did_change_configuration({'settings': {}}) # https://github.com/microsoft/language-server-protocol/issues/567#issuecomment-420589320
        except Exception as e:
            print(f'Mir ({self.name}) Error while creating subprocess.', e)
            self.status = 'off'

    def stop(self):
        self.view.settings().clear_on_change('')
        run_future(self.shutdown())

    async def shutdown(self):
        await self.send.shutdown().result
        self._received_shutdown = True
        self.notify.exit()
        if self._process and self._process.stdout:
            self._process.stdout.set_exception(StopLoopException())
        if self._process:
            self._process.kill()
            self._process = None
        self.status = 'off'

    def _log(self, message: str) -> None:
        self.send_notification("window/logMessage",
                     {"type": MessageType.Info, "message": message})

    async def _run_forever(self) -> bool:
        try:
            while self._process and self._process.stdout and not self._process.stdout.at_eof():
                line = await self._process.stdout.readline()
                if not line:
                    continue
                try:
                    num_bytes = content_length(line)
                except ValueError:
                    continue
                if num_bytes is None:
                    continue
                while line and line.strip():
                    line = await self._process.stdout.readline()
                if not line:
                    continue
                body = await self._process.stdout.readexactly(num_bytes)
                run_future(self._handle_body(body))
        except (BrokenPipeError, ConnectionResetError, StopLoopException) as e:
            print(f'Mir ({self.name}) Error in run_forever. ', e)
            pass
        return self._received_shutdown

    async def _handle_body(self, body: bytes) -> None:
        try:
            await self._receive_payload(json.loads(body))
        except IOError as ex:
            self._log(f"Mir ({self.name})  malformed {ENCODING}: {ex}")
        except UnicodeDecodeError as ex:
            self._log(f"Mir ({self.name})  malformed {ENCODING}: {ex}")
        except json.JSONDecodeError as ex:
            self._log(f"Mir ({self.name})  malformed JSON: {ex}")
        except Exception as e:
            print(f"Mir ({self.name}) Error in _handle_body. ", e)

    async def _receive_payload(self, payload: dict) -> None:
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

    def invalidete_cache(self, uri: str):
        for key, _ in list(self._cache_responses.items()):
            if f"uri:{uri};" in key:
                del self._cache_responses[key]

    def send_notification(self, method: str, params: Optional[dict] = None):
        if method == 'textDocument/didChange' and params and 'textDocument' in params:
            self.invalidete_cache(params['textDocument']['uri'])
        if method == 'textDocument/didClose' and params and 'textDocument' in params:
            self.invalidete_cache(params['textDocument']['uri'])
        self._communcation_logs.append(f'Send notification "{method}"\nParams: {format_payload(params)}')
        self._send_payload_sync(
            make_notification(method, params))

    async def send_response(self, request_id: Any, params: Any) -> None:
        await self._send_payload(
            make_response(request_id, params))

    async def send_error_response(self, request_id: Any, err: Error) -> None:
        self._communcation_logs.append(f'Send error response ({request_id})\n{err}')
        try:
            await self._send_payload(
                make_error_response(request_id, err))
        except Exception as e:
            print(f'Mir ({self.name}) Error in send_error_response.', e)

    def send_did_change_text_document(self):
        pending_changes = list(self.pending_changes.items())
        self.pending_changes = {}
        for _, did_change_text_document_params in pending_changes:
            self.notify.did_change_text_document(did_change_text_document_params)

    def send_request(self, method: str, params: Optional[dict] = None):
        self.send_did_change_text_document()
        request_id = self.request_id
        self.request_id += 1
        response = Request(self, request_id, method, params)
        cache = self._cache_responses.get(response.cache_key)
        if cache:
            self._communcation_logs.append(f'Sending request "{method}" ({request_id})\nParams: {format_payload(params)}')
            response.result.set_result(cache)
            self._communcation_logs.append(f'Cache hit "{response.method}" ({response.id}) - {0}s\nResponse: {format_payload(cache)}')
        else:
            self._response_handlers[request_id] = response
            self._communcation_logs.append(f'Sending request "{method}" ({request_id})\nParams: {format_payload(params)}')
            run_future(self._send_payload(make_request(method, request_id, params)))
        return response

    def _send_payload_sync(self, payload: dict) -> None:
        if not self._process or not self._process.stdin:
            return
        msg = create_message(payload)
        try:
            self._process.stdin.writelines(msg)
        except BrokenPipeError as e:
            print(f"Mir ({self.name}) BrokenPipeError | Error while writing (sync).", e)
        except Exception as e:
            print(f'Mir ({self.name}) Exception | Error while writing (sync).', e)

    async def _send_payload(self, payload: dict) -> None:
        if not self._process or not self._process.stdin:
            return
        msg = create_message(payload)
        try:
            self._process.stdin.writelines(msg)
            await self._process.stdin.drain()
        except BrokenPipeError as e:
            print(f"Mir ({self.name}) BrokenPipeError | Error while writing.", e)
        except Exception as e:
            print(f'Mir ({self.name}) Exception | Error while writing:', e)

    def on_request(self, method: str, cb):
        self.on_request_handlers[method] = cb

    def on_notification(self, method: str, cb):
        self.on_notification_handlers.append({
            'cb': cb,
            'method': method
        })

    async def _response_handler(self, server_response: dict) -> None:
        response = self._response_handlers.pop(server_response["id"])
        response.request_end_time = datetime.datetime.now()
        if "result" in server_response and "error" not in server_response:
            self._communcation_logs.append(f'Recieved response "{response.method}" ({response.id}) - {response.duration}s\nResponse: {format_payload(server_response["result"])}')
            response.result.set_result(server_response["result"])
            if response.cache_key:
                self._cache_responses[response.cache_key] = server_response["result"]
        elif "result" not in server_response and "error" in server_response:
            self._communcation_logs.append(f'Recieved error response "{response.method}" ({response.id}) - {response.duration}s\nResponse:{format_payload(server_response["error"])}')
            response.result.set_exception(Error.from_lsp(server_response["error"]))
        else:
            self._communcation_logs.append(f'Recieved error response "{response.method}" ({response.id}) - {response.duration}s\nResponse:{format_payload(server_response["error"])}')
            response.result.set_exception(Error(ErrorCodes.InvalidRequest, ''))

    async def _request_handler(self, response: dict) -> None:
        method = response.get("method", "")
        params = response.get("params")
        request_id = response.get("id")
        handler = self.on_request_handlers.get(method)
        if not handler:
            await self.send_error_response(request_id, Error(
                    ErrorCodes.MethodNotFound, "method '{}' not handled on client.".format(method)))
            return
        try:
            self._communcation_logs.append(f'Received request "{method}" ({request_id})\nParams: {format_payload(params)}')
            res = await handler(params)
            self._communcation_logs.append(f'Sending response "{method}" ({request_id})\nResponse: {format_payload(res)}')
            await self.send_response(request_id, res)
        except Error as ex:
            await self.send_error_response(request_id, ex)
        except Exception as ex:
            await self.send_error_response(request_id, Error(ErrorCodes.InternalError, str(ex)))

    async def _notification_handler(self, response: dict) -> None:
        method = response.get("method", "")
        params = response.get("params")
        handlers = [ handler['cb'] for handler in self.on_notification_handlers if handler['method'] == method]
        self._communcation_logs.append(f'Received notification "{method}"\nParams: {format_payload(params)}')
        if not handlers:
            self._log(f"unhandled {method}")
            return
        try:
            for handler in handlers:
                handler(params)
        except asyncio.CancelledError:
            return
        except Exception as ex:
            if not self._received_shutdown:
                self.send_notification("window/logMessage", {"type": MessageType.Error, "message": str(ex)})
