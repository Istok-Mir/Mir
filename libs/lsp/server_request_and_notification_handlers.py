from __future__ import annotations
from typing import TYPE_CHECKING

from .capabilities import method_to_capability
from .types import RegistrationParams, UnregistrationParams, LogMessageParams, LogMessageParams, MessageType

if TYPE_CHECKING:
	from .server import LanguageServer

def attach_server_request_and_notification_handlers(server: LanguageServer):
    async def workspace_configuration(payload):
        return [{
            "statusText": "{% set parts = [] %}{% if server_version %}{% do parts.append('v' + server_version) %}{% endif %}{% if venv %}{% do parts.append('venv: ' + venv.venv_prompt) %}{% do parts.append('py: ' + venv.python_version) %}{% do parts.append('by: ' + venv.finder_name) %}{% endif %}{{ parts|join('; ') }}",
            "venvStrategies": [
                "local_dot_venv",
                "env_var_conda_prefix",
                "env_var_virtual_env",
                "rye",
                "poetry",
                "pdm",
                "hatch",
                "pipenv",
                "pyenv",
                "any_subdirectory",
            ],
            "pyright.dev_environment": "",
            "python.analysis.autoImportCompletions": True,
            "python.analysis.autoSearchPaths": True,
            "python.analysis.extraPaths": [],
            "python.analysis.stubPath": "./typings",
            "python.analysis.diagnosticMode": "openFilesOnly",
            "python.analysis.diagnosticSeverityOverrides": {
            },
            "python.analysis.logLevel": "Information",
            "python.analysis.typeCheckingMode": "standard",
            "python.analysis.typeshedPaths": [],
            "python.analysis.useLibraryCodeForTypes": True,
            "pyright.disableLanguageServices": False,
            "pyright.disableOrganizeImports": False,
            "python.pythonPath": "",
            "python.venvPath": "",
        }]

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
