from __future__ import annotations
from typing import List
from .manage_servers import servers_for_view
from .types import DocumentSymbol, SymbolInformation
from .view_to_lsp import get_view_uri
import sublime
from typing import TypeVar, Generic

T = TypeVar('T')
ServerName = str
CacheKey = str


class Result(Generic[T]):
    def __init__(self, name: str, result: T):
        self.server_name= name
        self.result= result

    def __str__(self):
        return str((self.server_name, self.result))

    def __repr__(self):
        return str((self.server_name, self.result))


class TextDocument:
    document_symbols_cache: dict[CacheKey, List[SymbolInformation] | List[DocumentSymbol] | None] = {}

    def __init__(self, view: sublime.View | None):
        self.view = view

    async def document_symbols(self) -> list[Result[List[SymbolInformation] | List[DocumentSymbol] | None]]:
        if not self.view:
            return []
        if not self.view.is_valid():
            return []
        uri = get_view_uri(self.view)
        servers = servers_for_view(self.view, 'documentSymbolProvider')
        results: list[Result[List[SymbolInformation] | List[DocumentSymbol] | None]] = []
        for s in servers:
            cache_key = self._document_symbols_cache_key(s.name)
            cache = TextDocument.document_symbols_cache.get(cache_key)
            if cache:
                s._log('cache hit textDocument/documentSymbol')
                results.append(Result(s.name, cache))
            else:
                r = await s.send.document_symbol({
                    'textDocument': {
                        'uri': uri
                    },
                })
                results.append(Result(s.name, r))
                TextDocument.document_symbols_cache[cache_key] = r
        return results

    def _document_symbols_cache_key(self, server_name: str):
        if not self.view:
            return ""
        return f"server:{server_name};view_id:{self.view.id()};view_change_count:{self.view.change_count()}"

