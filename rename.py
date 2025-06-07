from __future__ import annotations
import asyncio
import sublime_aio
from .libs.lsp.workspace_edit import apply_workspace_edit


from .libs.lsp.mir import MAX_WAIT_TIME
from Mir.types.lsp import PrepareRenameResult
from .libs.lsp.server import is_applicable_view # Bad, mir.rename_symbol should exist instead, or something like that
import sublime_aio
import asyncio
from Mir import mir_logger, range_to_region, LanguageServer, point_to_position, get_view_uri, is_range, server_for_view, servers_for_view


class MirRenameCommand(sublime_aio.ViewCommand):
    async def run(self):
        sel = self.view.sel()
        if not sel:
            return
        point = sel[0].b
        # STEP 1:
        servers = [server for server in servers_for_view(self.view, 'renameProvider') if is_applicable_view(self.view, server.activation_events)]
        # STEP 2 define return value
        results: list[tuple[str, PrepareRenameResult | None]] = []
        # STEP 3:
        async def handle(server: LanguageServer):
            try:
                req = server.send.prepare_rename({
                    'textDocument': {'uri': get_view_uri(self.view)},
                    'position': point_to_position(self.view, point)
                })
                result = await asyncio.wait_for(req.result, MAX_WAIT_TIME)
            except Exception as e:
                mir_logger.error(f'Error happened in provider {server.name}', e)
                return (server.name, None)
            return (server.name, result)

        # STEP 4:
        # await all futures and handle them appropriately
        try:
            results = await asyncio.gather(
                *[handle(server) for server in servers],
            )
        except Exception as e:
            mir_logger.error('Mir (Prepare Rename):', e)

        server_name, response = next(iter([(server_name, response) for (server_name, response) in results if response]), ('', None))
        w = self.view.window()
        if not w:
            return
        if not response:
            w.status_message('Mir: Rename not supported at this position')
            return        
        server = server_for_view(server_name, self.view)
        if not server:
            return
        if is_range(response):
            initial_text = self.view.substr(range_to_region(self.view, response))
            def on_done(new_name: str):
                if not new_name.strip():
                    return
                sublime_aio.run_coroutine(self.rename(server, point, new_name))
            v = w.show_input_panel('Mir Rename:', initial_text, on_done, None, None)
            v.run_command('select_all')
        else:
            mir_logger.info('TODO implemet other rename reponses')

    async def rename(self, server: LanguageServer, point: int, new_name: str):
        req = server.send.rename({
            'textDocument': {'uri': get_view_uri(self.view)},
            'position': point_to_position(self.view, point),
            'newName': new_name
        })
        result = await req.result
        if result:
            await apply_workspace_edit(self.view, result)
