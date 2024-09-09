from __future__ import annotations
import asyncio
from typing import List

from .lsp_requests import Request
from .manage_servers import servers_for_view
from .providers import Providers, HoverProvider, CompletionProvider, DefinitionProvider, DocumentSymbolProvider
from .server import is_applicable_view
from .types import Definition, DocumentSymbol, SymbolInformation, LocationLink, Hover, CompletionItem, CompletionList, DocumentUri, Diagnostic
from .view_to_lsp import get_view_uri, point_to_position
import sublime
from typing import TypeVar, Generic

SourceName = str
""" The language server name or the provider name """

class mir:
    _definition_requests: List[Request] = []
    @staticmethod
    async def definitions(view: sublime.View, point: int) -> list[tuple[SourceName, Definition | list[LocationLink] | None]]:
        # STEP 1:
        # - Cancel LSP Requests
        # - Cancel Providers
        if mir._definition_requests:
            for request in mir._definition_requests:
                request.cancel()
            mir._definition_requests = []
        providers = [provider for provider in Providers.definition_providers if is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, Definition | list[LocationLink] | None]] = []

        # STEP 3:
        # Send completion requests to LSP, but don't await them
        servers = servers_for_view(view, 'definitionProvider')
        uri = get_view_uri(view)
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

        async def handle_provider(provider: DefinitionProvider):
            try:
                result = await provider.provide_definition(view, point)
            except Exception as e:
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        try:
            results = await asyncio.gather(
                *[handle(future) for future in mir._definition_requests],
                *[handle_provider(provider) for provider in providers]
            )
        except Exception as e:
            print('Mir (DefinitionError):', e)
        mir._definition_requests = []
        return results

    _hover_requests: List[Request] = []
    @staticmethod
    async def hover(view: sublime.View, hover_point: int) -> list[tuple[SourceName, Hover | None]]:
        # Step 0
        # Return empty results if things are not valid
        if not view:
            return []
        if not view.is_valid():
            return []
        # STEP 1:
        # - Cancel LSP Requests
        # - Cancel Providers

        # Cancel LSP Requests
        if mir._hover_requests:
            for request in mir._hover_requests:
                request.cancel()
            mir._hover_requests = []
        # Trigger Canceling Providers
        providers = [provider for provider in Providers.hover_providers if is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, Hover | None]] = []

        # STEP 3:
        # Send completion requests to LSP, but don't await them
        servers = servers_for_view(view, 'hoverProvider')
        uri = get_view_uri(view)
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

        async def handle_provider(provider: HoverProvider):
            try:
                result = await provider.provide_hover(view, hover_point)
            except Exception as e:
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        # STEP 4:
        # await all futures and handle them appropriately
        try:
            results = await asyncio.gather(
                *[handle(future) for future in mir._hover_requests],
                *[handle_provider(provider) for provider in providers]
            )
        except Exception as e:
            print('Mir (HoverError):', e)
        mir._hover_requests = []
        return results


    _completion_requests: List[Request] = []
    @staticmethod
    async def completions(view: sublime.View, point=int) -> list[tuple[SourceName, list[CompletionItem] | CompletionList | None]]:
        # STEP 1:
        # - Cancel LSP Requests
        # - Cancel Providers

        # Cancel LSP Requests
        if mir._completion_requests:
            for request in mir._completion_requests:
                request.cancel()
            mir._completion_requests = []
        # Trigger Canceling Providers
        providers = [provider for provider in Providers.completion_providers if is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, list[CompletionItem] | CompletionList | None]] = []

        # STEP 3:
        # Send completion requests to LSP, but don't await them
        servers = servers_for_view(view, 'completionProvider')
        uri = get_view_uri(view)
        for s in servers:
            req = s.send.completion({
                'textDocument': {
                    'uri': uri
                },
                'position': point_to_position(view, point)
            })
            mir._completion_requests.append(req)

        async def handle(req: Request):
            result = await req.result
            return (req.server.name, result)

        async def handle_provider(provider: CompletionProvider):
            try:
                result = await provider.provide_completion_items(view, point)
            except Exception as e:
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        # STEP 4:
        # await all futures and handle them appropriately
        try:
            results = await asyncio.gather(
                *[handle(future) for future in mir._completion_requests],
                *[handle_provider(provider) for provider in providers]
            )
        except Exception as e:
            print('Mir (CompletionError):', e)
        mir._completion_requests = []
        return results

    _document_symbols_requests: List[Request] = []
    @staticmethod
    async def document_symbols(view: sublime.View) -> list[tuple[SourceName, list[SymbolInformation] | list[DocumentSymbol] | None]]:
        # STEP 1:
        # - Cancel LSP Requests
        # - Cancel Providers
        if mir._document_symbols_requests:
            for request in mir._document_symbols_requests:
                request.cancel()
            mir._document_symbols_requests = []
        providers = [provider for provider in Providers.document_symbols_providers if is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, List[SymbolInformation] | List[DocumentSymbol] | None]] = []

        # STEP 3:
        # Send completion requests to LSP, but don't await them
        servers = servers_for_view(view, 'documentSymbolProvider')
        uri = get_view_uri(view)
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

        async def handle_provider(provider: DocumentSymbolProvider):
            try:
                result = await provider.provide_document_symbol(view)
            except Exception as e:
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        # STEP 4:
        # await all futures and handle them appropriately
        try:
            results = await asyncio.gather(
                *[handle(future) for future in mir._document_symbols_requests],
                *[handle_provider(provider) for provider in providers]
            )
        except Exception as e:
            print('Mir (DocumentSymbolError):', e)
        mir._document_symbols_requests = []
        return results

    @staticmethod
    def get_diagnostics(view_or_window: sublime.View | sublime.Window) -> list[tuple[DocumentUri, list[Diagnostic]]]:
        result: list[tuple[DocumentUri, list[Diagnostic]]] = []
        servers = servers_for_view(view_or_window)
        if isinstance(view_or_window, sublime.View):
            for server in servers:
                uri = get_view_uri(view_or_window)
                result.append((uri, server.diagnostics.get(uri)))
        elif isinstance(view_or_window, sublime.Window):
            for server in servers:
                result.append(list(server.diagnostics.items()))
        return result
