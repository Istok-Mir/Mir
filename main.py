from __future__ import annotations
from event_loop import run_future
from lsp.lsp_requests import Request
from lsp.manage_servers import ManageServers, servers_for_view
from lsp.providers import Providers
from lsp.minihtml import FORMAT_MARKED_STRING, FORMAT_MARKUP_CONTENT, minihtml
from lsp.server import LanguageServer, is_applicable_view
from lsp.types import CompletionParams, HoverParams
from lsp.view_to_lsp import get_view_uri, point_to_position
from sublime_types import Point
import asyncio
import sublime
import sublime_plugin
from lsp.text_change_listener import TextChangeListener


def register_language_server(server: LanguageServer):
    if server in ManageServers.all_servers:
        print(f'register_language_server {server.name} is skipped because it was already registred.')
        return
    ManageServers.all_servers.append(server)


def unregister_language_server(server: LanguageServer):
    server.stop()
    ManageServers.started_servers = [s for s in ManageServers.started_servers if s != server]
    ManageServers.all_servers = [s for s in ManageServers.started_servers if s != server]



class DocumentListener(sublime_plugin.ViewEventListener):
    _hover_requests: list[Request] = []

    def on_query_completions(self, _prefix: str, locations: list[Point]):
        completion_list = sublime.CompletionList()
        point = locations[0]
        params: CompletionParams = {
            'position': point_to_position(self.view, point),
            'textDocument': {
                'uri': get_view_uri(self.view)
            }
        }
        run_future(self.do_completions(completion_list, params, point))
        return completion_list

    async def do_completions(self, completion_list: sublime.CompletionList, params: CompletionParams, point: int):
        completions: list[sublime.CompletionValue] = []
        for server in servers_for_view(self.view):
            if not server.capabilities.has('completionProvider'):
                continue
            data=None
            try:
                data = await server.send.completion(params).result
            except Exception as e:
                print('CompletionError:', e)
            if isinstance(data, dict):
                items = data['items']
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
        try:
            completion_providers = [provider for provider in Providers.completion_providers if is_applicable_view(self.view, provider.activation_events)]
            providers_results = await asyncio.gather(*[provider.provide_completion_items(self.view, point) for provider in completion_providers])
            for data in providers_results: # todo refactor this. this is just a POC
              if isinstance(data, list):
                items = data
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
        except Exception as e:
            print('CompletionProvidersError:', e)
        completion_list.set_completions(completions, sublime.INHIBIT_WORD_COMPLETIONS)

    def on_hover(self, hover_point, hover_zone):
        if hover_zone == 1:
            run_future(self.do_hover({
                'position': point_to_position(self.view, hover_point),
                'textDocument': {
                    'uri': get_view_uri(self.view)
                },
            }, hover_point))

    async def do_hover(self, params: HoverParams, hover_point):
        results = []
        if DocumentListener._hover_requests:
            for req in DocumentListener._hover_requests:
                req.cancel()
            DocumentListener._hover_requests = []
        for server in servers_for_view(self.view, capability='hoverProvider'):
            req = server.send.hover(params)
            DocumentListener._hover_requests.append(req)
        try:
            results = await asyncio.gather(*[req.result for req in DocumentListener._hover_requests])
            DocumentListener._hover_requests = []
        except Exception as e:
            print('HoverError:', e)
        try:
            hover_providers = [provider for provider in Providers.hover_providers if is_applicable_view(self.view, provider.activation_events)]
            providers_results = await asyncio.gather(*[provider.provide_hover(self.view, hover_point) for provider in hover_providers])
            results.extend(providers_results)
        except Exception as e:
            print('HoverProvidersError:', e)
        combined_content = []
        for res in results:
            if isinstance(res, dict):
                content = res['contents']
                if content:
                    content = minihtml(self.view, content, FORMAT_MARKED_STRING | FORMAT_MARKUP_CONTENT)
                    combined_content.append(content)
            if combined_content:
                self.view.show_popup(
                    f"""<html style='border: 1px solid color(var(--foreground) blend(var(--background) 20%));'><body><div style='padding: 0.2rem 0.5rem; font-size: 1rem;'>{'<hr style="border: 1px solid color(var(--foreground) blend(var(--background) 20%)); display:block"/>'.join(combined_content)}</div></body></html>""",
                    sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                    hover_point,
                    max_width=800,
                )

