from __future__ import annotations
import sublime
from .libs.lsp.mir import mir
import sublime_plugin
from .libs.event_loop import run_future
from .libs.lsp.view_to_lsp import open_view_with_uri, range_to_region
from .libs.lsp.minihtml import FORMAT_MARKED_STRING, FORMAT_MARKUP_CONTENT, minihtml


class MirHoverListener(sublime_plugin.ViewEventListener):
    def on_hover(self, hover_point, hover_zone):
        if hover_zone == 1:
            run_future(self.do_hover(hover_point))

    async def do_hover(self, hover_point: int):
        hovers = await mir.hover(self.view, hover_point)
        window = self.view.window()
        if not window:
            return
        combined_content: list[str] = []
        for name, hover in hovers:
            if isinstance(hover, dict):
                content = hover['contents']
                if content:
                    content = minihtml(self.view, content, FORMAT_MARKED_STRING | FORMAT_MARKUP_CONTENT)
                    combined_content.append(content)
            if combined_content:
                self.view.show_popup(
                    f"""<html style='border: 1px solid color(var(--foreground) blend(var(--background) 20%));'><body><div style='padding: 0.0rem 0.2rem; font-size: 0.9rem;'>{'<hr style="border: 1px solid color(var(--foreground) blend(var(--background) 20%)); display:block"/>'.join(combined_content)}</div></body></html>""",
                    sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                    hover_point,
                    max_width=800,
                )


        for name, defintion in definitions:
            if isinstance(defintion, list):
                for d in defintion:
                    if 'targetUri' in d:
                        open_view_with_uri(d['targetUri'], d['targetSelectionRange'], window)
                    else:
                        open_view_with_uri(d['uri'], d['range'], window)
                    return
            if isinstance(defintion, dict):
                open_view_with_uri(defintion['uri'], defintion['range'], window)
                return


