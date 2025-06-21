from __future__ import annotations

from Mir import apply_workspace_edit

from .libs.lsp.view_to_lsp import is_text_edit, region_to_range, selector_to_language_id
import sublime_aio
import sublime
import sublime_plugin
import linecache
from Mir import mir, parse_uri
from Mir.types.lsp import Location, WorkspaceEdit
import os

view_reference_name = 'Mir References'

class mir_show_references_command(sublime_aio.ViewCommand):
    async def run(self):
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
        grouped_locations_by_uri = group_locations_by_uri(w, all_references)
        [v.close() for v in w.views() if v.settings().get('is_mir_references_view', False)]
        new_view = w.new_file(sublime.NewFileFlags.ADD_TO_SELECTION | sublime.NewFileFlags.SEMI_TRANSIENT, syntax="Packages/Markdown/Markdown.sublime-syntax")
        new_view.settings().set('is_mir_references_view', True)
        word = self.view.substr(self.view.word(point))
        new_view.set_name(f'{len(all_references)} references {word}')
        new_view.set_scratch(True)
        content = ''
        workspace_edits: WorkspaceEdit = {
            'changes': {}
        }
        for file_uri in grouped_locations_by_uri:
            if file_uri not in workspace_edits['changes']:
                workspace_edits['changes'][file_uri] = []
            for reference in grouped_locations_by_uri[file_uri]:
                row, line_content =  reference
                _, file_path = parse_uri(file_uri)
                relative_file_path = get_relative_path(file_path)
                syntax = self.view.syntax()
                language_id = ''
                if syntax:
                    language_id = selector_to_language_id(syntax.scope)
                lines = line_content.split('\n')
                number_of_line_rows = len(lines)
                workspace_edits['changes'][file_uri].append({
                    'range': {
                        'start': {'line': row, 'character': 0},
                        'end': {
                            'line': row + number_of_line_rows - 1, # lines in LSP are 0 based, so thus - 1
                            'character': len(lines[-1])
                        }
                    },
                    'newText': line_content
                })
                content += f"""```{language_id}\t{relative_file_path}:{row+1}
{line_content}
```\n"""
        new_view.run_command("append", {
            'characters': content,
            'force': False,
            'scroll_to_end': False
        })
        new_view.clear_undo_stack()
        found_regions = [r for r in new_view.find_all(fr'\b{word}\b') if new_view.match_selector(r.begin()+1, "markup.raw.code-fence")]
        new_view.sel().clear()
        new_view.sel().add_all(found_regions)
        new_view.settings().set('mir.referemce_workspace_edits', workspace_edits)

def group_locations_by_uri(
    window: sublime.Window,
    locations: list[Location]
) -> dict[str, list[tuple[int, str]]]:
    """Return a dictionary that groups locations by the URI it belongs."""
    grouped_locations: dict[str, list[tuple[int, str]]] = {}
    files_lines_added: dict[str, list[int]] = {}
    for location in locations:
        uri = location['uri']
        _, file_path = parse_uri(uri)
        row_line = location['range']['start']['line']
        # get line of the reference, to showcase its use
        if grouped_locations.get(uri) is None:
            grouped_locations[uri] = []
            files_lines_added[uri] = []
        how_many_lines_to_show_around = 2
        for row in range(max(0, row_line - how_many_lines_to_show_around), row_line + how_many_lines_to_show_around + 1):
            if row in files_lines_added[uri]:
                continue
            files_lines_added[uri].append(row)
            line_content = get_line_content(window, file_path, row, False)
            if line_content.startswith('```'):
                print('skipping ```')
                continue
            grouped_locations[uri].append((row, line_content))
    # we don't want to cache the line, we always want to get fresh data
    linecache.clearcache()
    return squash_nearby_lines(grouped_locations)


def get_line_content(window: sublime.Window, file_name: str, row: int, strip: bool = True) -> str:
    '''
    Get the line from the buffer if the view is open, else get line from linecache.
    row - is 1 based. If you want to get the first line, you should pass 0.
    '''
    view = window.find_open_file(file_name)
    if view:
        # get from buffer
        # linecache row is not 1 based, so we decrement it by 1 to get the correct line.
        point = view.text_point(row , 0)
        line = view.substr(view.line(point))
    else:
        # get from linecache
        line = linecache.getline(file_name, row + 1)
    return line.strip() if strip else line


def get_point(view: sublime.View):
    sel = view.sel()
    region = sel[-1] if sel else None
    if region is None:
        return
    return region.b


