from __future__ import annotations
from typing import List, Union
from .server import ActivationEvents
from .types import CompletionItem, Hover, CompletionList
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
    hover_providers: List[HoverProvider]=[]
    completion_providers: List[CompletionProvider]=[]

class HoverProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_hover(self, view: sublime.View, hover_point: int) -> Hover:
        ...

class CompletionProvider(BaseProvider):
    name: str
    activation_events: ActivationEvents

    async def provide_completion_items(self, view: sublime.View, point: int) -> Union[List[CompletionItem], CompletionList, None]:
        ...


def register_provider(provider: HoverProvider | CompletionProvider):
    if isinstance(provider, HoverProvider):
        Providers.hover_providers.append(provider)
    elif isinstance(provider, CompletionProvider):
        Providers.completion_providers.append(provider)
    else:
        raise Exception('Got a unusported provider')


def unregister_provider(provider: HoverProvider | CompletionProvider):
    if HoverProvider in provider.__bases__:
        Providers.hover_providers = [p for p in Providers.hover_providers if p.name != provider.name]
    elif CompletionProvider in provider.__bases__:
        Providers.completion_providers = [p for p in Providers.completion_providers if p.name != provider.name]
    else:
        raise Exception(f'Got a unusported provider {provider.__name__}')
