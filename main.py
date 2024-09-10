from __future__ import annotations
from .libs.lsp.manage_servers import ManageServers
from .libs.lsp.text_change_listener import TextChangeListener
from .libs.lsp.file_watcher import setup_file_watchers, cleanup_file_watchers
import sublime

def plugin_loaded():
    windows = sublime.windows()
    for window in windows:
        setup_file_watchers(window)

def plugin_unloaded():
    cleanup_file_watchers()
