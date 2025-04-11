from __future__ import annotations
from .libs.lsp.view_to_lsp import parse_uri, position_to_point
import sublime
from .api import mir
import sublime_aio
from .open_view import open_view


class MirGotoDefinitionCommand(sublime_aio.ViewCommand):
    async def run(self):
        sel = self.view.sel()
        if sel is None:
            return
        point = sel[0].b
        definitions = await mir.definitions(self.view, point)
        window = self.view.window()
        if not window:
            return
        for name, defintion in definitions:
            if isinstance(defintion, list):
                for d in defintion:
                    if 'targetUri' in d:
                        # open_view_with_uri(d['targetUri'], d['targetSelectionRange'], window)
                        _, file_name = parse_uri(d['targetUri'])
                        view = await open_view(file_name, window, flags=sublime.ENCODED_POSITION | sublime.SEMI_TRANSIENT)
                        point = position_to_point(view, d['targetSelectionRange']['end'])
                        window.focus_view(view)
                        move_cursor_to(view, point)
                    else:
                        # open_view_with_uri(d['uri'], d['range'], window)
                        _, file_name = parse_uri(d['uri'])
                        view = await open_view(file_name, window, flags=sublime.NewFileFlags.ENCODED_POSITION | sublime.SEMI_TRANSIENT)
                        point = position_to_point(view, d['range']['end'])
                        window.focus_view(view)
                        move_cursor_to(view, point)
                    return
            if isinstance(defintion, dict):
                # open_view_with_uri(defintion['uri'], defintion['range'], window)
                _, file_name = parse_uri(defintion['uri'])
                view = window.find_open_file(file_name)
                if view:
                    selected_sheets = window.selected_sheets()
                    if view.sheet() in selected_sheets:
                        window.select_sheets([view.sheet()])
                else:
                    view = await open_view(file_name, window, flags=sublime.NewFileFlags.ENCODED_POSITION | sublime.ADD_TO_SELECTION | sublime.SEMI_TRANSIENT)
                point = position_to_point(view, defintion['range']['end'])
                window.focus_view(view)
                move_cursor_to(view, point)
                return


def move_cursor_to(view: sublime.View, point: int) -> None:
    sel = view.sel()
    sel.clear()
    sel.add(point)
    view.run_command("add_jump_record", {"selection": [(point, point)]})
    if not view.visible_region().contains(point):
        view.show_at_center(point)

