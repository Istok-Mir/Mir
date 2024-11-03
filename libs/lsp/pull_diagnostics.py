from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .types import DocumentDiagnosticParams
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
        if server.diagnostics_previous_result_id:
            params['previousResultId'] = server.diagnostics_previous_result_id
        req = server.send.text_document_diagnostic(params)
        result = await req.result
        server.diagnostics_previous_result_id = str(req.id)
        if 'items' in result:
            server.diagnostics.set(uri, result['items'])
            mir._notify_did_change_diagnostics([uri])
    except Exception as e:
        print('Mir: Error in diagnostic pull', e)
