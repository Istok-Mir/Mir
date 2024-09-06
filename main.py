from __future__ import annotations
from .libs.event_loop import run_future
from .libs.lsp.lsp_requests import Request
from .libs.lsp.manage_servers import ManageServers, servers_for_view
from .libs.lsp.providers import Providers
from .libs.lsp.minihtml import FORMAT_MARKED_STRING, FORMAT_MARKUP_CONTENT, minihtml
from .libs.lsp.server import LanguageServer, is_applicable_view
from .libs.lsp.types import CompletionParams, HoverParams
from .libs.lsp.view_to_lsp import get_view_uri, point_to_position
from sublime_types import Point
import asyncio
import sublime
import sublime_plugin
from .libs.lsp.text_change_listener import TextChangeListener


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
