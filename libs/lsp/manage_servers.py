from __future__ import annotations
from ..event_loop import run_future
from .view_to_lsp import get_view_uri, view_to_text_document_item
from .server import LanguageServer, matches_activation_event_on_uri, is_applicable_view
from .server_request_and_notification_handlers import attach_server_request_and_notification_handlers
from .capabilities import ServerCapability
import sublime
import sublime_plugin
import copy


def servers_for_view(view: sublime.View, capability: ServerCapability | None = None) -> list[LanguageServer]:
    if capability:
        return [s for s in ManageServers.servers_for_view(view) if is_applicable_view(view, s.activation_events) and s.capabilities.has(capability)]
    return [s for s in ManageServers.servers_for_view(view) if is_applicable_view(view, s.activation_events)]


async def open_document(view: sublime.View):
    window = view.window()
    if not window:
        return
    server_for_the_view = servers_for_view(view)
    if len(server_for_the_view) == 0: # start the servers if not started
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
        server.notify.did_open_text_document({
            'textDocument': view_to_text_document_item(view)
        })


def close_document(view: sublime.View):
    for server in servers_for_view(view):
        server.notify.did_close_text_document({
            'textDocument': {
                'uri': get_view_uri(view)
            }
        })
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

    def on_pre_close_window(self, window):
        for server in ManageServers.servers_for_window(window):
            server.stop()
        ManageServers.detach_all_servers_from_window(window)
