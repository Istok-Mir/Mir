from __future__ import annotations
from lsp.text_document import TextDocument
import sublime_plugin
from event_loop import run_future

class ShowSymbolsCommand(sublime_plugin.WindowCommand):
	def run(self):
		print('eeej')
		run_future(self.show_symbols())

	async def show_symbols(self):
		document_symbols = await TextDocument(self.window.active_view()).document_symbols()
		print('document_symbols', document_symbols)


class ShowSymbols2Command(sublime_plugin.WindowCommand):
    def run(self):
        run_future(self.show_symbols())

    async def show_symbols(self):
        document_symbols = await TextDocument(self.window.active_view()).document_symbols()
        print('document_symbols', document_symbols)
