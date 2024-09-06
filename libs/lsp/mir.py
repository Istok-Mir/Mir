from __future__ import annotations
import asyncio
from typing import List

from .lsp_requests import Request
from .manage_servers import servers_for_view
from .providers import Providers
from .server import is_applicable_view
from .types import Definition, DocumentSymbol, SymbolInformation, LocationLink, Hover
from .view_to_lsp import get_view_uri, point_to_position
import sublime
from typing import TypeVar, Generic

SourceName = str

class mir:
    _definition_requests: List[Request] = []
    _hover_requests: List[Request] = []
    _document_symbols_requests: List[Request] = []

    @staticmethod
    async def definitions(view: sublime.View | None) -> list[tuple[SourceName, Definition | list[LocationLink] | None]]:
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
        results: list[tuple[SourceName, Definition | list[LocationLink] | None]] = []
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
            return (req.server.name, result)

        results = await asyncio.gather(*[handle(future) for future in mir._definition_requests])
        mir._definition_requests = []
        return results

    @staticmethod
    async def hover(view: sublime.View | None, hover_point: int) -> list[tuple[SourceName, Hover | None]]:
        if not view:
            return []
        if not view.is_valid():
            return []
        if mir._hover_requests:
            for request in mir._hover_requests:
                request.cancel()
            mir._hover_requests = []
        uri = get_view_uri(view)
        servers = servers_for_view(view, 'hoverProvider')
        results: list[tuple[SourceName, Hover | None]] = []
        for s in servers:
            req = s.send.hover({
                'textDocument': {
                    'uri': uri
                },
                'position': point_to_position(view, hover_point)
            })
            mir._hover_requests.append(req)

        async def handle(req: Request):
            result = await req.result
            return (req.server.name, result)

        results = await asyncio.gather(*[handle(future) for future in mir._hover_requests])

        async def handle_provider(provider: HoverProvider):
            result = await req.provide_hover(view, hover_point)
            return (provider.name, result)

        hover_providers = [provider for provider in Providers.hover_providers if is_applicable_view(view, provider.activation_events)]
        providers_results = await asyncio.gather(*[handle_provider(provider) for provider in hover_providers])
        results.extend(providers_results)

        mir._hover_requests = []
        return results

    @staticmethod
    async def document_symbols(view: sublime.View | None) -> list[tuple[SourceName, list[SymbolInformation] | list[DocumentSymbol] | None]]:
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
        results: list[tuple[SourceName, List[SymbolInformation] | List[DocumentSymbol] | None]] = []
        for s in servers:
            req = s.send.document_symbol({
                'textDocument': {
                    'uri': uri
                },
            })
            mir._document_symbols_requests.append(req)

        async def handle(req: Request):
            result = await req.result
            return (req.server.name, result)

        results = await asyncio.gather(*[handle(future) for future in mir._document_symbols_requests])
        mir._document_symbols_requests = []
        return results

