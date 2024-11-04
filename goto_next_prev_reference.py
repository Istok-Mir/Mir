from __future__ import annotations

from .libs.lsp.view_to_lsp import get_view_uri, parse_uri, range_to_region
from .libs.lsp.types import Location
import sublime
import sublime_plugin
from .api import mir, run_future
from .api.helpers import position_to_point
import operator
from .open_view import open_view


def find_reference(
    view: sublime.View,
    references: list[Location],
    forward: bool,
    start_point: int
) -> tuple[int, Location | None]:
    # Sort references by URI, line, and character
    sorted_references = sorted(
        references,
        key=lambda ref: (ref['uri'], ref['range']['start']['line'], ref['range']['start']['character'])
    )
    if not sorted_references:
        return (0, None)
    view_file_name = view.file_name()
    location: Location | None = None
    location_index = 0
    # find next/prev location
    for index, reference in enumerate(sorted_references):
        region = range_to_region(view, reference['range'])
        _, file_name = parse_uri(reference['uri'])
        if region.contains(start_point):
            location_index = index+1 if forward else index-1
            break
    # normalize index
    if location_index < 0:
        location_index = len(sorted_references) - 1
    if location_index >= len(sorted_references):
        location_index = 0
    location = sorted_references[location_index]
    return location_index+1, location
    

def get_point(view: sublime.View):
    sel = view.sel()
    region = sel[0] if sel else None
    if region is None:
        return
    return region.b

class MirNextReferenceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        point = get_point(self.view)
        if point is None:
            return
        run_future(self.goto_next(point))

    async def goto_next(self, point: int):
        results = await mir.references(self.view, point)
        all_references: list[Location] = []
        for _, references in results:
            if references:
                all_references.extend(references)
        ordinal_number, location = find_reference(self.view, all_references, forward=True, start_point=point)
        w = self.view.window()
        if not location or not w:
            return
        _, file_path = parse_uri(location['uri'])
        view = await open_view(file_path, w)
        w.focus_view(view)
        point = position_to_point(view, location['range']['end'])
        view.run_command('mir_go_to_point', {'point': point, 'message': f"{ordinal_number} of {len(all_references)} referenecs"})

class MirPrevReferenceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        point = get_point(self.view)
        if point is None:
            return
        run_future(self.goto_prev(point))

    async def goto_prev(self, point: int):
        results = await mir.references(self.view, point)
        all_references: list[Location] = []
        for _, references in results:
            if references:
                all_references.extend(references)
        ordinal_number, location = find_reference(self.view, all_references, forward=False, start_point=point)
        w = self.view.window()
        if not location or not w:
            return
        _, file_path = parse_uri(location['uri'])
        view = await open_view(file_path, w)
        point = position_to_point(view, location['range']['end'])
        view.run_command('mir_go_to_point', {'point': point, 'message': f"{ordinal_number} of {len(all_references)} referenecs"})



