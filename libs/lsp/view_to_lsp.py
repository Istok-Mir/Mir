from __future__ import annotations
from typing import cast, Any
from typing_extensions import TypeGuard
from Mir.types.lsp import LanguageKind, Position, Range, TextDocumentItem, TextEdit, TextDocumentEdit
import sublime
from urllib.parse import urlparse
from urllib.request import url2pathname
from urllib.request import pathname2url
import os
import linecache
import re


def view_to_text_document_item(view: sublime.View) -> TextDocumentItem :
    uri = get_view_uri(view)
    language_id = 'plaintext'
    syntax = view.syntax()
    if syntax:
        language_id = selector_to_language_id(syntax.scope)
    return {
        'languageId': cast(LanguageKind, language_id),
        'text': view.substr(sublime.Region(0, view.size())),
        'uri': str(uri),
        'version': view.change_count()
    }

def point_to_position(view: sublime.View, point: int) -> Position:
    row, col = view.rowcol(point)
    return {
        "line": row,
        "character": col
    }

def position_to_point(view: sublime.View, position: Position) -> int:
    point = view.text_point(position['line'], position['character'],clamp_column=True)
    return point


def range_to_region(view: sublime.View, range: Range) -> sublime.Region:
    a = position_to_point(view, range['start'])
    b = position_to_point(view, range['end'])
    return sublime.Region(a, b)


def region_to_range(view: sublime.View, region: sublime.Region) -> Range:
    return {
        'start': point_to_position(view, region.begin()),
        'end': point_to_position(view, region.end()),
    }

def _view_to_uri(view) -> str:
    file_name = view.file_name()
    if not file_name:
        return f"buffer:{view.buffer_id()}"
    return file_name_to_uri(file_name)

def file_name_to_uri(file_name: str) -> str:
    return 'file://' + pathname2url(file_name)

async def open_view_with_uri(uri: str, lsp_range: Range, view: sublime.View) -> sublime.View:
    window = view.window()
    if not window:
        raise Exception('No window')
    schema, parsed_uri = parse_uri(uri)
    if schema == 'deno':
        # TODO introduce UriResolverProvider or something like that
        from Mir import server_for_view
        server = server_for_view('deno', view)
        syntax = sublime.find_syntax_for_file(urlparse(uri).path).path
        if not server:
            raise Exception('No server')
        response = server.send_request('deno/virtualTextDocument', {"textDocument": {"uri": uri}})
        result = await response.result
        v = window.new_file(syntax=syntax)
        v.settings().set("mir_text_document_uri", uri)
        v.set_scratch(True)
        v.set_name(uri)
        v.run_command("append", {"characters": result})
        v.set_read_only(True)
        point = position_to_point(v, lsp_range['end'])
        window.focus_view(v)
        move_cursor_to(v, point)
        return v
    return window.open_file(parsed_uri+f":{lsp_range['end']['line']+1}:{lsp_range['end']['character']+1}", sublime.ENCODED_POSITION)


def move_cursor_to(view: sublime.View, point: int) -> None:
    sel = view.sel()
    sel.clear()
    sel.add(point)
    view.run_command("add_jump_record", {"selection": [(point, point)]})
    if not view.visible_region().contains(point):
        view.show_at_center(point)


def parse_uri(uri: str) -> tuple[str, str]:
    """
    Parses an URI into a tuple where the first element is the URI scheme. The
    second element is the local filesystem path if the URI is a file URI,
    otherwise the second element is the original URI.
    """
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        path = url2pathname(parsed.path)
        if os.name == 'nt':
            netloc = url2pathname(parsed.netloc)
            path = path.lstrip("\\")
            path = re.sub(r"^/([a-zA-Z]:)", r"\1", path)  # remove slash preceding drive letter
            path = re.sub(r"^([a-z]):", _uppercase_driveletter, path)
            if netloc:
                # Convert to UNC path
                return parsed.scheme, f"\\\\{netloc}\\{path}"
            else:
                return parsed.scheme, path
        return parsed.scheme, path
    elif parsed.scheme == '' and ':' in parsed.path.split('/')[0]:
        # workaround for bug in urllib.parse.urlparse
        return parsed.path.split(':')[0], uri
    return parsed.scheme, uri


def _uppercase_driveletter(match: Any) -> str:
    """
    For compatibility with Sublime's VCS status in the status bar.
    """
    return f"{match.group(1).upper()}:"


