# this is just a concept
from .api.types import Hover, Diagnostic, DiagnosticSeverity
from .api import HoverProvider, mir
from .api.helpers import range_to_region
import sublime


#Example of a hover provider
class DiagnosticsHoverProvider(HoverProvider):
    name= 'Package Json Enhancer'
    activation_events = {
        'selector': '*',
    }
    async def provide_hover(self, view: sublime.View, hover_point: int) -> Hover:
        all_diagnostics = await mir.get_diagnostics(view)
        diagnostics_under_cursor: list[Diagnostic] = []
        for _uri, diagnostics in all_diagnostics:
            diagnostics_under_cursor.extend([d for d in diagnostics if range_to_region(view, d['range']).contains(hover_point)])

        def format_diagnostics(diagnostic: Diagnostic):
            return f"<p>{diagnostic['message']}</p>"

        return {
          'contents': [format_diagnostics(d) for d in diagnostics_under_cursor]
        }


def plugin_loaded() -> None:
    DiagnosticsHoverProvider.setup()


def plugin_unloaded() -> None:
    DiagnosticsHoverProvider.cleanup()
