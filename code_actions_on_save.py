from __future__ import annotations
from asyncio import Future
import asyncio

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

        settings: list[str] = self.view.settings().get('mir.code_actions_on_save', [])
        for server in servers:
            code_action_provider: bool | CodeActionOptions = server.capabilities.get('codeActionProvider')
            matching_kinds = []
            for user_setting in settings:
                if isinstance(code_action_provider, bool):
                    matching_kinds.append(user_setting)
                else:
                    code_action_kinds = code_action_provider.get('codeActionKinds')
                    if code_action_kinds and user_setting in code_action_kinds:
                        matching_kinds.append(user_setting)

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
