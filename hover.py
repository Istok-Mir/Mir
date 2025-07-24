from __future__ import annotations
import re
import sublime
from Mir import mir, minihtml, MinihtmlKind
import sublime_aio
import sublime_plugin
import html
from .libs.hover_template import hover_template


class MirHoverListener(sublime_aio.EventListener):
    async def on_hover(self, view, hover_point, hover_zone):
        hovers = await mir.hover(view, hover_point, hover_zone)
        combined_content: list[str] = []
        for name, hover in hovers:
            if isinstance(hover, dict):
                content = hover['contents']
                mir_copy_text = ''
                if isinstance(content, str):
                    mir_copy_text = content
                elif isinstance(content, dict):
                    mir_copy_text = content.get('value', '')
                elif isinstance(content, list):
                    mir_copy_text = " ".join([c for c in content])
                content = minihtml(view, content, MinihtmlKind.FORMAT_MARKED_STRING | MinihtmlKind.FORMAT_MARKUP_CONTENT)
                if content:
                    content = f"""
                    <a title="Click to copy" style='text-decoration: none; display: block; color: var(--foreground)' href='{sublime.command_url('mir_copy_text', {
                        'text': html.unescape(strip_html_tags(mir_copy_text.replace(' ', ' ')))
                    })}'>
                        {content}
                    </a>"""
                combined_content.append(content)
        combined_content = [c for c in combined_content if c]
        if combined_content:
            view.show_popup(
                hover_template(f"""<div class="mir_popup_space_between"></div>""".join(combined_content)),
                sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                hover_point,
                max_width=800,
            )


class MirCopyTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text: str):
        w = self.view.window()
        if w:
            w.status_message('Copied: ' + text[:20] + "...")
        sublime.set_clipboard(text)


def strip_html_tags(html_string) -> str:
    clean_text = re.sub('<[^>]+>', '', html_string)
    return clean_text
