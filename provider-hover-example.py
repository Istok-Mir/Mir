# this is just a concept
from Mir.types.lsp import Hover, Diagnostic
from Mir import HoverProvider, mir, range_to_region
from Mir.types.lsp import DiagnosticSeverity

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
            message_styles: str = 'opacity: 0.4; color: var(--grayish)'
            source_styles: str = 'opacity: 0.4; color: var(--grayish)'
            if d.get('severity') == DiagnosticSeverity.Error:
                message_styles = 'color: var(--redish)'
                source_styles: str = 'opacity: 0.4; padding: 0 0.3rem; border-radius: 4px; color: var(--redish); background-color: color(var(--redish) alpha(0.1));'
            elif d.get('severity') == DiagnosticSeverity.Warning:
                message_styles = 'color:var(--yellowish)'
                source_styles: str = 'opacity: 0.4; padding: 0 0.3rem; border-radius: 4px; color: var(--yellowish); background-color: color(var(--yellowish) alpha(0.1))'
            source = d.get('source', '')
            formatted_source = ''
            if source:
                formatted_source = f"<span style='{source_styles}'>{source}</span>"
            return f"<div style='{message_styles}'>{d['message']} {formatted_source}</div>"

        return {
          'contents': [format(d) for d in diagnostics_under_cursor]
        }

