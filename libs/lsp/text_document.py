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


class mir:
    @staticmethod
    async def document_symbols(view: sublime.View | None) -> list[Result[List[SymbolInformation] | List[DocumentSymbol] | None]]:
        if not view:
            return []
        if not view.is_valid():
            return []
        uri = get_view_uri(view)
        servers = servers_for_view(view, 'documentSymbolProvider')
        results: list[Result[List[SymbolInformation] | List[DocumentSymbol] | None]] = []
        for s in servers:
            result = await s.send.document_symbol({
                'textDocument': {
                    'uri': uri
                },
            }).result
            print('res', result)
            results.append(Result(s.name, result))
        return results

