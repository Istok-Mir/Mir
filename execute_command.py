from __future__ import annotations
from .libs.event_loop import run_future
from .libs.lsp.server import LanguageServer
from .libs.lsp.manage_servers import server_for_view
from .libs.lsp.types import ExecuteCommandParams
from typing import Any
import sublime
import sublime_plugin


class MirExecuteCommandCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, server_name: str, command: str | None = None, arguments: list[Any] | None = None) -> None:
        print('run ...', server_name, command, arguments)
        server = server_for_view(server_name, self.view)
        if server and command:
            params: ExecuteCommandParams = {"command": command}
            if arguments:
                params["arguments"] = arguments
            run_future(self.execute_command(server, params))

    async def execute_command(self, server: LanguageServer, params: ExecuteCommandParams):
        req = server.send.execute_command(params)
        result = await req.result
        print('execute_command result', result)
