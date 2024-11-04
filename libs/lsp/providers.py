from __future__ import annotations
from typing import List, Union, TYPE_CHECKING
from .server import ActivationEvents
from .types import CompletionItem, Hover, CompletionList, Definition, Location, LocationLink, SymbolInformation, DocumentSymbol
import sublime

class BaseProvider:
    @classmethod
    def setup(cls):
        register_provider(cls())

    @classmethod
    def cleanup(cls):
        unregister_provider(cls)


    async def cancel(self) -> None:
        ...


class Providers:
    definition_providers: List[DefinitionProvider]=[]
    reference_providers: List[ReferencesProvider]=[]
    hover_providers: List[HoverProvider]=[]
    completion_providers: List[CompletionProvider]=[]
    document_symbols_providers: List[DocumentSymbolProvider]=[]


class DefinitionProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_definition(self, view: sublime.View, point: int) -> Definition | list[LocationLink] | None:
        ...


class ReferencesProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_references(self, view: sublime.View, point: int) -> list[Location] | None:
        ...


class HoverProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_hover(self, view: sublime.View, hover_point: int, hover_zone: sublime.HoverZone) -> Hover | None:
        ...


class CompletionProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_completion_items(self, view: sublime.View, point: int) -> list[CompletionItem] | CompletionList | None:
        ...


class DocumentSymbolProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_document_symbol(self, view: sublime.View) -> list[SymbolInformation] | list[DocumentSymbol] | None:
        ...

AllProviders = Union[DefinitionProvider, ReferencesProvider, HoverProvider, CompletionProvider, DocumentSymbolProvider]
def register_provider(provider: AllProviders):
    if isinstance(provider, DefinitionProvider):
        Providers.definition_providers.append(provider)
    elif isinstance(provider, ReferencesProvider):
        Providers.reference_providers.append(provider)
    elif isinstance(provider, HoverProvider):
        Providers.hover_providers.append(provider)
    elif isinstance(provider, CompletionProvider):
        Providers.completion_providers.append(provider)
    elif isinstance(provider, DocumentSymbolProvider):
        Providers.document_symbols_providers.append(provider)
    else:
        raise Exception(f'Mir: Got a unusported provider {provider.name} during register_provider')


def unregister_provider(provider: AllProviders):
    if isinstance(provider, DefinitionProvider):
        Providers.definition_providers = [p for p in Providers.definition_providers if p != provider]
    elif isinstance(provider, ReferencesProvider):
        Providers.reference_providers = [p for p in Providers.reference_providers if p != provider]
    elif isinstance(provider, HoverProvider):
        Providers.hover_providers = [p for p in Providers.hover_providers if p != provider]
    elif isinstance(provider, CompletionProvider):
        Providers.completion_providers = [p for p in Providers.completion_providers if p != provider]
    elif isinstance(provider, DocumentSymbolProvider):
        Providers.document_symbols_providers = [p for p in Providers.document_symbols_providers if p != provider]
    else:
        raise Exception(f'Mir: Got a unusported provider {provider.name} during unregister_provider')

