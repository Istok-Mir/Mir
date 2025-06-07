from __future__ import annotations

from Mir import mir, apply_workspace_edit, server_for_view, servers_for_view, get_view_uri, region_to_range
from .libs.lsp.pull_diagnostics import pull_diagnostics
from Mir.types.lsp import CodeActionOptions, CodeActionTriggerKind
import sublime_aio
import sublime_plugin
import sublime

class MirCompletionListener(sublime_plugin.EventListener):
    def on_pre_save(self, view: sublime.View):
        if MirCodeActionsOnSaveCommand.running_code_actions_on_save:
            return
        view.run_command('mir_code_actions_on_save')


class MirCodeActionsOnSaveCommand(sublime_aio.ViewCommand):
    running_code_actions_on_save = False

    async def run(self):
        MirCodeActionsOnSaveCommand.running_code_actions_on_save = True
        servers = servers_for_view(self.view, 'codeActionProvider')
        view_settings = self.view.settings()
        settings: list[str] = view_settings.get('mir.on_save', [])
        format_with_provider: str | None = None
        for server in servers:
            await pull_diagnostics(server, get_view_uri(self.view))
            code_action_provider: bool | CodeActionOptions = server.capabilities.get('codeActionProvider')
            matching_kinds = []
            for user_setting in settings:
                if user_setting.startswith('format'): # `format.biome` or `format.vtsls`
                    format_with_provider = user_setting.replace('format.', '')
                    continue
                if isinstance(code_action_provider, bool):
                    # This can be tested with the biome LSP
                    # if we uncomment this, biome will return some irrelevant code action fixes to suppress some linter rules, even if the linter is not enabled... which is a bug
                    # matching_kinds.append(user_setting)
                    continue
                else:
                    code_action_kinds = code_action_provider.get('codeActionKinds')
                    if code_action_kinds and user_setting in code_action_kinds:
                        matching_kinds.append(user_setting)
            if not matching_kinds: # don't send code actions if no matching code actions kinds are found
                continue
            diagnostics = await mir.get_diagnostics(self.view, server.name)

            future = server.send.code_action({
                'textDocument': {'uri': get_view_uri(self.view)},
                'range': region_to_range(self.view, sublime.Region(0, self.view.size())),
                'context': {
                    'only': matching_kinds,
                    'diagnostics': diagnostics,
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
                    await apply_workspace_edit(self.view, edit)

        if format_with_provider and (formatting_server := server_for_view(format_with_provider,self.view)) and formatting_server.capabilities.has('documentFormattingProvider'):
            future = formatting_server.send.formatting({
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
            if result:
                self.view.run_command('mir_apply_text_edits', {
                    'text_edits': result
                })

        self.view.run_command('save')
        MirCodeActionsOnSaveCommand.running_code_actions_on_save = False
