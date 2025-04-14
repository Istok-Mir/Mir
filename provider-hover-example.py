# this is just a concept
from Mir.types import Hover, Diagnostic
from Mir import HoverProvider, mir
from Mir.api import range_to_region
from Mir.types import DiagnosticSeverity


#Example of a hover provider
class DiagnosticsHoverProvider(HoverProvider):
    name= 'Diagnostics Hover Provider'
    activation_events = {
        'selector': '*',
    }
    async def provide_hover(self, view, hover_point, hover_zone) -> Hover:
        all_diagnostics = await mir.get_diagnostics(view)
        diagnostics_under_cursor: list[Diagnostic] = []
        for _uri, diagnostics in all_diagnostics:
            diagnostics_under_cursor.extend([d for d in diagnostics if range_to_region(view, d['range']).contains(hover_point)])

        def format(d: Diagnostic):
            styles: str = 'opacity: 0.4; color: var(--grayish)'
            if d.get('severity') == DiagnosticSeverity.Error:
                styles = 'color: var(--redish)'
            elif d.get('severity') == DiagnosticSeverity.Warning:
                styles = 'color:var(--yellowish)'
            return f"<div style='{styles}'>{d['message']}</div>"
            
        return {
          'contents': [format(d) + ' ' + d.get('source', '') for d in diagnostics_under_cursor]
        }
