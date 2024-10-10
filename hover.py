from __future__ import annotations
import sublime
import sublime_plugin
from .api import mir, run_future
from .api.helpers import minihtml, MinihtmlKind


class MirHoverListener(sublime_plugin.ViewEventListener):
    def on_hover(self, hover_point, hover_zone):
        run_future(self.do_hover(hover_point, hover_zone))

    async def do_hover(self, hover_point: int, hover_zone: sublime.HoverZone):
        hovers = await mir.hover(self.view, hover_point, hover_zone)
        combined_content: list[str] = []
        for name, hover in hovers:
            if isinstance(hover, dict):
                content = hover['contents']
                if content:
                    content = minihtml(self.view, content, MinihtmlKind.FORMAT_MARKED_STRING | MinihtmlKind.FORMAT_MARKUP_CONTENT)
                    combined_content.append(content)
            if combined_content:
                self.view.show_popup(
                    f"""<html style='box-sizing:border-box; background-color:var(--background); padding:0rem; margin:0'><body style='padding:0.3rem; margin:0; border-radius:4px; border: 1px solid color(var(--foreground) blend(var(--background) 20%));'><div style='padding: 0.0rem 0.2rem; font-size: 0.9rem;'>{'<hr style="border-top: 1px solid color(var(--foreground) blend(var(--background) 20%)); display:block"/>'.join(combined_content)}</div></body></html>""",
                    sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                    hover_point,
                    max_width=800,
                )

