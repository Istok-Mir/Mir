from __future__ import annotations
import sublime
from .api import mir
import sublime_aio
from .api.helpers import minihtml, MinihtmlKind


class MirHoverListener(sublime_aio.ViewEventListener):
    async def on_hover(self, hover_point, hover_zone):
        hovers = await mir.hover(self.view, hover_point, hover_zone)
        combined_content: list[str] = []
        for name, hover in hovers:
            if isinstance(hover, dict):
                content = hover['contents']
                content = minihtml(self.view, content, MinihtmlKind.FORMAT_MARKED_STRING | MinihtmlKind.FORMAT_MARKUP_CONTENT)
                combined_content.append(content)
        combined_content = [c for c in combined_content if c]
        if combined_content:
            self.view.show_popup(
                f"""<html style='box-sizing:border-box; background-color:var(--background); padding:0rem; margin:0'><body style='padding:0.3rem; margin:0; border-radius:4px; padding: 0.5rem;border: 1px solid color(var(--foreground) blend(var(--background) 20%));'><div style='padding: 0.0rem 0.2rem; font-size: 0.9rem;'>{'<hr style="border-top: 1px solid color(var(--foreground) blend(var(--background) 20%)); display:block; margin-bottom: 0.5rem"/>'.join(combined_content)}</div></body></html>""",
                sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                hover_point,
                max_width=800,
            )

