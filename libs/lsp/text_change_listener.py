from __future__ import annotations
from typing import Iterable, TYPE_CHECKING

from .manage_servers import servers_for_view
from .types import TextDocumentContentChangeEvent, TextDocumentSyncKind, TextDocumentSyncOptions
from .view_to_lsp import get_view_uri
import sublime_plugin
import sublime
import functools
if TYPE_CHECKING:
    from .server import LanguageServer

class MirTextChangeListener(sublime_plugin.TextChangeListener):
    @classmethod
    def is_applicable(cls, buffer: sublime.Buffer) -> bool:
        v = buffer.primary_view()
        return v is not None and is_regular_view(v)

    def on_text_changed(self, changes: Iterable[sublime.TextChange]) -> None:
        view = self.buffer.primary_view()
        if not view:
            return
        incremental_changes: list[TextDocumentContentChangeEvent] = []
        if changes is None:
            return
        incremental_changes = [text_change_to_text_document_content_change_event(text_change) for text_change in changes]
        servers = servers_for_view(view)
        for server in servers:
            # get sync kind for server
            textDocumentSyncKind = 0
            text_document_sync: TextDocumentSyncOptions | TextDocumentSyncKind = server.capabilities.get('textDocumentSync')
            if isinstance(text_document_sync, dict):
                textDocumentSyncKind = text_document_sync.get('change')
            elif isinstance(text_document_sync, int):
                textDocumentSyncKind = text_document_sync
            if textDocumentSyncKind == TextDocumentSyncKind.None_:
                # skipping
                continue
            server.pending_changes.setdefault(view.id(), {
                'textDocument': {
                    'uri': get_view_uri(view),
                    'version': view.change_count()
                },
                'contentChanges': []
            })
            server.pending_changes[view.id()]['textDocument']['version'] = view.change_count()
            if textDocumentSyncKind == TextDocumentSyncKind.Incremental:
                server.pending_changes[view.id()]['contentChanges'].extend(incremental_changes)
            elif textDocumentSyncKind == TextDocumentSyncKind.Full:
                full_file_changes: list[TextDocumentContentChangeEvent] = [{
                    'text': view.substr(sublime.Region(0, view.size()))
                }]
                server.pending_changes[view.id()]['contentChanges'] = full_file_changes
            else:
                raise Exception(f'TextChangeListener. ${server.name} somehow managed to get here. textDocumentSyncKind is {textDocumentSyncKind}.')
            debounce_func = functools.partial(self.debounce_sending_changes, server, view, last_change_count=view.change_count())
            sublime.set_timeout(debounce_func, 100)

    def debounce_sending_changes(self, server: LanguageServer, view:sublime.View, last_change_count: int):
        if view.change_count() == last_change_count and server.status == 'ready':
            server.send_did_change_text_document()


def text_change_to_text_document_content_change_event(change: sublime.TextChange) -> TextDocumentContentChangeEvent:
    return {
        "range": {
            "start": {"line": change.a.row, "character": change.a.col_utf16},
            "end": {"line": change.b.row, "character": change.b.col_utf16}},
        "rangeLength": change.len_utf16,
        "text": change.str
    }


def is_regular_view(v: sublime.View) -> bool:
    # Not from the quick panel (CTRL+P), and not a special view like a console, output panel or find-in-files panels.
    if v.window() is None: # detect hover popup
        return False
    if v.element() is not None:
        return False
    if v.settings().get('is_widget'):
        return False
    sheet = v.sheet()
    if not sheet:
        return False
    if sheet.is_transient():
        return False
    return True
