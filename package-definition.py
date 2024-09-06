from __future__ import annotations
import sublime
import sublime_plugin
from .api import mir, run_future
from .api.helpers import open_view_with_uri


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


