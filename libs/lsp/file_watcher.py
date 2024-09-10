from __future__ import annotations
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sublime
from wcmatch.glob import globmatch, GLOBSTAR
from .types import CreateFilesParams, RenameFilesParams, DeleteFilesParams, DidChangeWatchedFilesParams, FileChangeType
from .view_to_lsp import file_name_to_uri

file_watchers = []
def create_file_watcher(folder_name: str):
    global file_watchers
    ignore_patterns = get_global_ignore_globs()
    file_watcher = FileWatcher(folder_name, ignore_patterns=ignore_patterns)
    file_watcher.start()
    file_watchers.append(file_watcher)
    return file_watcher

def get_file_watcher(folder_name: str) -> FileWatcher | None:
    global file_watchers
    found_watchers = [fw for fw in file_watchers if fw.folder_name == folder_name]
    if found_watchers:
        return found_watchers[0]
    return None


def remove_file_watcher(folder_name: str):
    global file_watchers
    for i, file_watcher in enumerate(list(file_watchers)):
        if file_watcher.folder_name == folder_name:
            file_watcher.stop()
            file_watchers.pop(i)


class FileWatcher(FileSystemEventHandler):
    def __init__(self, folder_name, ignore_patterns):
        self.folder_name: str = folder_name
        self.watch_patterns: list[str] = []
        self.ignore_patterns: list[str] = [sublime_pattern_to_glob(p, False, folder_name) for p in ignore_patterns]
        self.observer = Observer()
        self.observer.schedule(self, folder_name, recursive=True)
        self.registar = {}

    def register(self, key: str, config: dict):
        self.registar[key] = config
        self.registar[key]['glob_patterns'] = [sublime_pattern_to_glob(p, False, self.folder_name) for p in config['glob_patterns']]

    def unregister(self, key: str):
        del self.registar[key]

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()

    def on_any_event(self, event):
        # Check if the file should be processed
        if event.is_directory and event.event_type == 'modified':
            return
        for key, config in self.registar.items():
            if self.matches_patterns(event.src_path, config['glob_patterns']) and not self.matches_patterns(event.src_path, self.ignore_patterns):
                self.handle_event(event, config)

    def handle_event(self, event, config):
        """Handle the file system event (customize this method)."""
        if event.event_type == 'deleted':
            uri = file_name_to_uri(event.src_path)
            delete_params: DeleteFilesParams = {
                'files': [{
                    'uri': uri
                }]
            }
            config['on_did_delete_files'](delete_params)
            did_change_params: DidChangeWatchedFilesParams = {
                'changes': [{
                    'uri': uri,
                    'type': FileChangeType.Deleted
                }]
            }
            config['on_did_change_watched_files'](did_change_params)

        elif event.event_type == 'created':
            uri = file_name_to_uri(event.src_path)
            create_params: CreateFilesParams = {
                'files': [{
                    'uri': uri
                }]
            }
            config['on_did_create_files'](create_params)
            did_change_params: DidChangeWatchedFilesParams = {
                'changes': [{
                    'uri': uri,
                    'type': FileChangeType.Created
                }]
            }
            config['on_did_change_watched_files'](did_change_params)

        elif event.event_type == 'modified':
            uri = file_name_to_uri(event.src_path)
            did_change_params: DidChangeWatchedFilesParams = {
                'changes': [{
                    'uri': uri,
                    'type': FileChangeType.Changed
                }]
            }
            config['on_did_change_watched_files'](did_change_params)
        elif event.event_type == 'moved':
            old_uri = file_name_to_uri(event.src_path)
            new_uri = file_name_to_uri(event.dest_path)
            rename_params: RenameFilesParams = {
                'files': [{
                    'oldUri': old_uri,
                    'newUri': new_uri,
                }]
            }
            config['on_did_rename_files'](rename_params)

    def matches_patterns(self, file_path, patterns):
        """Check if the file path matches any of the given patterns using wcmatch."""
        return any(globmatch(file_path, pattern, flags=GLOBSTAR) for pattern in patterns)


def sublime_pattern_to_glob(pattern: str, is_directory_pattern: bool, root_path: str | None = None) -> str:
    """
    Convert a Sublime Text pattern (http://www.sublimetext.com/docs/file_patterns.html)
    to a glob pattern that utilizes globstar extension.
    """
    glob = pattern
    if '/' not in glob:  # basic pattern: compared against exact file or directory name
        glob = f'**/{glob}'
        if is_directory_pattern:
            glob += '/**'
    else:  # complex pattern
        # With '*/' prefix or '/*' suffix, the '*' matches '/' characters.
        if glob.startswith('*/'):
            glob = f'*{glob}'
        if glob.endswith('/*'):
            glob += '*'
        # If a pattern ends in '/' it will be treated as a directory pattern, and will match both a directory with that
        # name and any contained files or subdirectories.
        if glob.endswith('/'):
            glob += '**'
        # If pattern begins with '//', it will be compared as a relative path from the project root.
        if glob.startswith('//') and root_path:
            glob = posixpath.join(root_path, glob[2:])
        # If a pattern begins with a single /, it will be treated as an absolute path.
        if not glob.startswith('/') and not glob.startswith('**/'):
            glob = f'**/{glob}'
        if is_directory_pattern and not glob.endswith('/**'):
            glob += '/**'
    return glob


def get_global_ignore_globs() -> list[str]:
    globalprefs = sublime.active_window().active_view().settings()
    folder_exclude_patterns: list[str] = globalprefs.get('folder_exclude_patterns', [])
    file_exclude_patterns: list[str] = globalprefs.get('file_exclude_patterns', [])
    return folder_exclude_patterns + file_exclude_patterns + ['**/node_modules/**']
