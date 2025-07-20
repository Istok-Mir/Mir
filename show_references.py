from __future__ import annotations

from Mir import apply_workspace_edit
from .multibuffer import Multibuffer, MultibufferContent

from .libs.lsp.view_to_lsp import get_lines, get_relative_path, is_text_edit
import sublime_aio
import sublime
import sublime_plugin
from Mir import mir, parse_uri
from Mir.types.lsp import Location, WorkspaceEdit
from Mir import mir_logger


class mir_show_references_command(sublime_aio.ViewCommand):
    async def run(self):
        try:
            point = get_point(self.view)
            if point is None:
                return
            results = await mir.references(self.view, point)
            all_references: list[Location] = []
            for _, references in results:
                if references:
                    all_references.extend(references)
            w = self.view.window()
            if not w:
                return
            if not all_references:
                w.status_message('No references')
                return
            content: list[MultibufferContent] = []
            extended_locations = merge_locations(extend_locations(all_references, 2))

            word = self.view.substr(self.view.word(point))
            title = f'{len(all_references)} references "{word}"'
            workspace_edits: WorkspaceEdit = {
                'changes': {}
            }
            for reference in extended_locations:
                _, file_path= parse_uri(reference['uri'])
                content.append({
                    'type': 'Buffer',
                    'file_path': file_path,
                    'start_line': reference['range']['start']['line'],
                    'end_line': reference['range']['end']['line']
                })
                workspace_edits['changes'].setdefault(reference['uri'], []).append({
                    'range': {
                        'start': {
                            'line': reference['range']['start']['line'],
                            'character': 0
                        },
                        'end': {
                            'line': reference['range']['end']['line'],
                            'character': -1
                        }
                    },
                    'newText': get_lines(w, file_path, reference['range']['start']['line'], reference['range']['end']['line'])
                })

            multibuffer = Multibuffer(w, 'mir-references-view')
            multibuffer.open(title, content)
            w.settings().set('mir.reference_workspace_edits', workspace_edits)
        except Exception as e:
            mir_logger.error("Show reference failed",  exc_info=e)



class InterceptKeyboard(sublime_plugin.ViewEventListener):
    def on_text_command(self, command_name, args):
        if self.view.settings().get('is_mir_references_view', False):
            point = get_point(self.view)
            if command_name == "select_all" and point and self.view.match_selector(point, "markup.raw.code-fence"):
                return ('mir_select_multibuffer_block')
            if command_name == 'find_under_expand' and point and not self.view.match_selector(point, "markup.raw.code-fence"):
                return ("find_under_expand_skip")

    def on_query_context(self, key: str, operator: int, operand, match_all: bool) -> bool | None:
        if (key == 'mir.is_reference_panel_visible'):
            return bool(self.view.settings().get('is_mir_references_view', False))

class mir_select_multibuffer_block_command(sublime_plugin.TextCommand):
    def run(self, edit):
        point = get_point(self.view)
        if point:
            region = self.view.expand_to_scope(point, "markup.raw.code-fence")
            if region:
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(region.begin(), region.end() -1))


class mir_save_multibuffer_blocks_command(sublime_aio.ViewCommand):
    async def run(self):
        w = self.view.window()
        if not w:
            return
        workspace_edits: WorkspaceEdit | None = w.settings().get('mir.reference_workspace_edits', None)
        print('workspace_edits', workspace_edits)
        if workspace_edits is None:
            return
        new_workspace_edits: WorkspaceEdit = {
            'changes': {}
        }
        for file_uri in workspace_edits.get('changes', {}):
            if file_uri not in new_workspace_edits['changes']:
                new_workspace_edits['changes'][file_uri] = []
            for change in workspace_edits['changes'][file_uri]:
                if not is_text_edit(change):
                    continue
                _, file_path = parse_uri(file_uri)
                relative_file_path = get_relative_path(file_path)
                row = change['range']['start']['line']
                start = self.view.find(f'{relative_file_path}:{row+1}', 0)
                end = self.view.find('```', start.end())
                new_range = sublime.Region(
                    start.end()+1,
                    end.begin()-1
                )
                new_text = self.view.substr(new_range)
                change['newText'] = new_text

                updated_change = change.copy()
                lines = new_text.split('\n')
                number_of_line_rows = len(lines)
                updated_change['range'] = {
                    'start': change['range']['start'],
                    'end': {
                        'line': change['range']['start']['line'] + number_of_line_rows - 1, #  lines in LSP are 0 based, so thus - 1
                        'character': len(lines[-1])
                    }
                }
                new_workspace_edits['changes'][file_uri].append(updated_change)
        await apply_workspace_edit(self.view, new_workspace_edits)
        w.settings().set('mir.reference_workspace_edits', new_workspace_edits)


def extend_locations(locations: list[Location], offset_lines:int) -> list[Location]:
    def transform(l: Location) -> Location:
        return {
            'uri': l['uri'],
            'range': {
                'start': {'line': max(0, l['range']['start']['line'] - offset_lines), 'character': l['range']['start']['character']},
                'end': {'line': l['range']['end']['line'] + offset_lines, 'character': l['range']['end']['character']},
            }
        }
    return [transform(l)for l in locations]


def merge_locations(locations: list[Location]) -> list[Location]:
    sorted_location = sorted(locations, key=lambda l: (l['uri'], l['range']['start']['line'], l['range']['start']['character']))
    merged_locations: list[Location] = []

    for location in sorted_location:
        if not merged_locations:
            merged_locations.append(location)
            continue
        last_location = merged_locations[-1]
        # overlaps
        if last_location['uri'] ==  location['uri'] and location['range']['start']['line'] <= last_location['range']['end']['line']:
            last_location['range']['end'] = location['range']['end']
            continue
        merged_locations.append(location)
    return merged_locations


def get_point(view: sublime.View):
    sel = view.sel()
    region = sel[-1] if sel else None
    if region is None:
        return
    return region.b
