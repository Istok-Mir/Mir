from __future__ import annotations

from .libs.lsp.providers import Providers

from .libs.lsp.constants import COMPLETION_KINDS
import sublime
import sublime_plugin
from .api import mir, run_future
from .api.helpers import range_to_region
from .api.types import CompletionItem, CompletionItemDefaults, TextEdit, InsertReplaceEdit, EditRangeWithInsertReplace, Range, InsertTextFormat
from typing import Any, Generator, List, Tuple, TypeVar
from typing import cast
from typing_extensions import TypeAlias, TypeGuard
from .api.helpers import minihtml, MinihtmlKind
import cProfile
import pstats


CompletionsStore: TypeAlias = Tuple[List[CompletionItem], CompletionItemDefaults]

T = TypeVar('T')

def get_chunked(items: list[T]) -> Generator[T]:
    for item in items:
        yield item


class MirCompletionListener(sublime_plugin.ViewEventListener):
    completions: dict[str, CompletionsStore] = {}
    def on_query_completions(self, prefix: str, locations: list[int]):
        completion_list = sublime.CompletionList()
        run_future(self.do_completions(completion_list, locations, prefix))
        return completion_list

    async def do_completions(self, completion_list: sublime.CompletionList, locations: list[int], prefix: str):
        completions_results = await mir.completions(self.view, prefix, locations)
        completions: list[sublime.CompletionValue] = []
        items: list[CompletionItem] = []
        item_defaults : CompletionItemDefaults = {}
        for name, result in completions_results:
            if isinstance(result, dict):
                items = result['items']
                completions.extend([format_completion(c, name, index) for index, c in enumerate(get_chunked(items))])
            elif isinstance(result, list):
                items = result
                completions.extend([format_completion(c, name, index) for index, c in enumerate(get_chunked(items))])
            MirCompletionListener.completions[name] = items, item_defaults
        completion_list.set_completions(completions, flags=sublime.AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS | sublime.AutoCompleteFlags.INHIBIT_EXPLICIT_COMPLETIONS )


def format_completion(i: CompletionItem, provider_name: str, index: int):
    label_details_description = i.get('labelDetails', {}).get('description') or ""
    completion_item_kind = i.get('kind')
    kind = COMPLETION_KINDS[completion_item_kind] if completion_item_kind else sublime.KIND_AMBIGUOUS
    ci = sublime.CompletionItem(i['label'], label_details_description, 
         f'mir_insert_completion {{"index":{index},"provider":"{provider_name}"}}', sublime.CompletionFormat.COMMAND, kind=kind)
    if 'textEdit' in i:
        ci.flags = sublime.COMPLETION_FLAG_KEEP_PREFIX
    return ci


class MirInsertCompletion(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, index: int, provider: str) -> None:
        items, item_defaults = MirCompletionListener.completions[provider]
        item = completion_with_defaults(items[index], item_defaults)
        text_edit = item.get("textEdit")
        if text_edit:
            new_text = text_edit["newText"].replace("\r", "")
            edit_region = range_to_region(self.view, get_text_edit_range(text_edit))
            for region in self._translated_regions(edit_region):
                self.view.erase(edit, region)
        else:
            new_text = item.get("insertText") or item["label"]
            new_text = new_text.replace("\r", "")
        if item.get("insertTextFormat", InsertTextFormat.PlainText) == InsertTextFormat.Snippet:
            self.view.run_command("insert_snippet", {"contents": new_text})
        else:
            self.view.run_command("insert", {"characters": new_text})
        resolve_completion_provider = next(iter([p for p in Providers.completion_providers if p.name == provider]), None)
        if not resolve_completion_provider:
            return

        async def resolve():
            resolved_item = await resolve_completion_provider.resolve_completion_item(item)
            self._on_resolved(provider, resolved_item)

        run_future(resolve())

    def _on_resolved(self, server_name: str, item: CompletionItem) -> None:
        additional_edits = item.get('additionalTextEdits')
        if additional_edits:
            self.view.run_command('mir_apply_text_edits', {
                'text_edits': additional_edits
            })
        command = item.get("command")
        if command:
            self.view.run_command('mir_execute_command', {
                'server_name': server_name,
                'command': command['command'],
                'arguments': command.get('arguments')
            })
        

    def _translated_regions(self, edit_region: sublime.Region) -> Generator[sublime.Region, None, None]:
        selection = self.view.sel()
        primary_cursor_position = selection[0].b
        for region in reversed(selection):
            # For each selection region, apply the same removal as for the "primary" region.
            # To do that, translate, or offset, the LSP edit region into the non-"primary" regions.
            # The concept of "primary" is our own, and there is no mention of it in the LSP spec.
            translation = region.b - primary_cursor_position
            translated_edit_region = sublime.Region(edit_region.a + translation, edit_region.b + translation)
            yield translated_edit_region


