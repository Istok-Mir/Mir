from __future__ import annotations
from .libs.lsp.server import LanguageServer
import sublime
import sublime_plugin
from .api import mir, run_future
from .api.helpers import position_to_point, range_to_region, server_for_view
from .api.types import CompletionItem, CompletionItemDefaults, TextEdit, InsertReplaceEdit, EditRangeWithInsertReplace, Range, InsertTextFormat
from typing import Any, Callable, Generator, List, Tuple, Union
from typing import cast
from typing_extensions import TypeAlias, TypeGuard
import functools
from .api.helpers import minihtml, MinihtmlKind


CompletionsStore: TypeAlias = Tuple[List[CompletionItem], CompletionItemDefaults]


class MirCompletionListener(sublime_plugin.ViewEventListener):
    completions: dict[str, CompletionsStore] = {}
    def on_query_completions(self, prefix: str, locations: list[int]):
        completion_list = sublime.CompletionList()
        run_future(self.do_completions(completion_list, locations[0], prefix))
        return completion_list

    async def do_completions(self, completion_list: sublime.CompletionList, point: int, prefix: str):
        completions_results = await mir.completions(self.view, point)
        completions: list[sublime.CompletionValue] = []
        first_letter = prefix[:1]
        items: list[CompletionItem] = []
        item_defaults : CompletionItemDefaults = {}
        for name, result in completions_results:
            if isinstance(result, dict):
                items = result['items']
                for index, i in enumerate(items):
                    # if first_letter and not i['label'].startswith(first_letter):
                    #     continue
                    label_details_description = i.get('labelDetails', {}).get('description') or ""
                    ci = sublime.CompletionItem.command_completion(i['label'], 'mir_insert_completion', {
                        'index': index,
                        'provider': name,
                    }, annotation=label_details_description)
                    if 'textEdit' in i:
                        ci.flags = sublime.COMPLETION_FLAG_KEEP_PREFIX
                    completions.append(ci)
            elif isinstance(result, list):
                items = result
                for index, i in enumerate(items):
                    label_details_description = i.get('labelDetails', {}).get('description') or ""
                    ci = sublime.CompletionItem.command_completion(i['label'], 'mir_insert_completion',{
                        'index': index,
                        'provider': name,
                    }, annotation=label_details_description)
                    if 'textEdit' in i:
                        ci.flags = sublime.COMPLETION_FLAG_KEEP_PREFIX
                    completions.append(ci)
            MirCompletionListener.completions[name] = items, item_defaults
        completion_list.set_completions(completions, sublime.INHIBIT_WORD_COMPLETIONS)

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
        # todo: this should all run from the worker thread
        server = server_for_view(provider, self.view)
        if not server or not server.capabilities.has('completionProvider.resolveProvider'):
            return
        additional_text_edits = item.get('additionalTextEdits')
        if not additional_text_edits:
            run_future(self.resolve_item(server, item))
        else:
            self._on_resolved(provider, item)

    async def resolve_item(self, server: LanguageServer, item: CompletionItem):
        req = server.send.resolve_completion_item(item)
        result = await req.result
        self._on_resolved(server.name, result)

    def _on_resolved_async(self, session_name: str, item: CompletionItem) -> None:
        sublime.set_timeout(functools.partial(self._on_resolved, session_name, item))

    def _on_resolved(self, session_name: str, item: CompletionItem) -> None:
        additional_edits = item.get('additionalTextEdits')
        if additional_edits:
            self.view.run_command('mir_apply_text_edits', {
                'text_edits': additional_edits
            })
        command = item.get("command")
        if command:
            args = {
                "command_name": command["command"],
                "command_args": command.get("arguments"),
                "session_name": session_name
            }
            print('TODO implement lsp_execute')
            # self.view.run_command("lsp_execute", args)
        

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
        insert_mode = 'replace'
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
