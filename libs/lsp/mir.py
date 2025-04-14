from __future__ import annotations
import asyncio
from typing import List

from sublime_aio import overload

from .commands import MirCommand
import sys
from .manage_servers import server_for_view, servers_for_view, servers_for_window
from .providers import CodeActionProvider, Providers, HoverProvider, CompletionProvider, DefinitionProvider, DocumentSymbolProvider, ReferencesProvider
from .server import is_applicable_view
from .types import CodeAction, CodeActionContext, Command, Definition, DocumentSymbol, Location, SymbolInformation, LocationLink, Hover, CompletionItem, CompletionList, DocumentUri, Diagnostic
from .view_to_lsp import get_view_uri, range_to_region
import sublime

SourceName = str
""" The language server name or the provider name """

MAX_WAIT_TIME=1 # second is a lot of time

class mir:
    commands = MirCommand

    @staticmethod
    async def definitions(view: sublime.View, point: int) -> list[tuple[SourceName, Definition | list[LocationLink] | None]]:
        # STEP 1:
        providers = [provider for provider in Providers.definition_providers if provider.is_applicable() and is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, Definition | list[LocationLink] | None]] = []

        # STEP 3:
        async def handle(provider: DefinitionProvider):
            try:
                result = await asyncio.wait_for(provider.provide_definition(view, point), MAX_WAIT_TIME)
            except Exception as e:
                await provider.cancel()
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
    async def references(view: sublime.View, point: int) -> list[tuple[SourceName, list[Location] | None]]:
        # STEP 1:
        providers = [provider for provider in Providers.reference_providers if provider.is_applicable() and is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, list[Location] | None]] = []

        # STEP 3:
        async def handle(provider: ReferencesProvider):
            try:
                result = await asyncio.wait_for(provider.provide_references(view, point), MAX_WAIT_TIME)
            except Exception as e:
                await provider.cancel()
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        try:
            results = await asyncio.gather(
                *[handle(provider) for provider in providers],
            )
        except Exception as e:
            print('Mir (ReferenceError):', e)
        return results

    @staticmethod
    async def code_actions(view: sublime.View, region: sublime.Region, context: CodeActionContext) -> list[tuple[SourceName, list[Command | CodeAction] | None]]:
        # STEP 1:
        providers = [provider for provider in Providers.code_action_providers if provider.is_applicable() and is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, list[Command | CodeAction] | None]] = []

        # STEP 3:
        async def handle(provider: CodeActionProvider):
            try:
                diagnostics = await mir.get_diagnostics(provider.name, view)
                diagnostics_in_region = [d for d in diagnostics if region.intersects(range_to_region(view, d['range']))]
                context['diagnostics'].extend(diagnostics_in_region)
                result = await asyncio.wait_for(provider.provide_code_actions(view, region, context), MAX_WAIT_TIME)
            except Exception as e:
                await provider.cancel()
                print(f'Error happened in provider {provider.name}', e)
                return (provider.name, None)
            return (provider.name, result)

        try:
            results = await asyncio.gather(
                *[handle(provider) for provider in providers],
            )
        except Exception as e:
            print('Mir (CodeActionError):', e)
        return results

    @staticmethod
    async def hover(view: sublime.View, hover_point: int, hover_zone: sublime.HoverZone) -> list[tuple[SourceName, Hover | None]]:
        # STEP 1:
        # Trigger Canceling Providers
        providers = [provider for provider in Providers.hover_providers if provider.is_applicable() and is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, Hover | None]] = []

        # STEP 3:
        async def handle(provider: HoverProvider):
            try:
                result = await asyncio.wait_for(provider.provide_hover(view, hover_point, hover_zone), MAX_WAIT_TIME)
            except Exception as e:
                await provider.cancel()
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

    cache_completion_response = {}
    @staticmethod
    async def completions(view: sublime.View, prefix: str, locations: list[int]) -> list[tuple[SourceName, list[CompletionItem] | CompletionList | None]]:
        # STEP 1:
        # Trigger Canceling Providers
        providers = [provider for provider in Providers.completion_providers if provider.is_applicable() and is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, list[CompletionItem] | CompletionList | None]] = []

        # STEP 3:
        async def handle(provider: CompletionProvider):
            try:
                cache = mir.cache_completion_response.get(provider.name)
                if cache is not None:
                    return cache
                result = await asyncio.wait_for(provider.provide_completion_items(view, prefix, locations), MAX_WAIT_TIME)
                if sizeof(result) > 1_000_000:
                    mir.cache_completion_response[provider.name] = result
                    def reset():
                        del mir.cache_completion_response[provider.name]
                    sublime.set_timeout(reset, 60_000) # this prevent lag while typing for 6 seconds
            except Exception as e:
                await provider.cancel()
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
            print('Mir (CompletionError):', e)
        return results

    @staticmethod
    async def document_symbols(view: sublime.View) -> list[tuple[SourceName, list[SymbolInformation] | list[DocumentSymbol] | None]]:
        # STEP 1:
        providers = [provider for provider in Providers.document_symbols_providers if provider.is_applicable() and is_applicable_view(view, provider.activation_events)]
        for provider in providers:
            await provider.cancel()

        # STEP 2 define return value
        results: list[tuple[SourceName, List[SymbolInformation] | List[DocumentSymbol] | None]] = []
        # STEP 3:
        async def handle(provider: DocumentSymbolProvider):
            try:
                result = await asyncio.wait_for(provider.provide_document_symbol(view), MAX_WAIT_TIME)
            except Exception as e:
                await provider.cancel()
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

    @overload
    @staticmethod
    async def get_diagnostics(view: sublime.View) -> list[tuple[SourceName, list[Diagnostic]]]:
        result: list[tuple[SourceName, list[Diagnostic]]] = []
        map_result: dict[SourceName, list[Diagnostic]] = {}
        servers = servers_for_view(view)
        uri = get_view_uri(view)
        for server in servers:
            if server.name not in map_result:
                map_result[server.name] = []
            map_result[server.name].extend(server.diagnostics.get(uri))
        result = list(map_result.items())
        return result

    @overload
    @staticmethod
    async def get_diagnostics(name: str, view: sublime.View) -> list[Diagnostic]:
        uri = get_view_uri(view)
        server = server_for_view(name, view)
        if not server:
            return []
        return server.diagnostics.get(uri)

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

def sizeof(obj):
    size = sys.getsizeof(obj)
    if isinstance(obj, dict): return size + sum(map(sizeof, obj.keys())) + sum(map(sizeof, obj.values()))
    if isinstance(obj, (list, tuple, set, frozenset)): return size + sum(map(sizeof, obj))
    return size
