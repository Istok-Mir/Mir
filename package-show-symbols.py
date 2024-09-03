from __future__ import annotations
from lsp.mir import mir
import sublime_plugin
from event_loop import run_future

class ShowSymbolsCommand(sublime_plugin.WindowCommand):
	def run(self):
		print('eeej')
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


