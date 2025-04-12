from __future__ import annotations
import asyncio
from .libs.lsp.future_with_id import FutureWithId
import sublime_aio
import sublime


class MirOpenViewListener(sublime_aio.EventListener):
    async def on_load(self, view):
        file_name = view.file_name() or ""
        future = FutureWithId.get(f"open:{file_name}")
        if future:
            future.set_result(view)

    def on_post_save(self, view):
        file_name = view.file_name() or ""
        future = FutureWithId.get(f"save:{file_name}")
        if future:
            future.set_result(None)

async def save_view(view: sublime.View) -> None:
    file_name = view.file_name() or ""
    if not file_name:
        view.run_command('save')
        return
    future: asyncio.Future = FutureWithId(f'save:{file_name}')
    view.run_command('save')
    await future


async def open_view(file_name, window: sublime.Window, flags: sublime.NewFileFlags=sublime.NewFileFlags.NONE) -> sublime.View:
    future: asyncio.Future = FutureWithId(f'open:{file_name}')
    active_view = window.active_view()
    view = window.find_open_file(file_name)
    if view:
        future.set_result(view)
    else:
        window.open_file(file_name, flags=flags)
    res = await future
    if active_view:
        window.focus_view(active_view)
    return res


