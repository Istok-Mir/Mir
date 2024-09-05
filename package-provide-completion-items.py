from __future__ import annotations
from typing import List, Union
from .libs.lsp.providers import register_provider, unregister_provider
from .libs.lsp.types import CompletionItem, CompletionList
from sublime import sublime_api
from .api import CompletionProvider

class ExampleCompletionProvider(CompletionProvider):
	name= 'HellooCompletionsGoodbyeMyTime'
	activation_events={
		'selector': 'source.js'
	}

	async def provide_completion_items(self, view: sublime_api.View, point: int) -> Union[List[CompletionItem], CompletionList, None]:
		return [{
			'label': 'Helloo',
		}]

example_completion_provider = ExampleCompletionProvider()
def plugin_loaded() -> None:
    register_provider(example_completion_provider)


def plugin_unloaded() -> None:
    unregister_provider(example_completion_provider)
