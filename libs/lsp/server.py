from __future__ import annotations
import os
import re

from Mir import mir_logger
from .pull_diagnostics import pull_diagnostics

from .server_request_and_notification_handlers import attach_server_request_and_notification_handlers
from .capabilities import CLIENT_CAPABILITIES, ServerCapabilities
from .lsp_requests import LspRequest, LspNotification, Request
from Mir.types.lsp import DidChangeTextDocumentParams, ErrorCodes, InitializeParams, LSPAny, MessageType, WorkspaceFolder
from .console import Console, format_payload
from .view_to_lsp import file_name_to_uri, get_view_uri
from pathlib import Path
from sublime_plugin import sublime
from typing import Any, Callable, Dict, Literal, Optional, TypedDict, cast
from typing_extensions import NotRequired
from wcmatch.glob import BRACE
from .dotted_dict import DottedDict
from wcmatch.glob import globmatch
from wcmatch.glob import GLOBSTAR
import asyncio
import sublime_aio
import datetime
import orjson
from .diagnostic_collection import DiagnosticCollection
import importlib
import functools
import sublime_aio
import asyncio


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
    body = orjson.dumps(payload)
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
    if not hasattr(server, 'name'):
        raise Exception(f'Specify a `name` static property for {server.__name__}.')
    if not hasattr(server, 'activation_events'):
        raise Exception(f'Specify a `activation_events` static property` for {server.name}.')
    if server.name in [s.name for s in ManageServers.language_servers_plugins]:
        mir_logger.info(f'{server.name} is skipped because it was already registered.')
        return
    ManageServers.language_servers_plugins.append(server)


def unregister_language_server(server: LanguageServer):
    from .manage_servers import ManageServers
    [s.stop() for servers in ManageServers.language_servers_per_window.values() for s in servers if s.name == server.name]
    ManageServers.language_servers_plugins = [s for s in ManageServers.language_servers_plugins if s.name != server.name]


server_callbacks_when_ready = []

class LanguageServerConnectionOptions(TypedDict):
    cmd: list[str]
    env: NotRequired[dict]
    initialization_options: NotRequired[dict]

