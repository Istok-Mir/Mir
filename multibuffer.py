from __future__ import annotations
from Mir import get_relative_path, selector_to_language_id, get_lines
import sublime
from typing_extensions import TypedDict, cast, Union, Literal


class Multibuffer:
    def __init__(self, window: sublime.Window, id: str):
        self.syntax = "Packages/Mir/mir-multibuffer.sublime-syntax"
        self.id = id
        self.window = window

    def open(self, tab_title, content: list[MultibufferContent], flags:sublime.NewFileFlags=sublime.NewFileFlags.NONE) -> sublime.View:
        [v.close() for v in self.window.views() if v.settings().get('is_mir_references_view', False)]
        view = self.window.new_file(flags, syntax=self.syntax)
        view.set_scratch(True)
        view.settings().set('is_mir_references_view', True)
        view.set_name(tab_title)
        self.render(view, content)
        return view

    def render(self, view: sublime.View, multibuffer_content: list[MultibufferContent]):
        rendered_content = ''
        for content in multibuffer_content:
            if isinstance(content, str):
                rendered_content += content + "\n"
            else:
                file_path = content['file_path']
                relative_file_path = get_relative_path(file_path)
                syntax = sublime.find_syntax_for_file(file_path)
                language_id = ''
                if syntax:
                    language_id = selector_to_language_id(syntax.scope)
                start_line = content['start_line']
                end_line = content['end_line']
                line_content = get_lines(self.window, file_path, start_line, end_line)
                rendered_content += f"""◤ {relative_file_path}:{start_line+1}\n{line_content}\n◣\n"""

        view.run_command("append", {
            'characters': rendered_content,
            'force': False,
            'scroll_to_end': False
        })
        view.clear_undo_stack()


class BufferContent(TypedDict):
    type: Literal['Buffer']
    file_path: str
    start_line: int
    end_line: int

MultibufferContent = Union[BufferContent, str]
