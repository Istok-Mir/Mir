from __future__ import annotations
from typing import TYPE_CHECKING, Any

from .capabilities import method_to_capability
from .types import RegistrationParams, UnregistrationParams, LogMessageParams, LogMessageParams, MessageType, ConfigurationParams

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

    async def register_capability(params: RegistrationParams):
        registrations = params["registrations"]
        for registration in registrations:
            capability_path = method_to_capability(registration["method"])
            options = registration.get("registerOptions")
            if not isinstance(options, dict):
                options = {}
            server.capabilities.register(capability_path, options)

    async def unregister_capability(params: UnregistrationParams):
        unregisterations = params["unregisterations"]
        for unregistration in unregisterations:
            capability_path = method_to_capability(unregistration["method"])
            server.capabilities.unregister(capability_path)

    def on_log_message(params: LogMessageParams):
        message_type = {
            MessageType.Error: 'Error',
            MessageType.Warning: 'Warning',
            MessageType.Info: 'Info',
            MessageType.Debug: 'Debug',
            MessageType.Log: 'Log',
        }.get(params.get('type', MessageType.Log))
        # print(f"Mir | {message_type}: {params.get('message')}")

    server.on_request('workspace/configuration', workspace_configuration)
    server.on_request('client/registerCapability', register_capability)
    server.on_request('client/unregisterCapability', unregister_capability)
    server.on_notification('window/logMessage', on_log_message)
