from __future__ import annotations
import sublime
import sublime_plugin
from .api import mir, run_future
from .api.types import Diagnostic
from .api.helpers import position_to_point
import operator


def find_diagnostic(view: sublime.View, diagnostics: list[Diagnostic], forward: bool) -> int:
    sorted_diagnostics: list[Diagnostic] = []
    sorted_diagnostics.extend(diagnostics)
    sorted_diagnostics.sort(key=lambda d: operator.itemgetter('line', 'character')(d['range']['start']), reverse=not forward)

    sel = view.sel()
    region = sel[0] if sel else None
    point = region.b if region is not None else 0

    op_func = operator.gt if forward else operator.lt
    for diagnostic in sorted_diagnostics:
        diag_pos = position_to_point(view, diagnostic['range']['start'])
        if op_func(diag_pos, point):
            break
    else:
        diag_pos = position_to_point(view, sorted_diagnostics[0]['range']['start'])
    return diag_pos


class MirNextDiagnosticCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        run_future(self.goto_next())

    async def goto_next(self):
        results = await mir.get_diagnostics(self.view)
        for _, diagnostics in results:
            diag_pos = find_diagnostic(self.view, diagnostics, forward=True)
            self.view.show_at_center(diag_pos)
            self.view.sel().clear()
            self.view.sel().add(diag_pos)
            break


class MirPrevDiagnosticCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        run_future(self.goto_prev())

    async def goto_prev(self):
        results = await mir.get_diagnostics(self.view)
        for _, diagnostics in results:
            diag_pos = find_diagnostic(self.view, diagnostics, forward=False)
            self.view.sel().clear()
            self.view.sel().add_all([diag_pos])
            self.view.show_at_center(diag_pos)
            break