def squash_nearby_lines(input_data: dict[str, list[tuple[int, str]]]) -> dict[str, list[tuple[int, str]]]:
    squashed_data: dict[str, list[tuple[int, str]]] = {}

    for uri, references in input_data.items():
        if not references:
            squashed_data[uri] = []
            continue
        sorted_references: list[tuple[int, str]] = sorted(references, key=lambda x: x[0])
        current_squashed_block: list[tuple[int, str]] = []
        result_for_uri: list[tuple[int, str]] = []
        for i, (row, line_content) in enumerate(sorted_references):
            if not current_squashed_block:
                # If the current block is empty, start a new one with the current reference.
                current_squashed_block.append((row, line_content))
            else:
                # Get the row number of the last line added to the current squashed block.
                last_row_in_block: int = current_squashed_block[-1][0]
                if row == last_row_in_block + 1:
                    # If the current line's row is exactly one greater than the last line's row,
                    # it's consecutive, so add it to the current block.
                    current_squashed_block.append((row, line_content))
                else:
                    # If the current line is not consecutive, it means the previous block is complete.
                    # Extract the first reference's row and column for the combined entry.
                    first_row: int = current_squashed_block[0][0]

                    # Join all line contents in the current block with a newline character.
                    combined_content: str = "\n".join([item[1] for item in current_squashed_block])

                    # Add the combined entry to the result list for this URI.
                    result_for_uri.append((first_row, combined_content))

                    # Start a new squashed block with the current non-consecutive line.
                    current_squashed_block = [(row, line_content)]

        # After the loop finishes, there might be a pending `current_squashed_block`
        # that needs to be added to the results.
        if current_squashed_block:
            first_row = current_squashed_block[0][0]
            combined_content = "\n".join([item[1] for item in current_squashed_block])
            result_for_uri.append((first_row, combined_content))

        # Assign the processed list of squashed references to the URI in the final dictionary.
        squashed_data[uri] = result_for_uri

    return squashed_data



def get_project_path(file_path: str) -> str | None:
    active_window = sublime.active_window()
    if not active_window:
        return None
    folders = active_window.folders()
    candidate: str | None = None
    for folder in folders:
        if file_path.startswith(folder):
            if candidate is None or len(folder) > len(candidate):
                candidate = folder
    return candidate

def get_relative_path(file_path: str) -> str:
    base_dir = get_project_path(file_path)
    if base_dir:
        try:
            return os.path.relpath(file_path, base_dir)
        except ValueError:
            # On Windows, ValueError is raised when path and start are on different drives.
            pass
    return file_path


class InterceptKeyboard(sublime_plugin.ViewEventListener):
    def on_text_command(self, command_name, args):
        if self.view.settings().get('is_mir_references_view', False):
            point = get_point(self.view)
            if command_name == "select_all" and point and self.view.match_selector(point, "markup.raw.code-fence"):
                return ('asd')
            if command_name == 'find_under_expand' and point and not self.view.match_selector(point, "markup.raw.code-fence"):
                return ("find_under_expand_skip")

    def on_query_context(self, key: str, operator: int, operand, match_all: bool) -> bool | None:
        if (key == 'mir.is_reference_panel_visible'):
            return bool(self.view.settings().get('is_mir_references_view', False))
        if (key == 'is_empty_block'):
            if self.view.settings().get('is_mir_references_view', False):
                return bool(self.view.settings().get('is_mir_references_view', False))

class AsdCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        point = get_point(self.view)
        if point:
            region = self.view.expand_to_scope(point, "markup.raw.code-fence")
            if region:
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(region.begin(), region.end() -1))


class DddCommand(sublime_aio.ViewCommand):
    async def run(self):
        workspace_edits: WorkspaceEdit | None = self.view.settings().get('mir.referemce_workspace_edits', None)
        if workspace_edits is None:
            return
        new_workspace_edits: WorkspaceEdit = {
            'changes': {}
        }
        print(workspace_edits['changes'])
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
                print('start looking for',f'{relative_file_path}:{row+1}', start)
                end = self.view.find('```', start.end())
                new_range = sublime.Region(
                    start.end()+1,
                    end.begin()-1
                )
                new_text = self.view.substr(new_range)
                change['newText'] = new_text
                print('new_text', new_text)

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
        await apply_workspace_edit(self.view, workspace_edits)
        self.view.settings().set('mir.referemce_workspace_edits', new_workspace_edits)




