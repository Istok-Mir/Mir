from __future__ import annotations
from typing import  Any, Dict, List, Optional, Union, cast
import asyncio
import json
import shutil

from event_loop import run_future
from lsp.communcation_logs import CommmunicationLogs, format_payload
from lsp.handle_server_requests_and_notifications import OnNotificationPayload, OnRequestPayload, on_log_message, register_capability, unregister_capability,workspace_configuration
from sublime_plugin import sublime
import datetime

from .types import ErrorCodes, MessageType
from .lsp_requests import LspRequest, LspNotification
from .capabilities import CLIENT_CAPABILITIES, ServerCapabilities


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
    def __init__(self, id, method='') -> None:
        self.id: int = id
        self.method = method
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


class LanguageServer:
    def __init__(self, name: str, cmd: str) -> None:
        self.name = name
        self.send = LspRequest(self.send_request)
        self.notify = LspNotification(self.send_notification)
        self.capabilities = ServerCapabilities()

        self._cmd = cmd
        self._process = None
        self._received_shutdown = False

        self.request_id = 1
        # equests sent from client
        self._response_handlers: Dict[Any, Request] = {}
        self._cancel_requests: list[Request] = []
        # requests and notifications sent from server
        self.on_request_handlers = {}
        self.on_notification_handlers = {}
        # logs
        self._communcation_logs = CommmunicationLogs(name)

        # respond to server requests and notifications
        self.on_request('workspace/configuration', workspace_configuration)
        self.on_request('client/registerCapability', register_capability)
        self.on_request('client/unregisterCapability', unregister_capability)
        self.on_notification('window/logMessage', on_log_message)

    async def start(self):
        try:
            if not shutil.which(self._cmd.split()[0]):
                raise RuntimeError(f"Command not found: {self._cmd}")

            self._process = await asyncio.create_subprocess_shell(
                self._cmd,
                stdout=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            run_future(self._run_forever())

            folders = sublime.active_window().folders()
            root_folder = folders[0] if folders else ''
            initialize_result = await self.send.initialize({
                'processId': self._process.pid,
                'rootUri': 'file://' + root_folder,
                'rootPath': root_folder,
                'workspaceFolders': [{'name': 'OLSP', 'uri': 'file://' + root_folder}],
                'capabilities': CLIENT_CAPABILITIES,
                'initializationOptions': {'completionDisableFilterText': True, 'disableAutomaticTypingAcquisition': False, 'locale': 'en', 'maxTsServerMemory': 0, 'npmLocation': '', 'plugins': [], 'preferences': {'allowIncompleteCompletions': True, 'allowRenameOfImportPath': True, 'allowTextChangesInNewFiles': True, 'autoImportFileExcludePatterns': [], 'disableSuggestions': False, 'displayPartsForJSDoc': True, 'excludeLibrarySymbolsInNavTo': True, 'generateReturnInDocTemplate': True, 'importModuleSpecifierEnding': 'auto', 'importModuleSpecifierPreference': 'shortest', 'includeAutomaticOptionalChainCompletions': True, 'includeCompletionsForImportStatements': True, 'includeCompletionsForModuleExports': True, 'includeCompletionsWithClassMemberSnippets': True, 'includeCompletionsWithInsertText': True, 'includeCompletionsWithObjectLiteralMethodSnippets': True, 'includeCompletionsWithSnippetText': True, 'includePackageJsonAutoImports': 'auto', 'interactiveInlayHints': True, 'jsxAttributeCompletionStyle': 'auto', 'lazyConfiguredProjectsFromExternalProject': False, 'organizeImportsAccentCollation': True, 'organizeImportsCaseFirst': False, 'organizeImportsCollation': 'ordinal', 'organizeImportsCollationLocale': 'en', 'organizeImportsIgnoreCase': 'auto', 'organizeImportsNumericCollation': False, 'providePrefixAndSuffixTextForRename': True, 'provideRefactorNotApplicableReason': True, 'quotePreference': 'auto', 'useLabelDetailsInCompletionEntries': True}, 'tsserver': {'fallbackPath': '', 'logDirectory': '', 'logVerbosity': 'off', 'path': '', 'trace': 'off', 'useSyntaxServer': 'auto'}}
            })
            self.capabilities.assign(cast(dict, initialize_result['capabilities']))
            self.notify.initialized({})
        except Exception as e:
            print(f'Zenit ({self.name}) Error while creating subprocess.', e)

    def stop(self):
        run_future(self.shutdown())
        if self._process:
            self._process.kill()

    async def shutdown(self):
        await self.send.shutdown()
        self._received_shutdown = True
        self.notify.exit()
        if self._process and self._process.stdout:
            self._process.stdout.set_exception(StopLoopException())

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
            print(f'Zenit ({self.name}) Error in run_forever. ', e)
            pass
        return self._received_shutdown

    async def _handle_body(self, body: bytes) -> None:
        try:
            await self._receive_payload(json.loads(body))
        except IOError as ex:
            self._log(f"Zenit ({self.name})  malformed {ENCODING}: {ex}")
        except UnicodeDecodeError as ex:
            self._log(f"Zenit ({self.name})  malformed {ENCODING}: {ex}")
        except json.JSONDecodeError as ex:
            self._log(f"Zenit ({self.name})  malformed JSON: {ex}")
        except Exception as e:
            print(f"Zenit ({self.name}) Error in _handle_body. ", e)

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
        self._communcation_logs.append(f'Send notification "{method}"\nParams: {format_payload(params)}')
        self._send_payload_sync(
            make_notification(method, params))

    async def send_response(self, request_id: Any, params: PayloadLike) -> None:
        await self._send_payload(
            make_response(request_id, params))

    async def send_error_response(self, request_id: Any, err: Error) -> None:
        self._communcation_logs.append(f'Send error response ({request_id})\n{err}')
        try:
            await self._send_payload(
                make_error_response(request_id, err))
        except Exception as e:
            print(f'Zenit ({self.name}) Error in send_error_response.', e)

    async def send_request(self, method: str, params: Optional[dict] = None):
        for i, cancel_request in enumerate(list(self._cancel_requests)):
            if cancel_request.method == method:
                self.notify.cancel_request({ 'id': cancel_request.id })
                self._cancel_requests.pop(i)
        request_id = self.request_id
        request = Request(request_id, method)
        self.request_id += 1
        self._response_handlers[request_id] = request
        self._cancel_requests.append(request)
        start_of_req = datetime.datetime.now()
        async with request.cv:
            self._communcation_logs.append(f'Sending request "{method}" ({request_id})\nParams: {format_payload(params)}')
            await self._send_payload(make_request(method, request_id, params))
            await request.cv.wait()
        end_of_req = datetime.datetime.now()
        duration = round((end_of_req-start_of_req).total_seconds(), 2)
        if isinstance(request.error, Error):
            self._communcation_logs.append(f'Recieved error response "{method}" ({request_id}) - {duration}s\n{format_payload(request.error)}')
            raise request.error
        self._communcation_logs.append(f'Recieved response "{method}" ({request_id}) - {duration}s\n{format_payload(request.result)}')
        return request.result

    def _send_payload_sync(self, payload: StringDict) -> None:
        if not self._process or not self._process.stdin:
            return
        msg = create_message(payload)
        try:
            self._process.stdin.writelines(msg)
        except BrokenPipeError as e:
            print(f"Zenit ({self.name}) BrokenPipeError | Error while writing (sync).", e)
        except Exception as e:
            print(f'Zenit ({self.name}) Exception | Error while writing (sync).', e)

    async def _send_payload(self, payload: StringDict) -> None:
        if not self._process or not self._process.stdin:
            return
        msg = create_message(payload)
        try:
            self._process.stdin.writelines(msg)
            await self._process.stdin.drain()
        except BrokenPipeError as e:
            print(f"Zenit ({self.name}) BrokenPipeError | Error while writing.", e)
        except Exception as e:
            print(f'Zenit ({self.name}) Exception | Error while writing:', e)

    def on_request(self, method: str, cb):
        self.on_request_handlers[method] = cb

    def on_notification(self, method: str, cb):
        self.on_notification_handlers[method] = cb

    async def _response_handler(self, response: StringDict) -> None:
        request = self._response_handlers.pop(response["id"])
        self._cancel_requests = [r for r in self._cancel_requests if r.id != response["id"]]
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
            await self.send_error_response(request_id, Error(
                    ErrorCodes.MethodNotFound, "method '{}' not handled on client.".format(method)))
            return
        try:
            self._communcation_logs.append(f'Received request "{method}" ({request_id})\nParams: {format_payload(params)}')
            res = await handler(OnRequestPayload(self, params))
            self._communcation_logs.append(f'Sending response "{method}" ({request_id})\n{format_payload(res)}')
            await self.send_response(request_id, res)
        except Error as ex:
            await self.send_error_response(request_id, ex)
        except Exception as ex:
            await self.send_error_response(request_id, Error(ErrorCodes.InternalError, str(ex)))

    async def _notification_handler(self, response: StringDict) -> None:
        method = response.get("method", "")
        params = response.get("params")
        handler = self.on_notification_handlers.get(method)
        self._communcation_logs.append(f'Received notification "{method}"\nParams: {format_payload(params)}')
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
