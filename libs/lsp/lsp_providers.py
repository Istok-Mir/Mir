from __future__ import annotations

from .providers import CompletionProvider, DefinitionProvider, CodeActionProvider, HoverProvider, DocumentSymbolProvider, ReferencesProvider
from .lsp_requests import Request
from typing import TYPE_CHECKING
from .view_to_lsp import get_view_uri, point_to_position, region_to_range
import sublime
if TYPE_CHECKING:
    import sublime
    from .types import CompletionItem, CompletionList, Definition, LocationLink, Hover, SymbolInformation, DocumentSymbol, Location, CodeAction, Command, CodeActionContext
    from .capabilities import ServerCapability
    from .server import LanguageServer

class LspProvider:
    def is_applicable(self):
        # LSP Providers are only active for a given window
        return self.server.window == sublime.active_window()

    def __init__(self, server: LanguageServer):
        self.server = server
        self.name = self.server.name
        self.activation_events = self.server.activation_events
        self._requests: list[Request]=[]

class LspDefinitionProvider(LspProvider, DefinitionProvider):
    async def provide_definition(self, view: sublime.View, point: int) -> Definition | list[LocationLink] | None:
        uri = get_view_uri(view)
        req = self.server.send.definition({
            'textDocument': {
                'uri': uri
            },
            'position': point_to_position(view, point)
        })
        self._requests.append(req)
        return await req.result

    async def cancel(self):
        if self._requests:
            for request in self._requests:
                request.cancel()
        self._requests = []


class LspReferencesProvider(LspProvider, ReferencesProvider):
    async def provide_references(self, view: sublime.View, point: int) -> list[Location] | None:
        uri = get_view_uri(view)
        req = self.server.send.references({
            'context': { 'includeDeclaration': True},
            'textDocument': {'uri': uri },
            'position': point_to_position(view, point)
        })
        self._requests.append(req)
        return await req.result

    async def cancel(self):
        if self._requests:
            for request in self._requests:
                request.cancel()
        self._requests = []

class LspCodeActionProvider(LspProvider, CodeActionProvider):
    async def provide_code_actions(self, view: sublime.View, region: sublime.Region, context: CodeActionContext) -> list[Command | CodeAction] | None:
        uri = get_view_uri(view)
        req = self.server.send.code_action({
            'textDocument': {'uri': uri },
            'range': region_to_range(view, region),
            'context': context
        })
        self._requests.append(req)
        return await req.result

    async def cancel(self):
        if self._requests:
            for request in self._requests:
                request.cancel()
        self._requests = []



class LspCompletionProvider(LspProvider, CompletionProvider):
    async def provide_completion_items(self, view: sublime.View, prefix, locations) -> list[CompletionItem] | CompletionList | None:
        point = locations[0]
        uri = get_view_uri(view)
        req = self.server.send.completion({
            'textDocument': {
                'uri': uri
            },
            'position': point_to_position(view, point)
        })
        self._requests.append(req)
        return await req.result

    async def resolve_completion_item(self, completion_item) -> CompletionItem:
        if not self.server.capabilities.has('completionProvider.resolveProvider'):
            return completion_item
        req = self.server.send.resolve_completion_item(completion_item)
        self._requests.append(req)
        resolved_completion_item = await req.result
        return resolved_completion_item

    async def cancel(self):
        if self._requests:
            for request in self._requests:
                request.cancel()
        self._requests = []


class LspHoverProvider(LspProvider, HoverProvider):
    async def provide_hover(self, view: sublime.View, hover_point: int, hover_zone: sublime.HoverZone) -> Hover | None:
        uri = get_view_uri(view)
        req = self.server.send.hover({
            'textDocument': {
                'uri': uri
            },
            'position': point_to_position(view, hover_point)
        })
        self._requests.append(req)
        return await req.result

    async def cancel(self):
        if self._requests:
            for request in self._requests:
                request.cancel()
        self._requests = []


class LspDocumentSymbolProvider(LspProvider, DocumentSymbolProvider):
    async def provide_document_symbol(self, view: sublime.View) -> list[SymbolInformation] | list[DocumentSymbol] | None:
        uri = get_view_uri(view)
        req = self.server.send.document_symbol({
            'textDocument': {
                'uri': uri
            },
        })
        self._requests.append(req)
        return await req.result

    async def cancel(self):
        if self._requests:
            for request in self._requests:
                request.cancel()
        self._requests = []


capabilities_to_lsp_providers: dict[ServerCapability, type[LspProvider]] = {
    'definitionProvider': LspDefinitionProvider,
    'referencesProvider': LspReferencesProvider,
    'codeActionProvider': LspCodeActionProvider,
    'hoverProvider': LspHoverProvider,
    'completionProvider': LspCompletionProvider,
    'documentSymbolProvider': LspDocumentSymbolProvider,
}
