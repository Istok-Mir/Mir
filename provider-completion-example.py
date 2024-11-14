from __future__ import annotations
from .api import CompletionProvider
from .api.types import CompletionItem, CompletionList


class ExampleCompletionProvider(CompletionProvider):
	name='HellooCompletionsGoodbyeMyTime'
	activation_events={
		'selector': 'source.js'
	}

	async def provide_completion_items(self, view, point) -> list[CompletionItem] | CompletionList | None:
		return [{
			'label': 'Helloo',
		}]
