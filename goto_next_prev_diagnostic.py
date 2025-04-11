from __future__ import annotations
import sublime
import sublime_plugin
from .api import mir
import sublime_aio
from .api.types import Diagnostic
from .api.helpers import position_to_point
import operator
from .api.helpers import minihtml, MinihtmlKind


def find_diagnostic(view: sublime.View, diagnostics: list[Diagnostic], forward: bool) -> tuple[int, Diagnostic|None]:
    sorted_diagnostics: list[Diagnostic] = []
    sorted_diagnostics.extend(diagnostics)
    sorted_diagnostics.sort(key=lambda d: operator.itemgetter('line', 'character')(d['range']['start']), reverse=not forward)

    sel = view.sel()
    region = sel[0] if sel else None
    point = region.b if region is not None else 0
    if not sorted_diagnostics:
        return (point, None)

    op_func = operator.gt if forward else operator.lt
    diag = None
    for diagnostic in sorted_diagnostics:
        diag_pos = position_to_point(view, diagnostic['range']['start'])
        diag = diagnostic
        if op_func(diag_pos, point):
            break
    else:
        diag_pos = position_to_point(view, sorted_diagnostics[0]['range']['start'])
        diag = sorted_diagnostics[0]
    return (diag_pos, diag)


class MirNextDiagnosticCommand(sublime_aio.ViewCommand):
    async def run(self):
        results = await mir.get_diagnostics(self.view)
        all_diagnostics = []
        for _, diagnostics in results:
            all_diagnostics.extend(diagnostics)
        diag_pos, diagnostic = find_diagnostic(self.view, all_diagnostics, forward=True)
        self.view.run_command('mir_go_to_point', {'point': diag_pos, 'message': diagnostic['message'] if diagnostic else None})

class MirPrevDiagnosticCommand(sublime_aio.ViewCommand):
    async def run(self):
        results = await mir.get_diagnostics(self.view)
        all_diagnostics = []
        for _, diagnostics in results:
            all_diagnostics.extend(diagnostics)
        diag_pos, diagnostic = find_diagnostic(self.view, all_diagnostics, forward=False)
        self.view.run_command('mir_go_to_point', {'point': diag_pos, 'message': diagnostic['message'] if diagnostic else None})


class MirGoToPointCommand(sublime_plugin.TextCommand):
    def run(self, edit, point, message: str | None=None):
        window = self.view.window()
        if not window:
            return
        window.focus_view(self.view)
        self.view.sel().clear()
        self.view.sel().add(point)
        self.view.show(point)
        if not message:
            return
        content = minihtml(self.view, message, MinihtmlKind.FORMAT_MARKED_STRING | MinihtmlKind.FORMAT_MARKUP_CONTENT)
        sublime.set_timeout(lambda: self.view.show_popup(
            f"""<html style='box-sizing:border-box; background-color:var(--background); padding:0rem; margin:0'><body style='padding:0.3rem; margin:0; border-radius:4px; padding: 0.5rem;border: 1px solid color(var(--foreground) blend(var(--background) 20%));'><div style='padding: 0.0rem 0.2rem; font-size: 0.9rem;'>{content}</div></body></html>""",
            sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
            point,
            max_width=800,
        ), 100)
