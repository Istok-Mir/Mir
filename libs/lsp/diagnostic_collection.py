from __future__ import annotations
from typing import List, Tuple, Callable, Any
from .types import DocumentUri, Diagnostic  # Assuming you're importing these from `lsp_types`


class DiagnosticCollection:
    def __init__(self):
        # Internal dictionary to store diagnostics associated with URIs
        self._diagnostics: dict[DocumentUri, list[Diagnostic]] = {}

    def __iter__(self) -> Iterator[Tuple[DocumentUri, List[Diagnostic]]]:
        """Magic method to make the collection iterable."""
        return iter(self._diagnostics.items())

    def clear(self):
        """Clear all diagnostics from the collection."""
        self._diagnostics.clear()

    def delete(self, uri: DocumentUri):
        """Delete diagnostics for a specific URI."""
        if uri in self._diagnostics:
            del self._diagnostics[uri]

    def get(self, uri: DocumentUri) -> List[Diagnostic]:
        """Get diagnostics for a specific URI."""
        return self._diagnostics.get(uri, [])

    def has(self, uri: DocumentUri) -> bool:
        """Check if diagnostics exist for a specific URI."""
        return uri in self._diagnostics

    def set(self, uri_or_entries: DocumentUri | tuple[DocumentUri, list[Diagnostic]], diagnostics: List[Diagnostic] = None):
        """
        Set diagnostics for a specific URI or set multiple URI-diagnostic pairs.
        If `uri_or_entries` is a Uri, the `diagnostics` argument must be provided.
        If `uri_or_entries` is a list of tuples, each tuple should contain a Uri and a list of Diagnostics.
        """
        if isinstance(uri_or_entries, str):
            # Single URI-Diagnostic pair
            self._diagnostics[uri_or_entries] = diagnostics or []
        elif isinstance(uri_or_entries, list):
            # Multiple URI-Diagnostic pairs
            for uri, diag_list in uri_or_entries:
                self._diagnostics[uri] = diag_list
