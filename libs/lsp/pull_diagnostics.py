from __future__ import annotations
from typing import TYPE_CHECKING

from Mir import mir_logger
if TYPE_CHECKING:
    from Mir.types.lsp import DocumentDiagnosticParams
    from .server import LanguageServer

async def pull_diagnostics(server: LanguageServer, uri: str) -> None:
    from .mir import mir
    if not server.capabilities.has('diagnosticProvider'):
        return
    try:
        params: DocumentDiagnosticParams = {
            'textDocument': {
                'uri': uri
            },
        }
        identifier = server.capabilities.get('diagnosticProvider.identifier')
        if identifier:
            params['identifier'] = identifier
        if server.diagnostics_previous_result_id is not None:
            params['previousResultId'] = server.diagnostics_previous_result_id
        req = server.send.text_document_diagnostic(params)
        result = await req.result
        server.diagnostics_previous_result_id = result.get('resultId')
        if 'items' in result:
            server.diagnostics.set(uri, result['items'])
            mir._notify_did_change_diagnostics([uri])
    except Exception as e:
        mir_logger.error('Mir: Error in diagnostic pull', exc_info=e)
