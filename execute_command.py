from __future__ import annotations
from .libs.event_loop import run_future
from .libs.lsp.server import LanguageServer
from .libs.lsp.manage_servers import server_for_view
from .libs.lsp.types import ExecuteCommandParams
from typing import Any
from .api import mir
import sublime
import sublime_plugin

class MirExecuteCommandCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, server_name: str, command: str | None = None, arguments: list[Any] | None = None) -> None:
        if not command:
            return
        sublime_commands = mir.commands.get_sublime_commands(command)
        if sublime_commands: 
            for sublime_command in sublime_commands:
                self.view.run_command(sublime_command, {'arguments': arguments})
            # after handling the commands on the client side, don't send commands to the server
            return

        server = server_for_view(server_name, self.view)
        if server:
            params: ExecuteCommandParams = {"command": command}
            if arguments:
                params["arguments"] = arguments
            run_future(self.execute_server_command(server, params))

    async def execute_server_command(self, server: LanguageServer, params: ExecuteCommandParams):
        req = server.send.execute_command(params)
        result = await req.result
