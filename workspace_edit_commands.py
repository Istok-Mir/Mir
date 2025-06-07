from __future__ import annotations

from .libs.future_with_id import FutureWithId
import sublime_aio

from Mir import mir_logger, is_text_document_edit, parse_uri, is_text_edit, range_to_region, open_view, save_view, apply_text_document_edits
from Mir.types.lsp import WorkspaceEdit, TextEdit, AnnotatedTextEdit, SnippetTextEdit
import sublime
import sublime_plugin

# use `from Mir import apply_workspace_edit`
class MirApplyWorkspaceEdit(sublime_aio.ViewCommand):
    async def run(self, future_id: str, workspace_edit: WorkspaceEdit):
        try:
            window = self.view.window()
            if not window:
                return
            document_changes = workspace_edit.get('documentChanges')
            if document_changes:
                for change in document_changes:
                    was_open = False
                    if not is_text_document_edit(change):
                        mir_logger.info("Mir: TODO implement change", change)
                        continue
                    schema, file_path = parse_uri(change['textDocument']['uri'])
                    view = window.find_open_file(file_path)
                    if view:
                        was_open = True
                    else:
                        view = await open_view(file_path, window)
                    await apply_text_document_edits(view, change['edits'])
                    if not was_open:
                        view.close()
                return
            changes = workspace_edit.get('changes')
            if changes:
                for uri, text_edits in changes.items():
                    was_open = False
                    schema, file_path = parse_uri(uri)
                    view = window.find_open_file(file_path)
                    if view:
                        was_open = True
                    else:
                        view = await open_view(file_path, window)
                    await apply_text_document_edits(view, text_edits)
                    if not was_open:
                        view.close()
                return
            mir_logger.info('Mir: TODO implement workspace_edit for', document_changes)
        finally:
            future = FutureWithId.get(future_id)
            if future:
                future.set_result(None)


# use `from Mir import apply_text_document_edits`
class MirApplyTextDocumentEditsCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, future_id: str, edits: list[TextEdit | AnnotatedTextEdit | SnippetTextEdit], close_after_edit=False):
        text_edits: list[TextEdit] = []
        for e in edits:
            if is_text_edit(e):
                text_edits.append(e)
            else:
                mir_logger.info('Mir TODO implement edit for', e)
        for text_edit in reversed(text_edits):
            self.view.replace(edit, range_to_region(self.view, text_edit['range']), text_edit['newText'])
        sublime_aio.run_coroutine(self.save(future_id))

    async def save(self, future_id: str):
        await save_view(self.view)
        future = FutureWithId.get(future_id)
        if future:
            future.set_result(None)

