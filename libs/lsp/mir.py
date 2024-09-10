from __future__ import annotations
import asyncio
from typing import List

from .lsp_requests import Request
from .manage_servers import servers_for_view, servers_for_window
from .providers import Providers, HoverProvider, CompletionProvider, DefinitionProvider, DocumentSymbolProvider
from .server import is_applicable_view
from .types import Definition, DocumentSymbol, SymbolInformation, LocationLink, Hover, CompletionItem, CompletionList, DocumentUri, Diagnostic
from .view_to_lsp import get_view_uri, point_to_position
import sublime
from typing import TypeVar, Generic

SourceName = str
""" The language server name or the provider name """

MAX_WAIT_TIME=1 # second

class mir:
    @staticmethod
    async def definitions(view: sublime.View, point: int) -> list[tuple[SourceName, Definition | list[LocationLink] | None]]:
        # STEP 1:
        providers = [provider for provider in Providers.definition_providers if is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, Definition | list[LocationLink] | None]] = []

        # STEP 3:
        async def handle(provider: DefinitionProvider):
            try:
                result = await asyncio.wait_for(provider.provide_definition(view, point), MAX_WAIT_TIME)
            except Exception as e:
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        try:
            results = await asyncio.gather(
                *[handle(provider) for provider in providers],
            )
        except Exception as e:
            print('Mir (DefinitionError):', e)
        return results

    @staticmethod
    async def hover(view: sublime.View, hover_point: int, hover_zone: sublime.HoverZone) -> list[tuple[SourceName, Hover | None]]:
        # STEP 1:
        # Trigger Canceling Providers
        providers = [provider for provider in Providers.hover_providers if is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, Hover | None]] = []

        # STEP 3:
        async def handle(provider: HoverProvider):
            try:
                result = await asyncio.wait_for(provider.provide_hover(view, hover_point, hover_zone), MAX_WAIT_TIME)
            except Exception as e:
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        # STEP 4:
        # await all futures and handle them appropriately
        try:
            results = await asyncio.gather(
                *[handle(provider) for provider in providers],
            )
        except Exception as e:
            print('Mir (HoverError):', e)
        return results

    @staticmethod
    async def completions(view: sublime.View, point: int) -> list[tuple[SourceName, list[CompletionItem] | CompletionList | None]]:
        # STEP 1:
        # Trigger Canceling Providers
        providers = [provider for provider in Providers.completion_providers if is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, list[CompletionItem] | CompletionList | None]] = []

        # STEP 3:
        async def handle(provider: CompletionProvider):
            try:
                result = await asyncio.wait_for(provider.provide_completion_items(view, point), MAX_WAIT_TIME)
            except Exception as e:
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        # STEP 4:
        # await all futures and handle them appropriately
        try:
            results = await asyncio.gather(
                *[handle(provider) for provider in providers]
            )
        except Exception as e:
            print('Mir (CompletionError):', e)
        return results

    @staticmethod
    async def document_symbols(view: sublime.View) -> list[tuple[SourceName, list[SymbolInformation] | list[DocumentSymbol] | None]]:
        # STEP 1:
        providers = [provider for provider in Providers.document_symbols_providers if is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, List[SymbolInformation] | List[DocumentSymbol] | None]] = []

        # STEP 3:
        async def handle(provider: DocumentSymbolProvider):
            try:
                result = await asyncio.wait_for(provider.provide_document_symbol(view), MAX_WAIT_TIME)
            except Exception as e:
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        # STEP 4:
        # await all futures and handle them appropriately
        try:
            results = await asyncio.gather(
                *[handle(provider) for provider in providers],
            )
        except Exception as e:
            print('Mir (DocumentSymbolError):', e)
        return results

    @staticmethod
    async def get_diagnostics(view_or_window: sublime.View | sublime.Window) -> list[tuple[DocumentUri, list[Diagnostic]]]:
        result: list[tuple[DocumentUri, list[Diagnostic]]] = []
        map_result: dict[DocumentUri, list[Diagnostic]] = {}
        if isinstance(view_or_window, sublime.View):
            servers = servers_for_view(view_or_window)
            for server in servers:
                uri = get_view_uri(view_or_window)
                if uri not in map_result:
                    map_result[uri] = []
                map_result[uri].extend(server.diagnostics.get(uri))
        elif isinstance(view_or_window, sublime.Window):
            servers = servers_for_window(view_or_window)
            for server in servers:
                for uri, diagnostics in server.diagnostics.items():
                    if uri not in map_result:
                        map_result[uri] = []
                    map_result[uri].extend(diagnostics)
        result = list(map_result.items())
        return result

    _on_did_change_diagnostics_cbs = []
    @staticmethod
    def on_did_change_diagnostics(cb):
        mir._on_did_change_diagnostics_cbs.append(cb)
        def cleanup():
            mir._on_did_change_diagnostics_cbs = [c for c in mir._on_did_change_diagnostics_cbs if c != cb]
        return cleanup

    @staticmethod
    def _notify_did_change_diagnostics(uris: list[str]):
        [cb(uris) for cb in mir._on_did_change_diagnostics_cbs]
