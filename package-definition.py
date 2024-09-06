from __future__ import annotations
import sublime
from .libs.lsp.mir import mir
import sublime_plugin
from .libs.event_loop import run_future
from .libs.lsp.view_to_lsp import open_view_with_uri, range_to_region


class MirGotoDefinitionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        run_future(self.goto_definition())

    async def goto_definition(self):
        definitions = await mir.definitions(self.view)
        window = self.view.window()
        if not window:
            return
        for name, defintion in definitions:
            if isinstance(defintion, list):
                for d in defintion:
                    if 'targetUri' in d:
                        open_view_with_uri(d['targetUri'], d['targetSelectionRange'], window)
                    else:
                        open_view_with_uri(d['uri'], d['range'], window)
                    return
            if isinstance(defintion, dict):
                open_view_with_uri(defintion['uri'], defintion['range'], window)
                return


