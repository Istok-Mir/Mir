from __future__ import annotations
import asyncio
import os
from re import sub
import re

from event_loop import run_future
from lsp.server import LanguageServer
from lsp.types import CompletionParams, HoverParams
from lsp.view_to_lsp import get_view_uri, view_to_text_document_item
import sublime
from html import escape

import sublime_plugin
from sublime_types import Point

servers: list[LanguageServer] = []

async def main():
    global servers
    ts_ls = LanguageServer('typescript-language-server', cmd='typescript-language-server --stdio')
    await ts_ls.start()
    servers.append(ts_ls)
    tailwind_ls = LanguageServer('tailwindcss-language-server', cmd='tailwindcss-language-server --stdio')
    await tailwind_ls.start()
    servers.append(tailwind_ls)

    # notify ls of currenly open views
    views = sublime.active_window().views()
    for v in views:
        open_document(v)

def plugin_loaded() -> None:
    run_future(main())

def open_document(view: sublime.View):
    file_name = view.file_name()
    if not file_name:
        return
    for server in servers:
        text_document = view_to_text_document_item(view)
        server.notify.did_open_text_document({
            'textDocument': text_document
        })

class DocumentListener3(sublime_plugin.EventListener):
    def on_exit(self):
        global servers
        for server in servers:
            server.stop()

class DocumentListener(sublime_plugin.ViewEventListener):
    def on_load(self):
        open_document(self.view)

    def on_close(self):
        uri = get_view_uri(self.view)
        if not uri:
            return
        for server in servers:
            server.notify.did_close_text_document({
                'textDocument': {
                    'uri': uri
                }
            })

    def on_query_completions(self, _prefix: str, locations: list[Point]):
        completion_list = sublime.CompletionList()
        file_name = self.view.file_name()
        if not file_name:
            return
        row, col = self.view.rowcol(locations[0])
        params: CompletionParams = {
            'position': {'line': row, 'character': col},
            'textDocument': {
                'uri': 'file://' + file_name
            }
        }
        run_future(self.do_completions(completion_list, params))
        return completion_list

    def on_hover(self, point, hover_zone):
        if hover_zone == 1:
            file_name = self.view.file_name()
            if not file_name:
                return
            row, col = self.view.rowcol(point)
            run_future(self.do_hover({
                'position': { 'line': row,'character': col },
                'textDocument': {
                    'uri': 'file://' + file_name
                },
            }, point))

    async def do_hover(self, params: HoverParams, hover_point):
        for server in servers:
            res = None
            try:
                res = await server.send.hover(params)
            except Exception as e:
                print('HoverError:', e)
            if isinstance(res, dict):
                content = res['contents']
                if isinstance(content, dict) and 'value' in content:
                    self.view.show_popup(
                        "<pre style='white-space: pre-wrap'>"+escape(content['value']).replace('\n', '<br>')+"</pre>",
                        sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                        hover_point,
                        max_width=1200,
                    )

    async def do_completions(self, completion_list: sublime.CompletionList, params: CompletionParams):
        completions: list[sublime.CompletionValue] = []
        for server in servers:
            if not server.capabilities.has('completionProvider'):
                continue
            server.notify.did_change_text_document({
                'textDocument': {
                    'uri': params['textDocument']['uri'],
                    'version': self.view.change_count()
                },
                'contentChanges': [{
                    'text': self.view.substr(sublime.Region(0, self.view.size()))
                }]
            })
            res=None
            try:
                res = await server.send.completion(params)
            except Exception as e:
                print('CompletionError:', e)
            if isinstance(res, dict):
                items = res['items']
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
        completion_list.set_completions(completions, sublime.INHIBIT_WORD_COMPLETIONS)
