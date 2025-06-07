from __future__ import annotations
import sublime
import sublime_aio
from Mir import mir, parse_uri, range_to_region
from Mir.types.lsp import DiagnosticSeverity, DiagnosticTag


class MirDiagnosticListener(sublime_aio.ViewEventListener):
    def __init__(self, view):
        super().__init__(view)
        self.cleanup = None

    def on_activated(self):
        if self.cleanup:
            return
        self.cleanup = mir.on_did_change_diagnostics(self.on_did_change_diagnostics)

    def on_load(self):
        if self.cleanup:
            return
        self.cleanup = mir.on_did_change_diagnostics(self.on_did_change_diagnostics)

    def on_did_change_diagnostics(self, uris: list[str]):
        sublime_aio.run_coroutine(self.draw_diagnotsics(uris))

    async def draw_diagnotsics(self, uris: list[str]):
        window = self.view.window()
        if not window:
            return

        for uri in uris:
            _, file_name = parse_uri(uri)
            view = next(iter([v for w in sublime.windows() for v in w.views() if v.file_name() == file_name]), None)
            if not view:
                continue
            results = await mir.get_diagnostics(view)
            errors = []
            deprecated = []
            unnecessary = []
            warnings = []
            infos = []
            hints = []
            for _, diagnostics in results:
                for diagnostic in diagnostics:
                    region = range_to_region(view, diagnostic['range'])
                    severity = diagnostic.get('severity', DiagnosticSeverity.Information)
                    tags = diagnostic.get('tags', [])
                    if DiagnosticTag.Unnecessary in tags:
                        unnecessary.append(region)
                    elif DiagnosticTag.Deprecated in tags:
                        deprecated.append(region)
                    elif severity == DiagnosticSeverity.Error:
                        errors.append(region)
                    elif severity == DiagnosticSeverity.Warning:
                        warnings.append(region)
                    elif severity == DiagnosticSeverity.Hint:
                        hints.append(region)
                    elif severity == DiagnosticSeverity.Information:
                        infos.append(region)
            view.erase_regions('mir-deprecated')
            view.add_regions('mir-deprecated', deprecated, 'markup.unnecessary', flags=sublime.DRAW_NO_OUTLINE | sublime.NO_UNDO)
            view.erase_regions('mir-unnecessary')
            view.add_regions('mir-unnecessary', unnecessary, 'markup.unnecessary', flags=sublime.DRAW_NO_OUTLINE | sublime.NO_UNDO)
            view.erase_regions('mir-hints')
            view.add_regions('mir-hints', hints, 'comment', flags=sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_OUTLINE | sublime.DRAW_NO_FILL | sublime.NO_UNDO)
            view.erase_regions('mir-infos')
            view.add_regions('mir-infos', infos, 'comment', flags=sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_OUTLINE | sublime.DRAW_NO_FILL | sublime.NO_UNDO)
            view.erase_regions('mir-warnings')
            view.add_regions('mir-warnings', warnings, 'region.yellowish', flags=sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_OUTLINE | sublime.DRAW_NO_FILL | sublime.NO_UNDO)
            view.erase_regions('mir-errors')
            view.add_regions('mir-errors', errors, 'region.redish', flags=sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_OUTLINE | sublime.DRAW_NO_FILL | sublime.NO_UNDO)

    def on_close(self):
        if self.cleanup:
            self.cleanup()
            self.cleanup = None
