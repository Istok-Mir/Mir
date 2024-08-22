from __future__ import annotations
from lsp.capabilities import method_to_capability
from lsp.types import LogMessageParams, MessageType, RegistrationParams, UnregistrationParams
from typing import TYPE_CHECKING, Generic, TypeVar
if TYPE_CHECKING:
    from lsp.server import LanguageServer


NotificationPayload = TypeVar('NotificationPayload')
class OnNotificationPayload(Generic[NotificationPayload]):
    def __init__(self, server: LanguageServer, params: NotificationPayload) -> None:
        self.server =server
        self.params =params


RequestPayload = TypeVar('RequestPayload')
class OnRequestPayload(Generic[RequestPayload]):
    def __init__(self, server: LanguageServer, params: RequestPayload) -> None:
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
    print(f"Zenit | {message_type}: {payload.params.get('message')}")

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


async def unregister_capability(payload: OnRequestPayload[UnregistrationParams]):
    params = payload.params
    unregisterations = params["unregisterations"]
    for unregistration in unregisterations:
        capability_path = method_to_capability(unregistration["method"])
        payload.server.capabilities.unregister(capability_path)
