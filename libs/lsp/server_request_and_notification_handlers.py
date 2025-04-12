from __future__ import annotations
from typing import TYPE_CHECKING, Any, cast
from .capabilities import method_to_capability
from .view_to_lsp import get_view_uri, parse_uri
from .types import ApplyWorkspaceEditParams, ApplyWorkspaceEditResult, RegistrationParams, UnregistrationParams, LogMessageParams, LogMessageParams, MessageType, ConfigurationParams, PublishDiagnosticsParams, DidChangeWatchedFilesRegistrationOptions, CreateFilesParams, RenameFilesParams, DeleteFilesParams, DidChangeWatchedFilesParams, WorkspaceFolder
from .file_watcher import get_file_watcher, create_file_watcher
from .workspace_edit import apply_workspace_edit
if TYPE_CHECKING:
	from .server import LanguageServer

def attach_server_request_and_notification_handlers(server: LanguageServer):
    async def workspace_configuration(payload: ConfigurationParams):
        items: list[Any] = []
        requested_items = payload["items"]
        for requested_item in requested_items:
            configuration = server.settings.copy(requested_item.get('section') or None)
            items.append(configuration)
        return items

    def on_did_create_files(params: CreateFilesParams):
        if server.capabilities.has('workspace.fileOperations.didCreate'):
            server.notify.did_create_files(params)

    def on_did_rename_files(params: RenameFilesParams):
        if server.capabilities.has('workspace.fileOperations.didRename'):
            server.notify.did_rename_files(params)

    def on_did_delete_files(params: DeleteFilesParams):
        if server.capabilities.has('workspace.fileOperations.didDelete'):
            server.notify.did_delete_files(params)

    def on_did_change_watched_files(params: DidChangeWatchedFilesParams):
        server.notify.did_change_watched_files(params)

    register_provider_map = {}
    async def register_capability(params: RegistrationParams):
        from .lsp_providers import capabilities_to_lsp_providers
        from .providers import register_provider
        registrations = params["registrations"]
        for registration in registrations:
            capability_path = method_to_capability(registration["method"])
            options = registration.get("registerOptions")
            if not isinstance(options, dict):
                options = {}
            if capability_path == 'workspace.didChangeWatchedFiles':
                wacher_options = cast(DidChangeWatchedFilesRegistrationOptions, options)
                watchers = wacher_options['watchers']
                for folder in server.workspace_folders:
                    _, folder_name = parse_uri(folder['uri'])
                    glob_patterns = [watcher['globPattern'] for watcher in watchers if isinstance(watcher['globPattern'], str)]
                    watcher = get_file_watcher(folder_name)
                    if watcher is None:
                        watcher = create_file_watcher(folder_name)
                    watcher.register(server.name, {
                        'glob_patterns': glob_patterns,
                        'on_did_create_files': on_did_create_files,
                        'on_did_rename_files': on_did_rename_files,
                        'on_did_delete_files': on_did_delete_files,
                        'on_did_change_watched_files': on_did_change_watched_files,
                    })
            if capability_path in capabilities_to_lsp_providers:
                LspProvider = capabilities_to_lsp_providers[capability_path]
                provider = LspProvider(server)
                register_provider(provider)
                if not capability_path in register_provider_map:
                    register_provider_map[capability_path] = []
                register_provider_map[capability_path].append(provider)

            server.capabilities.register(capability_path, options)

    async def unregister_capability(params: UnregistrationParams):
        from .providers import unregister_provider
        unregisterations = params["unregisterations"]
        for unregistration in unregisterations:
            capability_path = method_to_capability(unregistration["method"])
            server.capabilities.unregister(capability_path)
            provider = register_provider_map.get(capability_path, []).pop()
            if provider:
                unregister_provider(provider)
            if capability_path == 'workspace.didChangeWatchedFiles':
                for folder in server.workspace_folders:
                    _, folder_name = parse_uri(folder['uri'])
                    watcher = get_file_watcher(folder_name)
                    # watcher.unregister(server.name) # pyright for some reason unregisters this capaability immediately afterm registering it


    def on_log_message(params: LogMessageParams):
        message_type = {
            MessageType.Error: 'Error',
            MessageType.Warning: 'Warning',
            MessageType.Info: 'Info',
            MessageType.Debug: 'Debug',
            MessageType.Log: 'Log',
        }.get(params.get('type', MessageType.Log))
        if message_type in ['Error', 'Warning']:
            print(f"Mir | {message_type}: {params.get('message')}")

    def publish_diagnostics(params: PublishDiagnosticsParams):
        from .mir import mir
        server.diagnostics.set(params['uri'], params['diagnostics'])
        mir._notify_did_change_diagnostics([params['uri']])

    async def diagnostic_refresh(params: None):
        for view in server.open_views:
            req = server.send.text_document_diagnostic({
                'textDocument': {
                    'uri': get_view_uri(view)
                }
            })

    async def workspace_folders(params: None) -> list[WorkspaceFolder] | None:
        return server.workspace_folders

    async def workspace_apply_edits(params: ApplyWorkspaceEditParams) -> ApplyWorkspaceEditResult:
        view = server.window.active_view()
        if not view:
            return {
                'applied': False,
                'failureReason': "I do not have a view available to trigger applying workspace edits"
            }

        await apply_workspace_edit(view, params['edit'])
        return {
            'applied': True # TODO improve, what can go wrong?
        }

    server.on_request('workspace/configuration', workspace_configuration)
    server.on_request('client/registerCapability', register_capability)
    server.on_request('client/unregisterCapability', unregister_capability)
    server.on_request('workspace/diagnostic/refresh', diagnostic_refresh)
    server.on_request('workspace/workspaceFolders', workspace_folders)
    server.on_request('workspace/applyEdit', workspace_apply_edits)
    server.on_notification('window/logMessage', on_log_message)
    server.on_notification('textDocument/publishDiagnostics', publish_diagnostics)



