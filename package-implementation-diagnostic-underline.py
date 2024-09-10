from __future__ import annotations
import sublime
import sublime_plugin
from .api import mir, run_future
from .api.types import DiagnosticSeverity
from .api.helpers import open_view_with_uri, minihtml, MinihtmlKind, parse_uri, range_to_region


class MirHoverListener(sublime_plugin.ViewEventListener):
    def __init__(self, view):
        super().__init__(view)
        self.cleanup = None

    def on_activated(self):
        if self.cleanup:
            return
        self.cleanup = mir.on_did_change_diagnostics(self.on_did_change_diagnostics)

    def on_did_change_diagnostics(self, uris: list[str]):
        run_future(self.draw_diagnotsics(uris))

    async def draw_diagnotsics(self, uris: list[str]):
        window = self.view.window()
        if not window:
            return

        for uri in uris:
            _, file_name = parse_uri(uri)
            view = window.find_open_file(file_name)
            if not view:
                continue
            results = await mir.get_diagnostics(view)
            errors = []
            warnings = []
            infos = []
            hints = []
            for _, diagnostics in results:
                for diagnostic in diagnostics:
                    region = range_to_region(view, diagnostic['range'])
                    severity = diagnostic.get('severity', DiagnosticSeverity.Information)
                    if severity == DiagnosticSeverity.Error:
                        errors.append(region)
                    elif severity == DiagnosticSeverity.Warning:
                        warnings.append(region)
                    elif severity == DiagnosticSeverity.Hint:
                        hints.append(region)
                    elif severity == DiagnosticSeverity.Information:
                        infos.append(region)
            view.erase_regions('mir-errors')
            view.erase_regions('mir-warnings')
            view.erase_regions('mir-infos')
            view.erase_regions('mir-hints')
            view.add_regions('mir-errors', errors, 'region.redish', flags=sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_OUTLINE | sublime.DRAW_NO_FILL)
            view.add_regions('mir-warnings', warnings, 'region.yellowish', flags=sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_OUTLINE | sublime.DRAW_NO_FILL)
            view.add_regions('mir-infos', infos, 'region.purplish', flags=sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_OUTLINE | sublime.DRAW_NO_FILL)
            view.add_regions('mir-hints', hints, 'region.bluish', flags=sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_OUTLINE | sublime.DRAW_NO_FILL)

    def on_close(self):
        if self.cleanup:
            self.cleanup()
            self.cleanup = None
