from __future__ import annotations
from ..future_with_id import FutureWithId
import sublime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Mir.types.lsp import WorkspaceEdit, TextEdit, AnnotatedTextEdit, SnippetTextEdit


async def apply_workspace_edit(view: sublime.View, workspace_edit: WorkspaceEdit):
    future = FutureWithId()
    view.run_command('mir_apply_workspace_edit', {
        'future_id': future.id,
        'workspace_edit': workspace_edit
    })
    return future


def apply_text_document_edits(view: sublime.View, edits: list[TextEdit | AnnotatedTextEdit | SnippetTextEdit] | list[AnnotatedTextEdit] | list[TextEdit] | list[SnippetTextEdit]): # the wierd type is to silence pyright
    view.run_command('mir_apply_text_document_edits', {
        'edits': edits
    })


