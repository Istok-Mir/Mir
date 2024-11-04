from __future__ import annotations
from typing import Literal


from .api.types import CodeActionTriggerKind, Diagnostic, CodeAction, Command, CodeActionKind
from .api import mir
from .libs.event_loop import run_future
import sublime
import sublime_plugin

class CodeActionSelectionListener(sublime_plugin.ViewEventListener):
    def on_selection_modified(self):
        sel = self.view.sel()
        if not sel:
            return
        region = sel[0].to_tuple()
        self.view.erase_regions('mir_bulb')
        sublime.set_timeout(lambda: self.debounce(region), 1000)

    def debounce(self, region: tuple[int, int]):
        new_sel = self.view.sel()
        if not new_sel:
            return
        if region == new_sel[0].to_tuple():
            run_future(self.draw_bulb())

    async def draw_bulb(self):
        sel = self.view.sel()
        if not sel:
            return []
        self.view.erase_regions('mir_bulb')
        region = sel[0]
        all_code_actions= await get_code_actions(self.view, region)
        if not all_code_actions:
            return
        quick_fixes: list[CodeAction] = []
        # for code_action in all_code_actions:
        #     if 'isPreferred' in code_action and code_action.get('isPreferred'):
        #         quick_fixes.append(code_action)
        flags =  sublime.RegionFlags.DRAW_NO_FILL | sublime.RegionFlags.DRAW_NO_OUTLINE | sublime.RegionFlags.NO_UNDO
        scope = 'region.bluish' if quick_fixes else 'region.yellowish'
        icon = 'Packages/Mir/icons/ligthing-fix.png' if quick_fixes else 'Packages/Mir/icons/lightning.png' 
        self.view.add_regions('mir_bulb', [sublime.Region(region.b)], scope=scope, icon=icon, flags=flags)


class MirCodeActionsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        run_future(self.show_popup())

    async def show_popup(self):
        sel = self.view.sel()
        if not sel:
            return []
        region = sel[0]
        all_code_actions= await get_code_actions(self.view, region)
        if not all_code_actions:
            return
        quick_fixes: list[CodeAction] = []
        code_actions: list[CodeAction|Command] = []
        for code_action in all_code_actions:
            if 'isPreferred' in code_action and code_action.get('isPreferred'):
                quick_fixes.append(code_action)
            else:
                code_actions.append(code_action)
        items: list[tuple[str, CodeAction|Command]] = []
        for qf in quick_fixes:
            items.append((qf['title'], qf))
        for ca in code_actions:
            items.append((ca['title'], ca))

        def on_done(i: int):
            if i < 0:
                return
            code_action = items[i][1]
            if 'command' in code_action:
                print('TODO Mir doesnt support command yet')
                return
            edit = code_action.get('edit')
            if not edit:
                return
            self.view.run_command('mir_apply_workspace_edit', {
                'workspace_edit': edit
            })
            print('selected', items[i])
        self.view.show_popup_menu([i[0] for i in items], on_done)



def get_point(view: sublime.View):
    sel = view.sel()
    region = sel[0] if sel else None
    if region is None:
        return
    return region.b


async def get_code_actions(view: sublime.View, region: sublime.Region) -> list[Command | CodeAction]:
    # get diagnostics
    diagnostics_results = await mir.get_diagnostics(view)
    all_diagnostics: list[Diagnostic] = []
    for _, diagnostics in diagnostics_results:
        all_diagnostics.extend(diagnostics)
    result = await mir.code_actions(view, region, {
        'diagnostics': all_diagnostics,
        'only': [CodeActionKind.QuickFix],
        'triggerKind': CodeActionTriggerKind.Automatic
    })
    all_code_actions: list[Command | CodeAction] = []
    for _, code_actions in result:
        if code_actions:
            all_code_actions.extend(code_actions)
    return all_code_actions
