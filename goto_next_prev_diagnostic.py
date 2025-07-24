from __future__ import annotations
import html

from .libs.hover_template import hover_template
from .hover import strip_html_tags
import sublime
import sublime_aio
import sublime_plugin
from Mir import mir, position_to_point, minihtml, MinihtmlKind
from Mir.types.lsp import Diagnostic, DiagnosticSeverity
import operator


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


class mir_next_diagnostic_command(sublime_aio.ViewCommand):
    async def run(self):
        results = await mir.get_diagnostics(self.view)
        all_diagnostics = []
        for _, diagnostics in results:
            all_diagnostics.extend(diagnostics)
        diag_pos, diagnostic = find_diagnostic(self.view, all_diagnostics, forward=True)
        self.view.run_command('mir_go_to_point', {'point': diag_pos, 'diagnostic': diagnostic if diagnostic else None})

class mir_prev_diagnostic_command(sublime_aio.ViewCommand):
    async def run(self):
        results = await mir.get_diagnostics(self.view)
        all_diagnostics = []
        for _, diagnostics in results:
            all_diagnostics.extend(diagnostics)
        diag_pos, diagnostic = find_diagnostic(self.view, all_diagnostics, forward=False)
        self.view.run_command('mir_go_to_point', {'point': diag_pos, 'diagnostic': diagnostic if diagnostic else None})


class MirGoToPointCommand(sublime_plugin.TextCommand):
    def run(self, edit, point, diagnostic: Diagnostic | None=None):
        window = self.view.window()
        if not window:
            return
        window.focus_view(self.view)
        self.view.sel().clear()
        self.view.sel().add(point)
        self.view.show(point)
        if not diagnostic:
            return

        def format(d: Diagnostic):
            message_styles: str = 'opacity: 0.4; color: var(--grayish)'
            source_styles: str = 'opacity: 0.4; color: var(--grayish)'
            if d.get('severity') == DiagnosticSeverity.Error:
                message_styles = 'color: var(--redish)'
                source_styles = 'opacity: 0.4; padding: 0 0.3rem; border-radius: 4px; color: var(--redish); background-color: color(var(--redish) alpha(0.1));'
            elif d.get('severity') == DiagnosticSeverity.Warning:
                message_styles = 'color:var(--yellowish)'
                source_styles = 'opacity: 0.4; padding: 0 0.3rem; border-radius: 4px; color: var(--yellowish); background-color: color(var(--yellowish) alpha(0.1))'
            else:
                source_styles = 'opacity: 0.4; padding: 0 0.3rem; border-radius: 4px; color: var(--foreground); background-color: color(var(--foreground) alpha(0.1))'
            source = d.get('source', '')
            formatted_source = ''
            if source:
                formatted_source = f"<span style='{source_styles}'>{source}</span>"
            return f"<div style='{message_styles}'>{d['message']} {formatted_source}</div>"

        content = minihtml(self.view, format(diagnostic), MinihtmlKind.FORMAT_MARKED_STRING | MinihtmlKind.FORMAT_MARKUP_CONTENT)

        content = f"""
         <a title="Click to copy" style='text-decoration: none; display: block; color: var(--foreground)' href='{sublime.command_url('mir_copy_text', {
            'text': html.unescape(strip_html_tags(content))
        })}'>
             {content}
         </a>
        """
        sublime.set_timeout(lambda: self.view.show_popup(
            hover_template(content),
            sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
            point,
            max_width=800,
        ), 100)
