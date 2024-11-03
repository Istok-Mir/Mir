from __future__ import annotations

from .pull_diagnostics import pull_diagnostics
from ..event_loop import run_future
from .view_to_lsp import get_view_uri, view_to_text_document_item
from .server import LanguageServer, matches_activation_event_on_uri, is_applicable_view
from .file_watcher import remove_file_watcher
from .capabilities import ServerCapability
import sublime
import sublime_plugin


def servers_for_view(view: sublime.View, capability: ServerCapability | None = None) -> list[LanguageServer]:
    if capability:
        return [s for s in ManageServers.servers_for_view(view) if is_applicable_view(view, s.activation_events) and s.capabilities.has(capability)]
    return [s for s in ManageServers.servers_for_view(view) if is_applicable_view(view, s.activation_events)]


def server_for_view(name: str, view: sublime.View) -> LanguageServer | None:
    language_server = next(iter([s for s in ManageServers.servers_for_view(view) if is_applicable_view(view, s.activation_events) and s.name == name]), None)
    return language_server


def servers_for_window(window: sublime.Window, capability: ServerCapability | None = None) -> list[LanguageServer]:
    if capability:
        return [s for s in ManageServers.servers_for_window(window) if s.capabilities.has(capability)]
    return [s for s in ManageServers.servers_for_window(window)]


async def open_document(view: sublime.View):
    window = view.window()
    if not window:
        return
    for server in ManageServers.language_servers_pluguins:
        if not is_applicable_view(view, server.activation_events):
            continue
        if server.name not in [s.name for s in ManageServers.servers_for_view(view)]:
            try:
                new_server = server()
                await new_server.start(view)
                ManageServers.attach_server_to_window(new_server, window)
            except Exception as e:
                print(f'Mir ({server.name}) | Error while starting.', e)
                continue
    for server in servers_for_view(view):
        text_document = view_to_text_document_item(view)
        server.notify.did_open_text_document({
            'textDocument': text_document
        })
        server.open_views.append(view)
        await pull_diagnostics(server, text_document['uri'])


def close_document(view: sublime.View):
    for server in servers_for_view(view):
        server.notify.did_close_text_document({
            'textDocument': {
                'uri': get_view_uri(view)
            }
        })
        server.open_views = [v for v in server.open_views if v.id() != view.id()]
        if server.activation_events.get('on_uri'): # close servers who specify on_uri activation event
            window = view.window()
            if not window:
                continue
            relevant_views = [matches_activation_event_on_uri(view, server.activation_events) for view in window.views()]
            if len(relevant_views) <= 1:
                server.stop()
                ManageServers.detach_server_from_window(server, window)


class ManageServers(sublime_plugin.EventListener):
    language_servers_pluguins: list[LanguageServer] = []
    language_servers_per_window: dict[int, list[LanguageServer]] = {}

    @classmethod
    def servers_for_view(cls, view: sublime.View):
        window = view.window()
        if not window:
            return []
        return [s for s in ManageServers.language_servers_per_window.get(window.id(), [])]

    @classmethod
    def servers_for_window(cls, window: sublime.Window):
        return [s for s in ManageServers.language_servers_per_window.get(window.id(), [])]

    @classmethod
    def attach_server_to_window(cls, server: LanguageServer, window: sublime.Window):
        ManageServers.language_servers_per_window.setdefault(window.id(), [])
        ManageServers.language_servers_per_window[window.id()].append(server)

    @classmethod
    def detach_server_from_window(cls, server: LanguageServer, window: sublime.Window):
        ManageServers.language_servers_per_window[window.id()] = [s for s in ManageServers.language_servers_per_window[window.id()] if s != server]

    @classmethod
    def detach_all_servers_from_window(cls, window: sublime.Window):
        del ManageServers.language_servers_per_window[window.id()]

    def on_init(self, views: list[sublime.View]):
        run_future(self.initialize(views))

    async def initialize(self, views: list[sublime.View]):
        for v in views:
            await open_document(v)

    def on_pre_move(self, view):
        print('EventListener on_pre_move', view)

    def on_post_move(self, view):
        print('EventListener on_post_move', view)

    def on_reload(self, view):
        print('EventListener on_reload', view)

    def on_revert(self, view):
        print('EventListener on_revert', view)

    def on_load(self, view):
        run_future(open_document(view))

    def on_pre_close(self, view):
        close_document(view)

    def on_new_window(self, window):
        print('EventListener on_new_window', window)

    def on_pre_close_window(self, window: sublime.Window):
        for server in ManageServers.servers_for_window(window):
            server.stop()
        for folder_name in window.folders():
            remove_file_watcher(folder_name)
        ManageServers.detach_all_servers_from_window(window)
