from __future__ import annotations

from .libs.event_loop import run_future
from .open_view import open_view, save_view

from .api.helpers import is_text_document_edit, parse_uri, is_text_edit, range_to_region
import sublime
import sublime_plugin
from .api.types import WorkspaceEdit, TextEdit, AnnotatedTextEdit, SnippetTextEdit

class MirApplyWorkspaceEdit(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, workspace_edit: WorkspaceEdit):
        run_future(self.apply(workspace_edit))

    async def apply(self, workspace_edit: WorkspaceEdit):
        window = self.view.window()
        if not window:
            return
        document_changes = workspace_edit.get('documentChanges')
        if document_changes:
            for change in document_changes:
                is_view_open = False
                if not is_text_document_edit(change):
                    print("Mir: TODO implement change", change)
                    continue
                schema, file_path = parse_uri(change['textDocument']['uri'])
                view = window.find_open_file(file_path)
                if view:
                    is_view_open = True
                else:
                    view = await open_view(file_path, window)
                view.run_command('mir_apply_text_document_edits', {'edits': change['edits'] })
                await save_view(view)
                if not is_view_open:
                    view.close()
            return
        changes = workspace_edit.get('changes')
        if changes:
            for uri, text_edits in changes.items():
                is_view_open = False
                schema, file_path = parse_uri(uri)
                view = window.find_open_file(file_path)
                if view:
                    is_view_open = True
                else:
                    view = await open_view(file_path, window)
                view.run_command('mir_apply_text_document_edits', {'edits': text_edits })
                await save_view(view)
                if not is_view_open:
                    view.close()
            return
        print('Mir: TODO implement workspace_edit for', document_changes)
        


class MirApplyTextDocumentEditsCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, edits: list[TextEdit | AnnotatedTextEdit | SnippetTextEdit]):
        text_edits: list[TextEdit] = []
        print('ovde apply ediut', self.view.file_name())
        for e in edits:
            if is_text_edit(e):
                text_edits.append(e)
            else:
                print('Mir TODO implement edit for', e)
        for text_edit in reversed(text_edits):
            self.view.replace(edit, range_to_region(self.view, text_edit['range']), text_edit['newText'])



