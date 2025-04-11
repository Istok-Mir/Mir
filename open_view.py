from __future__ import annotations
import asyncio
import sublime_aio
import sublime

open_view_futures_map: dict[str, asyncio.Future[sublime.View]] = {}
on_save_futures_map: dict[str, asyncio.Future] = {}


class EventListener(sublime_aio.EventListener):
    async def on_load(self, view):
        file_name = view.file_name() or ""
        if file_name not in open_view_futures_map:
            return
        future = open_view_futures_map.pop(file_name)
        if future:
            future.set_result(view)

    def on_post_save(self, view):
        file_name = view.file_name() or ""
        if file_name not in on_save_futures_map:
            return
        future = on_save_futures_map.pop(file_name)
        if future:
            future.set_result(None)

async def save_view(view: sublime.View) -> None:
    file_name = view.file_name() or ""
    if not file_name:
        view.run_command('save')
        return
    future: asyncio.Future = asyncio.Future()
    on_save_futures_map[file_name] = future
    view.run_command('save')
    await future


async def open_view(file_name, window: sublime.Window, flags: sublime.NewFileFlags=sublime.NewFileFlags.NONE) -> sublime.View:
    future: asyncio.Future[sublime.View] = asyncio.Future()
    open_view_futures_map[file_name] = future
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


