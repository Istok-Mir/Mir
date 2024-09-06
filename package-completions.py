from __future__ import annotations
import sublime
from .libs.lsp.mir import mir
import sublime_plugin
from .libs.event_loop import run_future
from .libs.lsp.view_to_lsp import open_view_with_uri, range_to_region
from .libs.lsp.minihtml import FORMAT_MARKED_STRING, FORMAT_MARKUP_CONTENT, minihtml


class MirCompletionListener(sublime_plugin.ViewEventListener):
    def on_query_completions(self, _prefix: str, locations: list[Point]):
        completion_list = sublime.CompletionList()
        run_future(self.do_completions(completion_list, locations[0]))
        return completion_list

    async def do_completions(self, completion_list: sublime.CompletionList, point: int):
        completions_results = await mir.completions(self.view, point)
        completions: list[sublime.CompletionValue] = []
        for name, result in completions_results:
            if isinstance(result, dict):
                items = result['items']
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
            elif isinstance(result, list):
                items = result
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
        completion_list.set_completions(completions, sublime.INHIBIT_WORD_COMPLETIONS)





