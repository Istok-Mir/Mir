from __future__ import annotations
import sublime
from typing import List, Union
from .api import CompletionProvider
from .api.types import CompletionItem, CompletionList


class ExampleCompletionProvider(CompletionProvider):
	name='HellooCompletionsGoodbyeMyTime'
	activation_events={
		'selector': 'source.js'
	}

	async def provide_completion_items(self, view: sublime.View, point: int) -> Union[List[CompletionItem], CompletionList, None]:
		return [{
			'label': 'Helloo',
		}]
