from __future__ import annotations
from asyncio import Future
import asyncio

from .libs.lsp.pull_diagnostics import pull_diagnostics

from .libs.lsp.mir import mir

from .libs.lsp.manage_servers import servers_for_view
from .libs.lsp.types import CodeActionOptions, CodeActionTriggerKind, Diagnostic
from .libs.lsp.view_to_lsp import get_view_uri, region_to_range
from .libs.event_loop import run_future
import sublime_plugin
import sublime

class MirCompletionListener(sublime_plugin.EventListener):
    def on_pre_save(self, view: sublime.View):
        if MirCodeActionsOnSaveCommand.running_code_actions_on_save:
            return
        view.run_command('mir_code_actions_on_save')


class MirCodeActionsOnSaveCommand(sublime_plugin.TextCommand):
    running_code_actions_on_save = False

    def run(self, edit: sublime.Edit):
        run_future(self.run_code_actions_on_save())

    async def run_code_actions_on_save(self):
        MirCodeActionsOnSaveCommand.running_code_actions_on_save = True
        diagnostics_results = await mir.get_diagnostics(self.view)
        all_diagnostics: list[Diagnostic] = []
        for _, diagnostics in diagnostics_results:
            all_diagnostics.extend(diagnostics)

        servers = servers_for_view(self.view, 'codeActionProvider')

        view_settings = self.view.settings()
        settings: list[str] = view_settings.get('mir.on_save', [])
        for server in servers:
            await pull_diagnostics(server, get_view_uri(self.view))
            code_action_provider: bool | CodeActionOptions = server.capabilities.get('codeActionProvider')
            matching_kinds = []
            format_with_provider: str | None = None
            for user_setting in settings:
                if user_setting.startswith('format'): # `format.biome` or `format.vtsls`
                    format_with_provider = user_setting.replace('format.', '')
                    continue
                if isinstance(code_action_provider, bool):
                    matching_kinds.append(user_setting)
                else:
                    code_action_kinds = code_action_provider.get('codeActionKinds')
                    if code_action_kinds and user_setting in code_action_kinds:
                        matching_kinds.append(user_setting)
            if format_with_provider == server.name:
                future = server.send.formatting({
                    'textDocument': {'uri': get_view_uri(self.view)},
                    'options': {
                        'tabSize': int(view_settings.get("tab_size", 4)),
                        'insertSpaces': bool(view_settings.get("translate_tabs_to_spaces", False)),
                        'trimTrailingWhitespace': True,
                        'insertFinalNewline': False,
                        'trimFinalNewlines': False
                    }
                })
                result = await future.result
                if not result:
                    continue
                self.view.run_command('mir_apply_text_edits', {
                    'text_edits': result
                })
                continue

            future = server.send.code_action({
                'textDocument': {'uri': get_view_uri(self.view)},
                'range': region_to_range(self.view, sublime.Region(0, self.view.size())),
                'context': {
                    'only': matching_kinds,
                    'diagnostics': all_diagnostics,
                    'triggerKind': CodeActionTriggerKind.Automatic
                }
            })
            # for code action on save we will not do asyncio.gather
            # to prevent servers to return edits that can clash with other servers
            # instead request CodeAction's from one server, apply edits, then request CodeAction's from the other server, apply edits and so on
            result = await future.result
            if not result:
                continue
            for maybe_code_action in result:
                edit = maybe_code_action.get('edit')
                if edit:
                    self.view.run_command('mir_apply_workspace_edit', {
                        'workspace_edit': edit
                    })

        self.view.run_command('save')
        MirCodeActionsOnSaveCommand.running_code_actions_on_save = False
