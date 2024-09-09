from __future__ import annotations
from .api import mir, run_future
import sublime_plugin

class ShowSymbolsCommand(sublime_plugin.WindowCommand):
	def run(self):
		run_future(self.show_symbols())

	async def show_symbols(self):
		view = self.window.active_view()
		document_symbols = await mir.document_symbols(view)
		print('document_symbols', document_symbols)
		document_symbols2 = await mir.document_symbols(view)
		print('document_symbols2', document_symbols)
		document_symbols3 = await mir.document_symbols(view)
		print('document_symbols3', document_symbols)
		document_symbols4 = await mir.document_symbols(view)
		print('document_symbols4', document_symbols)


