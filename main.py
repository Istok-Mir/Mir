from __future__ import annotations
import asyncio
from event_loop import run_future
from lsp.minihtml import FORMAT_MARKED_STRING, FORMAT_MARKUP_CONTENT, minihtml
from lsp.server import LanguageServer
from lsp.types import CompletionParams, HoverParams
from lsp.view_to_lsp import get_view_uri, point_to_position, view_to_text_document_item
import sublime
from html import escape

import sublime_plugin
from sublime_types import Point

all_servers: list[LanguageServer] = []
started_servers: list[LanguageServer] = []

def servers_for_view(view: sublime.View) -> list[LanguageServer]:
    global started_servers
    return [s for s in started_servers if s.is_applicable_view(view)]

async def main():
    global all_servers
    global started_servers
    ts_ls = LanguageServer('typescript-language-server', {
        'cmd':'typescript-language-server --stdio',
        'activation_events': {
            'selector': 'selector:source.js, source.jsx, source.ts, source.tsx'
        }
    })
    all_servers.append(ts_ls)
    pvs_ls = LanguageServer('package-version-server', {
        'cmd': '/Users/predrag/Downloads/package-version-server',
        'activation_events': {
            'selector': 'source.json',
            'on_uri': ['file://**/package.json'],
        }
    })
    all_servers.append(pvs_ls)

    tailwind_ls = LanguageServer('tailwindcss-language-server', {
        'cmd':'tailwindcss-language-server --stdio',
        'activation_events': {
            'selector': 'source.jsx | source.js.react | source.js | source.tsx | source.ts | source.css | source.scss | source.less | text.html.vue | text.html.svelte | text.html.basic | text.html.twig | text.blade | text.html.blade | embedding.php | text.html.rails | text.html.erb | text.haml | text.jinja | text.django | text.html.elixir | source.elixir | text.html.ngx | source.astro',
            'workspace_contains': ['**/tailwind.config.{ts,js,cjs,mjs}'],
        }
    })
    all_servers.append(tailwind_ls)

    # start servers that have selector "*"
    for server in all_servers:
        if server.configuration['activation_events']['selector'] == '*':
            try:
                await server.start()
                started_servers.append(server)
            except Exception as e:
                print(f'Zenit ({server.name}) | Error while starting.', e)

    # notify ls of currenly open views
    views = [v for w in sublime.windows() for v in w.views()]
    for v in views:
        await open_document(v)

def plugin_loaded() -> None:
    run_future(main())

async def open_document(view: sublime.View):
    global all_servers
    global started_servers
    for server in all_servers:
        if not server.is_applicable_view(view):
            continue
        if server not in started_servers:
            try:
                await server.start()
                started_servers.append(server)
            except Exception as e:
                print(f'Zenit ({server.name}) | Error while starting.', e)
                continue
        text_document = view_to_text_document_item(view)
        server.notify.did_open_text_document({
            'textDocument': text_document
        })

def close_document(view: sublime.View):
    global started_servers
    for server in servers_for_view(view):
        server.notify.did_close_text_document({
            'textDocument': {
                'uri': get_view_uri(view)
            }
        })
        if server.matches_activation_event_on_uri(view): # close servers who specify on_uri activation event
            server.stop()
            started_servers = [s for s in started_servers if s != server]


class DocumentListener3(sublime_plugin.EventListener):
    def on_exit(self):
        global started_servers
        for server in started_servers:
            server.stop()

class DocumentListener(sublime_plugin.ViewEventListener):
    def on_load(self):
        run_future(open_document(self.view))

    def on_close(self):
       close_document(self.view)

    def on_query_completions(self, _prefix: str, locations: list[Point]):
        completion_list = sublime.CompletionList()
        params: CompletionParams = {
            'position': point_to_position(self.view, locations[0]),
            'textDocument': {
                'uri': get_view_uri(self.view)
            }
        }
        run_future(self.do_completions(completion_list, params))
        return completion_list

    def on_hover(self, point, hover_zone):
        if hover_zone == 1:
            run_future(self.do_hover({
                'position': point_to_position(self.view, point),
                'textDocument': {
                    'uri': get_view_uri(self.view)
                },
            }, point))

    async def do_hover(self, params: HoverParams, hover_point):
        results = []
        try:
            results = await asyncio.gather(*[server.send.hover(params) for server in servers_for_view(self.view) if server.capabilities.has('hoverProvider')])
        except Exception as e:
            print('HoverError:', e)
        combined_content = []
        for res in results:
            if isinstance(res, dict):
                content = res['contents']
                if content:
                    content = minihtml(self.view, content, FORMAT_MARKED_STRING | FORMAT_MARKUP_CONTENT)
                    print('content', content)
                    combined_content.append(content)
            if combined_content:
                print('ovdeee')
                self.view.show_popup(
                    f"<html style='border: 1px solid color(var(--foreground) blend(var(--background) 20%));'><body><div style='padding: 0.2rem 0.5rem; font-size: 1rem;'>{'<hr>'.join(combined_content)}</div></body></html>",
                    sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                    hover_point,
                    max_width=800,
                )

    async def do_completions(self, completion_list: sublime.CompletionList, params: CompletionParams):
        completions: list[sublime.CompletionValue] = []
        for server in servers_for_view(self.view):
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