def get_view_uri(view) -> str:
    uri = view.settings().get("mir_text_document_uri")
    if not uri:
        uri = _view_to_uri(view)
        view.settings().set("mir_text_document_uri", uri)
    return uri


def selector_to_language_id(selector: str) -> str:
    selector_to_language_id_map = {
        "source.c++": "cpp",
        "source.coffee": "coffeescript",
        "source.cs": "csharp",
        "source.dosbatch": "bat",
        "source.fixedform-fortran": "fortran", # https://packagecontrol.io/packages/Fortran
        "source.js": "javascript",
        "source.js.react": "javascriptreact", # https://github.com/Thom1729/Sublime-JS-Custom
        "source.json-tmlanguage": "jsonc", # https://github.com/SublimeText/PackageDev
        "source.json.sublime": "jsonc", # https://github.com/SublimeText/PackageDev
        "source.jsx": "javascriptreact",
        "source.Kotlin": "kotlin", # https://github.com/vkostyukov/kotlin-sublime-package
        "source.modern-fortran": "fortran", # https://packagecontrol.io/packages/Fortran
        "source.objc": "objective-c",
        "source.objc++": "objective-cpp",
        "source.shader": "shaderlab", # https://github.com/waqiju/unity_shader_st3
        "source.shell": "shellscript",
        "source.ts": "typescript",
        "source.ts.react": "typescriptreact", # https://github.com/Thom1729/Sublime-JS-Custom
        "source.tsx": "typescriptreact",
        "source.unity.unity_shader": "shaderlab", # https://github.com/petereichinger/Unity3D-Shader
        "source.yaml-tmlanguage": "yaml", # https://github.com/SublimeText/PackageDev
        "text.advanced_csv": "csv", # https://github.com/SublimeText/AFileIcon
        "text.django": "html", # https://github.com/willstott101/django-sublime-syntax
        "text.html.handlebars": "handlebars",
        "text.html.markdown": "markdown",
        "text.html.markdown.rmarkdown": "r", # https://github.com/REditorSupport/sublime-ide-r
        "text.html.vue": "vue",
        "text.jinja": "html", # https://github.com/Sublime-Instincts/BetterJinja
        "text.plain": "plaintext",
        "text.plist": "xml", # https://bitbucket.org/fschwehn/sublime_plist
        "text.tex.latex": "latex",
        "text.xml.xsl": "xsl",
    }

    result = ""
    # Try to find exact match or less specific match consisting of at least 2 components.
    scope_parts = selector.split('.')
    while len(scope_parts) >= 2:
        result = selector_to_language_id_map.get('.'.join(scope_parts))
        if result:
            break
        scope_parts.pop()
    if not result:
        # If no match, use the second component of the scope as the language ID.
        scope_parts = selector.split('.')
        result = scope_parts[1] if len(scope_parts) > 1 else scope_parts[0]
    return result if isinstance(result, str) else ""


def is_range(val: Any) -> TypeGuard[Range]:
    return isinstance(val, dict) and 'start' in val and 'end' in val


def is_text_edit(val: Any) -> TypeGuard[TextEdit]:
    return isinstance(val, dict) and 'range' in val and 'newText' in val

def is_text_document_edit(val: Any) -> TypeGuard[TextDocumentEdit]:
    return isinstance(val, dict) and 'textDocument' in val and 'edits' in val


def get_relative_path(file_path: str) -> str:
    base_dir = get_project_path(file_path)
    if base_dir:
        try:
            return os.path.relpath(file_path, base_dir)
        except ValueError:
            # On Windows, ValueError is raised when path and start are on different drives.
            pass
    return file_path


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


def get_lines(window: sublime.Window, file_name: str, start_line: int, end_line:int|None = None) -> str:
    '''
    Get the line from the buffer if the view is open, else get line from linecache.
    start_line and end_line - are 0 based. If you want to get the first line, you should pass 0.
    '''
    view = window.find_open_file(file_name)
    if view:
        if end_line is not None:
            start_point = view.text_point(start_line , 0)
            end_point = view.text_point(end_line , 0)
            return view.substr(sublime.Region(view.line(start_point).begin(), view.line(end_point).end()))
        else:
            point = view.text_point(start_line , 0)
            return view.substr(view.line(point))
    else:
        # get from linecache
        if end_line is not None:
            lines = []
            for line_index in range(start_line, end_line + 1):
                lines.append(linecache.getline(file_name, line_index + 1).strip('\n'))
            linecache.clearcache()
            return '\n'.join(lines)
        else:
            line = linecache.getline(file_name, start_line + 1)
            linecache.clearcache()
            return line
