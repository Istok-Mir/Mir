from __future__ import annotations
# THIS IS BAD, but this code will not work when there are two event loops
# IMPORTANT, for this to work
# override Sublime Text/Packages/Debugger/modules/core/asyncio.py
# ```diff
# - loop = SublimeEventLoop()
# + import sublime_aio
# + loop = sublime_aio.__loop
# ```


from Mir.types.lsp import Hover
from Mir import HoverProvider
import sublime
try:
    from Debugger.modules.debugger import Debugger
    from Debugger.modules import dap
    from Debugger.modules.views.variable import VariableView
except:
    Debugger = None


class DebugHoverProvider(HoverProvider):
    name= 'Debug Hover Provider'
    activation_events = {
        'selector': '*',
    }
    async def provide_hover(self, view, hover_point, hover_zone) -> Hover | None:
        if Debugger is None:
            return
        if Debugger.ignore(view): return
        debugger = Debugger.get(view)
        if not debugger:
            return
        project = debugger.project
        if hover_zone != sublime.HOVER_TEXT or not project.is_source_file(view):
            return
        if not debugger.session:
            return
        session = debugger.session
        r = session.adapter_configuration.on_hover_provider(view, hover_point)
        if not r:
            return
        word_string, region = r
        value = ''
        try:
            response =await session.evaluate_expression(word_string, 'hover')
            component = VariableView(debugger, dap.Variable(session, '', response.result, response.variablesReference, evaluateName=word_string))
            component.toggle_expand()
            res = await component.variable.session.evaluate_expression(word_string, 'variables')
            value = res.result
        # errors trying to evaluate a hover expression should be ignored
        except dap.Error as e:
            print('ee', e)
            raise Exception('adapter failed hover evaluation', e)
        source_styles: str = 'opacity: 0.4; padding: 0 0.3rem; border-radius: 4px; color: var(--bluish); background-color: color(var(--bluish) alpha(0.1));'
        content = f"""<div><code style='white-space: pre;'><pre style='white-space: pre;'>{value}</pre></code> <span style='{source_styles}'>{session.name}</span></div>"""
        return {
            'contents': [content]
        }
