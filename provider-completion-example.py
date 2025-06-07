from __future__ import annotations

import asyncio
from Mir import CompletionProvider
from Mir.types.lsp import CompletionItem, CompletionList


class ExampleCompletionProvider(CompletionProvider):
	name='HellooCompletionsGoodbyeMyTime'
	activation_events={
		'selector': 'source.js'
	}

	async def provide_completion_items(self, view, prefix, locations) -> list[CompletionItem] | CompletionList | None:
		await asyncio.sleep(0.3)
		return [{
			'label': 'Helloo',
		}]