def completion_with_defaults(item: CompletionItem, item_defaults: CompletionItemDefaults) -> CompletionItem:
    """ Currently supports defaults for: ["editRange", "insertTextFormat", "data"] """
    if not item_defaults:
        return item
    default_text_edit: TextEdit | InsertReplaceEdit | None = None
    edit_range = item_defaults.get('editRange')
    if edit_range:
        #  If textEditText is not provided and a list's default range is provided
        # the label property is used as a text.
        new_text = item.get('textEditText') or item['label']
        if is_edit_range(edit_range):
            default_text_edit = {
                'newText': new_text,
                'insert': edit_range.get('insert'),
                'replace': edit_range.get('insert'),
            }
        elif is_range(edit_range):
            default_text_edit = {
                'newText': new_text,
                'range': edit_range
            }
    if default_text_edit and 'textEdit' not in item:
        item['textEdit'] = default_text_edit
    default_insert_text_format = item_defaults.get('insertTextFormat')
    if default_insert_text_format and 'insertTextFormat' not in item:
        item['insertTextFormat'] = default_insert_text_format
    default_data = item_defaults.get('data')
    if default_data and 'data' not in item:
        item['data'] = default_data
    return item


def is_range(val: Any) -> TypeGuard[Range]:
    return isinstance(val, dict) and 'start' in val and 'end' in val


def is_edit_range(val: Any) -> TypeGuard[EditRangeWithInsertReplace]:
    return isinstance(val, dict) and 'insert' in val and 'replace' in val


def get_text_edit_range(text_edit: TextEdit | InsertReplaceEdit) -> Range:
    if 'insert' in text_edit and 'replace' in text_edit:
        text_edit = cast(InsertReplaceEdit, text_edit)
        # insert_mode = 'replace' if insert_mode == 'insert' else 'insert'
        insert_mode = 'insert'
        return text_edit.get(insert_mode)  # type: ignore
    text_edit = cast(TextEdit, text_edit)
    return text_edit['range']

class MirApplyTextEditsCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, text_edits: list[TextEdit]) -> None:
        if not text_edits:
            return
        content = []
        for text_edit in text_edits:
            self.view.replace(edit, range_to_region(self.view, text_edit['range']), text_edit['newText'])
            content.append(f"+ {text_edit['newText']}")
        content = f"""```diff
{" ".join(content)}
```"""
        formatted_content = content = minihtml(self.view, content, MinihtmlKind.FORMAT_MARKED_STRING | MinihtmlKind.FORMAT_MARKUP_CONTENT)


        self.view.show_popup(
            f"""<html style='box-sizing:border-box; background-color:var(--background); padding:0rem; margin:0'><body style='padding:0.3rem; margin:0; border-radius:4px; border: 1px solid color(var(--foreground) blend(var(--background) 20%));'><div style='padding: 0.0rem 0.2rem; font-size: 0.9rem;'>{formatted_content}</div></body></html>""",
            sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
            max_width=800,
        )
        sublime.set_timeout(lambda: self.view.hide_popup(), 2000)
