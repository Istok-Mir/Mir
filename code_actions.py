from __future__ import annotations

from .libs.lsp.mir import SourceName

from Mir.types.lsp import CodeActionTriggerKind, CodeAction, Command, CodeActionKind, CodeActionContext
from Mir import mir, apply_workspace_edit, server_for_view
import sublime
import sublime_plugin
import sublime_aio

class CodeActionSelectionListener(sublime_aio.ViewEventListener):
    async def on_selection_modified(self):
        self.view.erase_regions('mir_bulb')
        await self.draw_bulb()
        
    @sublime_aio.debounced(1000)
    async def draw_bulb(self):
        sel = self.view.sel()
        if not sel:
            return []
        self.view.erase_regions('mir_bulb')
        region = sel[0]
        only_kinds=[CodeActionKind.QuickFix]
        if len(region)>1:
            only_kinds.extend([CodeActionKind.Refactor, CodeActionKind.RefactorExtract, CodeActionKind.RefactorInline, CodeActionKind.RefactorMove, CodeActionKind.RefactorRewrite])
        all_code_actions= await get_code_actions(self.view, region, CodeActionTriggerKind.Invoked, only_kinds=only_kinds)
        if not all_code_actions:
            return
        quick_fixes: list[CodeAction] = []
        for _, code_actions in all_code_actions:
            for code_action in code_actions:
                if 'isPreferred' in code_action and code_action.get('isPreferred'):
                    quick_fixes.append(code_action)
        flags =  sublime.RegionFlags.DRAW_NO_FILL | sublime.RegionFlags.DRAW_NO_OUTLINE | sublime.RegionFlags.NO_UNDO
        scope = 'region.bluish' if quick_fixes else 'region.yellowish'
        icon = 'Packages/Mir/icons/lighting-fix.png' if quick_fixes else 'Packages/Mir/icons/lightning.png' 
        self.view.add_regions('mir_bulb', [sublime.Region(region.b)], scope=scope, icon=icon, flags=flags)


class MirCodeActionsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sublime_aio.run_coroutine(self.show_popup())

    async def show_popup(self):
        sel = self.view.sel()
        if not sel:
            return []
        region = sel[0]
        all_code_actions= await get_code_actions(self.view, region, CodeActionTriggerKind.Invoked)
        if not all_code_actions:
            return
        quick_fixes: list[tuple[SourceName, CodeAction]] = []
        code_actions: list[tuple[SourceName, CodeAction|Command]] = []
        for server_name, loop_code_actions in all_code_actions:
            for code_action in loop_code_actions:
                if 'isPreferred' in code_action and code_action.get('isPreferred'):
                    quick_fixes.append((server_name, code_action))
                else:
                    code_actions.append((server_name, code_action))
        items: list[tuple[str, CodeAction|Command, str]] = []
        for code_action in quick_fixes:
            server_name=code_action[0]
            code_action=code_action[1]
            title=code_action['title']
            items.append((title, code_action, server_name))
        for code_action in code_actions:
            server_name=code_action[0]
            code_action=code_action[1]
            title=code_action['title']
            items.append((title, code_action, server_name))

        def on_done(i: int):
            if i < 0:
                return
            sublime_aio.run_coroutine(on_done_async(i))

        async def on_done_async(i: int):
            code_action = items[i][1]
            server_name = items[i][2]
            server = server_for_view(server_name, self.view)
            if server and server.capabilities.has('codeActionProvider.resolveProvider'):
                req =  server.send.resolve_code_action(code_action)
                code_action = await req.result
            command = code_action.get('command')
            if isinstance(command, dict):
                self.view.run_command('mir_execute_command', {
                    'server_name': server_name,
                    'command': command['command'],
                    'arguments': command.get('arguments')
                })
            if isinstance(command, str):
                self.view.run_command('mir_execute_command', {
                    'server_name': server_name,
                    'command': command,
                    'arguments': code_action.get('arguments')
                })
            edit = code_action.get('edit')
            if not edit:
                return
            await apply_workspace_edit(self.view, edit)
        self.view.show_popup_menu([i[0] for i in items], on_done)



def get_point(view: sublime.View):
    sel = view.sel()
    region = sel[0] if sel else None
    if region is None:
        return
    return region.b


async def get_code_actions(view: sublime.View, region: sublime.Region, trigger_kind: CodeActionTriggerKind, only_kinds: list[CodeActionKind] | None=None) -> list[tuple[SourceName, list[Command | CodeAction]]]:
    context: CodeActionContext = {
        'diagnostics': [],
        'triggerKind': trigger_kind
    }
    if only_kinds:
        context['only'] = only_kinds
    result = await mir.code_actions(view, region, context)
    all_code_actions: list[tuple[SourceName, list[Command | CodeAction]]] = []
    for name, code_actions in result:
        if code_actions:
            all_code_actions.append((name, code_actions))
    return all_code_actions