class LanguageServer:
    name: str
    activation_events: ActivationEvents
    settings_file: NotRequired[str]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        global server_callbacks_when_ready

        def is_api_ready():
            from sublime_plugin import api_ready
            return api_ready

        api_ready = is_api_ready()
        def run():
            register_language_server(cls)

            def schedule():
                m = importlib.import_module(cls.__module__)
                original_plugin_unloaded = m.__dict__.get('plugin_unloaded')

                def override_plugin_unloaded():
                    if original_plugin_unloaded:
                        original_plugin_unloaded()
                    unregister_language_server(cls)

                m.__dict__['plugin_unloaded'] = override_plugin_unloaded

            sublime.set_timeout(schedule, 1)
        if not api_ready:
            server_callbacks_when_ready.append(run)
        else:
            run()

    async def activate(self):
        ...


    async def connect(self, transport: Literal['stdio', 'tcp'], options: LanguageServerConnectionOptions):
        if "initialization_options" in options:
            self.initialization_options.update(options['initialization_options'])
        env = os.environ.copy()
        if 'env' in options:
            env.update(options['env'])

        if transport == 'stdio':
            try:
                self.status = 'initializing'
                self._process = await asyncio.create_subprocess_exec(
                    *options['cmd'],
                    stdout=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )

                await asyncio.sleep(0.2)
                if self._process.returncode and self._process.stderr:
                    error_message = (await self._process.stderr.read()).decode('utf-8', errors='ignore')
                    error_message_wihout_ascii_chars = re.sub(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]',' ', error_message)
                    final_message = f"Command: '{' '.join([str(o) for o in options['cmd']])}'" + '\nExited with: ' + error_message_wihout_ascii_chars
                    self.console.log(final_message)
                    raise Exception(final_message)

                sublime_aio.run_coroutine(self._run_forever())
            except Exception as e:
                mir_logger.error(f'Mir ({self.name}) Error while creating subprocess.', exc_info=e)
                self.status = 'off'
                raise e
        else: 
            raise Exception('Mir: Only transport stdio is supported at the moment.')

    def __init__(self) -> None:
        self.status: Literal['off', 'initializing','ready'] = 'off'

        self.send = LspRequest(self.send_request)
        self.notify = LspNotification(self.send_notification)
        self.capabilities = ServerCapabilities()

        self.view: sublime.View = sublime.View(-1)
        self.open_views: list[sublime.View] = []
        self.window: sublime.Window = sublime.Window(-1)

        default_setting = sublime.load_settings(self.settings_file).to_dict() if hasattr(self, 'settings_file') else None
        self.settings = DottedDict(default_setting)

        self.initialization_options = DottedDict()

        self.diagnostics = DiagnosticCollection()

        self._process = None
        self._received_shutdown = False

        self.initialize_params: InitializeParams = {
            'processId': None,
            'workspaceFolders': [],
            'rootUri': None,
            'rootPath': None,
            'capabilities': CLIENT_CAPABILITIES,
            'initializationOptions': {}
        }

        self.pending_changes: dict[int, DidChangeTextDocumentParams] = {}

        self.request_id = 1
        # requests sent from client
        self._response_handlers: Dict[Any, Request] = {}
        # requests and notifications sent from server
        self.on_request_handlers = {}
        self.on_notification_handlers: list[NotificationHandler] = []
        # logs
        self.console: Console = Console(self.name)
        self.before_shutdown: list[Callable[[],None]] = []

        self.diagnostics_previous_result_id: str | None = None
        attach_server_request_and_notification_handlers(self)

    async def start(self, view: sublime.View):
        self.view = view
        self.settings.update(view.settings().get('mir.language_server_settings', {}))
        window = view.window()
        if not window:
            raise Exception('A window must exists now')
        self.window = window
        self.console = Console(self.name, window)

        folders = window.folders() if window else []
        first_folder = folders[0] if folders else ''
        workspace_folders: list[WorkspaceFolder] = [{'name': Path(f).name, 'uri':file_name_to_uri(f)} for f in folders]
        first_folder_uri = workspace_folders[0]['uri'] if workspace_folders else None

        self.initialize_params = {
            'processId': None,
            'workspaceFolders': workspace_folders,
            'rootUri': first_folder_uri,  # @deprecated in favour of `workspaceFolders`
            'rootPath': first_folder,  # @deprecated in favour of `rootUri`.
            'capabilities': CLIENT_CAPABILITIES,
            'initializationOptions': self.initialization_options.get()
        }
        await self.activate() # lots of stuff can fail here

        assert self._process, f"Mir: {self.name} should be running after activation, but it is not."
        self.initialize_params['processId'] = self._process.pid # process
        initialize_result = await self.send.initialize(self.initialize_params).result
        self.capabilities.assign(cast(dict, initialize_result['capabilities']))

        self.register_providers()
        self.status = 'ready'

        self.notify.initialized({})

        def update_settings_on_change():
            self.settings.update(view.settings().get('mir.language_server_settings', {}))
            self.notify.workspace_did_change_configuration({'settings': {}}) # https://github.com/microsoft/language-server-protocol/issues/567#issuecomment-420589320

        self.view.settings().add_on_change('mir-settings-listener', update_settings_on_change)
        self.notify.workspace_did_change_configuration({'settings': {}}) # https://github.com/microsoft/language-server-protocol/issues/567#issuecomment-420589320


    def stop(self):
        self.view.settings().clear_on_change('mir-settings-listener')
        sublime_aio.run_coroutine(self.shutdown())

    def register_providers(self):
        from .providers import register_provider, unregister_provider
        from .lsp_providers import capabilities_to_lsp_providers
        for capability, LspProvider in capabilities_to_lsp_providers.items():
            if self.capabilities.has(capability):
                provider = LspProvider(self)
                def dispose(provider):
                    unregister_provider(provider)
                bound_fn = functools.partial(dispose, provider)
                self.before_shutdown.append(bound_fn)
                register_provider(provider)

    async def shutdown(self):
        for cb in self.before_shutdown:
            cb()
        self.cancel_all_requests('Cancelling requests due to shutting down.')
        await self.send.shutdown().result
        self._received_shutdown = True
        self.notify.exit()
        if self._process and self._process.stdout:
            self._process.stdout.set_exception(StopLoopException())
        if self._process:
            self._process.kill()
            await self._process.wait()
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
                await self._handle_body(body, num_bytes)
            self.cancel_all_requests('The process exited so stopping all requests.')
        except (BrokenPipeError, ConnectionResetError) as e:
            mir_logger.error(f'Mir ({self.name}). BrokenPipeError, ConnectionResetError', exc_info=e)
            pass
        except StopLoopException as e:
            mir_logger.error(f'Mir: ({self.name}) stopped.', exc_info=e)
            pass
        return self._received_shutdown

    async def _handle_body(self, body: bytes, num_bytes: int) -> None:
        try:
            await self._receive_payload(orjson.loads(body))
        except IOError as ex:
            self._log(f"Mir ({self.name})  malformed {ENCODING}: {ex}")
        except UnicodeDecodeError as ex:
            self._log(f"Mir ({self.name})  malformed {ENCODING}: {ex}")
        except orjson.JSONDecodeError as ex:
            self._log(f"Mir ({self.name})  malformed JSON: {ex}")
        except Exception as e:
            mir_logger.error(f"Mir ({self.name}) Error in _handle_body. ", exc_info=e)

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

    def send_notification(self, method: str, params: Optional[dict|list] = None):
        self.console.log(f'Send notification "{method}"\nParams: {format_payload(params)}')
        self._send_payload_sync(
            make_notification(method, params))

    async def send_response(self, request_id: Any, params: Any) -> None:
        await self._send_payload(
            make_response(request_id, params))

    async def send_error_response(self, request_id: Any, err: Error) -> None:
        self.console.log(f'Send error response ({request_id})\n{err}')
        try:
            await self._send_payload(
                make_error_response(request_id, err))
        except Exception as e:
            mir_logger.error(f'Mir ({self.name}) Error in send_error_response.', exc_info=e)

    def send_request(self, method: str, params: Optional[dict] = None):
        self.send_did_change_text_document()
        request_id = self.request_id
        self.request_id += 1
        response = Request(self, request_id, method, params)
        self._response_handlers[request_id] = response
        self.console.log(f'Sending request "{method}" ({request_id})\nParams: {format_payload(params)}')
        sublime_aio.run_coroutine(self._send_payload(make_request(method, request_id, params)))
        return response

    def cancel_all_requests(self, message: str):
        for request_id in self._response_handlers:
            response = self._response_handlers[request_id]
            response.result.set_exception(Exception(message))

    def _send_payload_sync(self, payload: dict) -> None:
        if not self._process or not self._process.stdin:
            return
        msg = create_message(payload)
        try:
            self._process.stdin.writelines(msg)
        except BrokenPipeError as e:
            mir_logger.error(f"Mir ({self.name}) BrokenPipeError | Error while writing (sync).", exc_info=e)
        except Exception as e:
            mir_logger.error(f'Mir ({self.name}) Exception | Error while writing (sync).', exc_info=e)

    async def _send_payload(self, payload: dict) -> None:
        if not self._process or not self._process.stdin:
            return
        msg = create_message(payload)
        try:
            self._process.stdin.writelines(msg)
            await self._process.stdin.drain()
        except BrokenPipeError as e:
            mir_logger.error(f"Mir ({self.name}) BrokenPipeError | Error while writing.", exc_info=e)
        except Exception as e:
            mir_logger.error(f'Mir ({self.name}) Exception | Error while writing:', exc_info=e)

    def on_request(self, method: str, cb):
        self.on_request_handlers[method] = cb

    def on_notification(self, method: str, cb):
        self.on_notification_handlers.append({
            'cb': cb,
            'method': method
        })

    async def _response_handler(self, server_response: dict) -> None:
        request = self._response_handlers.pop(server_response["id"])
        request.request_end_time = datetime.datetime.now()
        if "__ignore" in server_response:
            self.console.log(f'Received response "{request.method}" ({request.id}) - {request.duration}s\nResponse is overridden to be "{format_payload(server_response["result"])}" because the original response is too large ({server_response["num_bytes"]})')
            request.result.set_result(server_response["result"])
        elif "result" in server_response and "error" not in server_response:
            self.console.log(f'Received response "{request.method}" ({request.id}) - {request.duration}s\nResponse: {format_payload(server_response["result"])}')
            request.result.set_result(server_response["result"])
        elif "result" not in server_response and "error" in server_response:
            self.console.log(f'Received error response "{request.method}" ({request.id}) - {request.duration}s\nResponse:{format_payload(server_response["error"])}')
            request.result.set_exception(Error.from_lsp(server_response["error"]))
        else:
            self.console.log(f'Received error response "{request.method}" ({request.id}) - {request.duration}s\nResponse:{format_payload(server_response["error"])}')
            request.result.set_exception(Error(ErrorCodes.InvalidRequest, ''))

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
            self.console.log(f'Received request "{method}" ({request_id})\nParams: {format_payload(params)}')
            res = await handler(params)
            self.console.log(f'Sending response "{method}" ({request_id})\nResponse: {format_payload(res)}')
            await self.send_response(request_id, res)
        except Error as ex:
            await self.send_error_response(request_id, ex)
        except Exception as ex:
            await self.send_error_response(request_id, Error(ErrorCodes.InternalError, str(ex)))

    async def _notification_handler(self, response: dict) -> None:
        method = response.get("method", "")
        params = response.get("params")
        handlers = [ handler['cb'] for handler in self.on_notification_handlers if handler['method'] == method]
        self.console.log(f'Received notification "{method}"\nParams: {format_payload(params)}')
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

    def send_did_change_text_document(self):
        pending_changes = list(self.pending_changes.items())
        self.pending_changes = {}
        for _, did_change_text_document_params in pending_changes:
            self.notify.did_change_text_document(did_change_text_document_params)
            sublime_aio.run_coroutine(pull_diagnostics(self, did_change_text_document_params['textDocument']['uri']))

def strip_ansi_codes(text):
    """
    Removes ANSI escape codes from a string.
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)
