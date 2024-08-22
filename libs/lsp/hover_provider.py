from __future__ import annotations
from typing import List
from lsp.server import ActivationEvents
from lsp.types import Hover
import sublime

class HoverProviders:
	providers: List[HoverProvider]=[]

class HoverProvider:
	name: str
	activation_events: ActivationEvents

	async def provide_hover(self, view: sublime.View, hover_point: int) -> Hover:
		...

def register_hover_provider(hover_provider: HoverProvider):
	HoverProviders.providers.append(hover_provider)
	print('implement register_hover_provider')

def unregister_hover_provider(hover_provider: HoverProvider):
	print('implement unregister_hover_provider')
