from __future__ import annotations
from typing import List, Union
from .server import ActivationEvents
from .types import CompletionItem, Hover, CompletionList
import sublime

class Providers:
	hover_providers: List[HoverProvider]=[]
	completion_providers: List[CompletionProvider]=[]

class HoverProvider:
	name: str
	activation_events: ActivationEvents

	async def provide_hover(self, view: sublime.View, hover_point: int) -> Hover:
		...

class CompletionProvider:
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
	print('implement unregister_hover_provider')
