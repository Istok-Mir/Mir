from __future__ import annotations
import sublime
from Mir import mir, parse_uri, position_to_point, open_view, open_view_with_uri
import sublime_aio


class mir_goto_definition_command(sublime_aio.ViewCommand):
    async def run(self):
        sel = self.view.sel()
        if sel is None:
            return
        point = sel[0].b
        definitions = await mir.definitions(self.view, point)
        window = self.view.window()
        if not window:
            return
        for name, definition in definitions:
            if isinstance(definition, list):
                for d in definition:
                    if 'targetUri' in d:
                        await open_view_with_uri(d['targetUri'], d['targetSelectionRange'], self.view)
                    else:
                        await open_view_with_uri(d['uri'], d['range'], self.view)
                    return
            if isinstance(definition, dict):
                await open_view_with_uri(definition['uri'], definition['range'], self.view)
                return
