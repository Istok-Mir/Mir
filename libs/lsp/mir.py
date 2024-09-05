from __future__ import annotations
import asyncio
from typing import List

from .lsp_requests import Request
from .manage_servers import servers_for_view
from .types import Definition, DocumentSymbol, SymbolInformation, LocationLink
from .view_to_lsp import get_view_uri, point_to_position
import sublime
from typing import TypeVar, Generic

T = TypeVar('T')
class Result(Generic[T]):
    def __init__(self, name: str, result: T):
        self.server_name= name
        self.result= result

    def __str__(self):
        return str((self.server_name, self.result))

    def __repr__(self):
        return str((self.server_name, self.result))


class mir:
    _definition_requests: List[Request] = []
    _document_symbols_requests: List[Request] = []

    @staticmethod
    async def definitions(view: sublime.View | None) -> list[Result[Definition | list[LocationLink] | None]]:
        if not view:
            return []
        if not view.is_valid():
            return []
        sel = view.sel()
        if not sel:
            return
        point = sel[0].b
        if mir._definition_requests:
            for request in mir._definition_requests:
                request.cancel()
            mir._definition_requests = []
        uri = get_view_uri(view)
        servers = servers_for_view(view, 'definitionProvider')
        results: list[Result[Definition | list[LocationLink] | None]] = []
        for s in servers:
            req = s.send.definition({
                'textDocument': {
                    'uri': uri
                },
                'position': point_to_position(view, point)
            })
            mir._definition_requests.append(req)

        async def handle(req: Request):
            result = await req.result
            return Result(req.server.name, result)

        results = await asyncio.gather(*[handle(future) for future in mir._definition_requests])
        mir._definition_requests = []
        return results

    @staticmethod
    async def document_symbols(view: sublime.View | None) -> list[Result[list[SymbolInformation] | list[DocumentSymbol] | None]]:
        if not view:
            return []
        if not view.is_valid():
            return []
        if mir._document_symbols_requests:
            for request in mir._document_symbols_requests:
                request.cancel()
            mir._document_symbols_requests = []
        uri = get_view_uri(view)
        servers = servers_for_view(view, 'documentSymbolProvider')
        results: list[Result[List[SymbolInformation] | List[DocumentSymbol] | None]] = []
        for s in servers:
            req = s.send.document_symbol({
                'textDocument': {
                    'uri': uri
                },
            })
            mir._document_symbols_requests.append(req)

        async def handle(req: Request):
            result = await req.result
            return Result(req.server.name, result)

        results = await asyncio.gather(*[handle(future) for future in mir._document_symbols_requests])
        mir._document_symbols_requests = []
        return results

