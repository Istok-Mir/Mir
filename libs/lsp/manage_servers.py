from __future__ import annotations
from event_loop import run_future
from .view_to_lsp import get_view_uri, view_to_text_document_item
from .server import LanguageServer, matches_activation_event_on_uri
from .capabilities import ServerCapability
import sublime
import sublime_plugin


def servers_for_view(view: sublime.View, capability: ServerCapability | None = None) -> list[LanguageServer]:
    if capability:
        return [s for s in ManageServers.started_servers if s.is_applicable_view(view) and s.capabilities.has(capability)]
    return [s for s in ManageServers.started_servers if s.is_applicable_view(view)]


async def open_document(view: sublime.View):
    for server in ManageServers.all_servers:
        if not server.is_applicable_view(view):
            continue
        if server not in ManageServers.started_servers:
            try:
                await server.start()
                ManageServers.started_servers.append(server)
            except Exception as e:
                print(f'Mir ({server.name}) | Error while starting.', e)
                continue
        text_document = view_to_text_document_item(view)
        server.notify.did_open_text_document({
            'textDocument': text_document
        })


def close_document(view: sublime.View):
    for server in servers_for_view(view):
        server.notify.did_close_text_document({
            'textDocument': {
                'uri': get_view_uri(view)
            }
        })
        if matches_activation_event_on_uri(view, server.configuration['activation_events']): # close servers who specify on_uri activation event
            server.stop()
            ManageServers.started_servers = [s for s in ManageServers.started_servers if s != server]


class ManageServers(sublime_plugin.EventListener):
    all_servers: list[LanguageServer] = []
    started_servers: list[LanguageServer] = []

    def on_init(self, views: list[sublime.View]):
        run_future(self.initialize(views))

    async def initialize(self, views: list[sublime.View]):

        # start servers that have selector "*"
        for server in ManageServers.all_servers:
            if server.configuration['activation_events']['selector'] == '*':
                try:
                    await server.start()
                    ManageServers.started_servers.append(server)
                except Exception as e:
                    print(f'Mir ({server.name}) | Error while starting.', e)
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

    def on_activated(self, view):
        print('EventListener on_activated', view)

    def on_close(self, view):
        close_document(view)

    def on_new_window(self, window):
        print('EventListener on_new_window', window)

    def on_pre_close_window(self, window):
        print('EventListener on_pre_close_window', window)

    def on_exit(self):
        for server in ManageServers.started_servers:
            server.stop()
