from __future__ import annotations
import sublime_aio

from Mir.types.lsp import ExecuteCommandParams
from Mir import mir, server_for_view
from typing import Any

class mir_execute_command_command(sublime_aio.ViewCommand):
    async def run(self, server_name: str, command: str | None = None, arguments: list[Any] | None = None) -> None:
        if not command:
            return
        sublime_commands = mir.commands.to_sublime_commands(command)
        if sublime_commands: 
            for sublime_command in sublime_commands:
                self.view.run_command(sublime_command, {'arguments': arguments})
            # after handling the commands on the client side, don't send the command to the server
            return

        server = server_for_view(server_name, self.view)
        if server:
            params: ExecuteCommandParams = {"command": command}
            if arguments:
                params["arguments"] = arguments
            req = server.send.execute_command(params)
            _ = await req.result
