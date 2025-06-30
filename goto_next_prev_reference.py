from __future__ import annotations

from Mir import parse_uri, range_to_region
from Mir.types.lsp import Location
import sublime
from Mir import mir, position_to_point, open_view
import sublime_aio


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
            if file_name != view_file_name:
                continue
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

class Cache:
    results: list[Location] = []

    @staticmethod
    def cache_hit(point: int, view):
        for ref in Cache.results:
            r = range_to_region(view, ref['range'])
            if r.contains(point):
                return True
        return False



class mir_next_reference_command(sublime_aio.ViewCommand):
    async def run(self):
        point = get_point(self.view)
        if point is None:
            return
        cache_hit = Cache.cache_hit(point, self.view)
        all_references: list[Location] = Cache.results if cache_hit else []
        if not cache_hit:
            results = await mir.references(self.view, point)
            Cache.results = []
            for _, references in results:
                if references:
                    all_references.extend(references)
            Cache.results = all_references
        ordinal_number, location = find_reference(self.view, all_references, forward=True, start_point=point)
        w = self.view.window()
        if not location or not w:
            return
        _, file_path = parse_uri(location['uri'])
        view = await open_view(file_path, w)
        w.focus_view(view)
        point = position_to_point(view, location['range']['end'])
        view.run_command('mir_go_to_point', {'point': point, 'message': f"{ordinal_number} of {len(all_references)} referenecs"})

class mir_prev_reference_command(sublime_aio.ViewCommand):
    async def run(self):
        point = get_point(self.view)
        if point is None:
            return
        cache_hit = Cache.cache_hit(point, self.view)
        all_references: list[Location] = Cache.results if cache_hit else []
        if not cache_hit:
            results = await mir.references(self.view, point)
            Cache.results = []
            for _, references in results:
                if references:
                    all_references.extend(references)
            Cache.results = all_references
        ordinal_number, location = find_reference(self.view, all_references, forward=False, start_point=point)
        w = self.view.window()
        if not location or not w:
            return
        _, file_path = parse_uri(location['uri'])
        view = await open_view(file_path, w)
        w.focus_view(view)
        point = position_to_point(view, location['range']['end'])
        view.run_command('mir_go_to_point', {'point': point, 'message': f"{ordinal_number} of {len(all_references)} referenecs"})



