from __future__ import annotations
from typing import cast
from lsp.types import LanguageKind, Position, TextDocumentItem
from sublime_plugin import sublime


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

def view_to_uri(view) -> str:
    file_name = view.file_name()
    if not file_name:
        return f"buffer:{view.buffer_id()}"
    return 'file://' + file_name

def file_name_to_uri(file_name: str) -> str:
    return 'file://' + file_name


def get_view_uri(view) -> str:
    uri = view.settings().get("cn_uri")
    if not uri:
        uri = view_to_uri(view)
        view.settings().set("lsp_uri", uri)
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


