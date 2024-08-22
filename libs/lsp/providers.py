from __future__ import annotations
from typing import List
from lsp.server import ActivationEvents
from lsp.types import Hover
import sublime

class Providers:
	hover_providers: List[HoverProvider]=[]

class HoverProvider:
	name: str
	activation_events: ActivationEvents

	async def provide_hover(self, view: sublime.View, hover_point: int) -> Hover:
		...

def register_provider(provider: HoverProvider):
	if isinstance(provider, HoverProvider):
		Providers.hover_providers.append(provider)
	else:
		raise Exception('Got a unusported provider')

def unregister_provider(provider: HoverProvider):
	print('implement unregister_hover_provider')
