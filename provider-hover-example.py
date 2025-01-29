# this is just a concept
from .api.types import Hover, Diagnostic
from .api import HoverProvider, mir
from .api.helpers import range_to_region


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

        return {
          'contents': [d['message'] + ' ' + d.get('source', '') for d in diagnostics_under_cursor]
        }
