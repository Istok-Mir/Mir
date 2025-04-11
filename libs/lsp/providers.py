from __future__ import annotations
from typing import List, Union

from sublime_plugin import importlib
from .server import ActivationEvents
from .types import CodeActionContext, CompletionItem, Hover, CompletionList, Definition, Location, LocationLink, SymbolInformation, DocumentSymbol, Command, CodeAction
import sublime

callbacks_when_ready = []

class BaseProvider:
    def is_applicable(self) -> bool:
        return True

    async def cancel(self) -> None:
        ...

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        global callbacks_when_ready

        def is_api_ready():
            from sublime_plugin import api_ready
            return api_ready

        api_ready = is_api_ready()
        def run():
            for parent in cls.__bases__:
                if parent.__name__ in ['LspProvider', 'BaseProvider']:
                    # skip classes like LspDefinitionProvider, Or DefinitionProvider and any class that directly inherits LspProvider or BaseProvider
                    return 
            provider = cls()
            register_provider(provider)

            def schedule():
                m = importlib.import_module(cls.__module__)
                original_plugin_unloaded = m.__dict__.get('plugin_unloaded')

                def override_plugin_unloaded():
                    if original_plugin_unloaded:
                        original_plugin_unloaded()
                    unregister_provider(provider)

                m.__dict__['plugin_unloaded'] = override_plugin_unloaded

            sublime.set_timeout(schedule, 1)
        if not api_ready:
            callbacks_when_ready.append(run)
        else:
            run()

class Providers:
    definition_providers: List[DefinitionProvider]=[]
    reference_providers: List[ReferencesProvider]=[]
    code_action_providers: List[CodeActionProvider]=[]
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


class CodeActionProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_code_actions(self, view: sublime.View, region: sublime.Region, context: CodeActionContext) -> list[Command | CodeAction] | None:
        ...


class HoverProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_hover(self, view: sublime.View, hover_point: int, hover_zone: sublime.HoverZone) -> Hover | None:
        ...


class CompletionProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_completion_items(self, view: sublime.View, prefix:str, locations: list[int]) -> list[CompletionItem] | CompletionList | None:
        ...

    async def resolve_completion_item(self, completion_item: CompletionItem) -> CompletionItem:
        return completion_item


class DocumentSymbolProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_document_symbol(self, view: sublime.View) -> list[SymbolInformation] | list[DocumentSymbol] | None:
        ...

AllProviders = Union[DefinitionProvider, ReferencesProvider, CodeActionProvider, HoverProvider, CompletionProvider, DocumentSymbolProvider]
def register_provider(provider: AllProviders):
    if isinstance(provider, DefinitionProvider):
        Providers.definition_providers.append(provider)
    elif isinstance(provider, ReferencesProvider):
        Providers.reference_providers.append(provider)
    elif isinstance(provider, CodeActionProvider):
        Providers.code_action_providers.append(provider)
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
    elif isinstance(provider, CodeActionProvider):
        Providers.code_action_providers = [p for p in Providers.code_action_providers if p != provider]
    elif isinstance(provider, HoverProvider):
        Providers.hover_providers = [p for p in Providers.hover_providers if p != provider]
    elif isinstance(provider, CompletionProvider):
        Providers.completion_providers = [p for p in Providers.completion_providers if p != provider]
    elif isinstance(provider, DocumentSymbolProvider):
        Providers.document_symbols_providers = [p for p in Providers.document_symbols_providers if p != provider]
    else:
        raise Exception(f'Mir: Got a unusported provider {provider.name} during unregister_provider')

