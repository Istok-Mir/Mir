from __future__ import annotations
from .dotted_dict import DottedDict
from .types import ClientCapabilities, CompletionItemKind, CompletionItemTag, InsertTextMode, MarkupKind
from typing import Any, Literal, cast

CLIENT_CAPABILITIES: ClientCapabilities = {
    'general': {
        'regularExpressions': {'engine': 'ECMAScript'},
        'markdown': {'parser': 'Python-Markdown', 'version': '3.2.2'}
    },
    'textDocument': {
        'synchronization': {
            'dynamicRegistration': True,
            'didSave': True,
            'willSave': True,
            'willSaveWaitUntil': True
        },
        'hover': {
            'dynamicRegistration': True,
            'contentFormat': [MarkupKind.PlainText]
        },
        'completion': {
            'dynamicRegistration': True,
            'completionItem': {
                'snippetSupport': True,
                'deprecatedSupport': True,
                'documentationFormat': [MarkupKind.PlainText],
                'tagSupport': {'valueSet': [CompletionItemTag.Deprecated]},
                'resolveSupport': {
                    'properties': ['detail', 'documentation', 'additionalTextEdits']
                },
                'insertReplaceSupport': True,
                'insertTextModeSupport': {'valueSet': [InsertTextMode.AdjustIndentation]},
                'labelDetailsSupport': True},
                'completionItemKind': {
                    'valueSet': [v.value for v in CompletionItemKind]
                },
                'insertTextMode': 2,
                'completionList': {
                    'itemDefaults': ['editRange', 'insertTextFormat', 'data']
                }
            },
        'signatureHelp': {
            'dynamicRegistration': True,
            'contextSupport': True,
            'signatureInformation': {
                'activeParameterSupport': True,
                'documentationFormat': [MarkupKind.PlainText],
                'parameterInformation': {'labelOffsetSupport': True}
            }
        },
        'references': {'dynamicRegistration': True},
        'documentHighlight': {'dynamicRegistration': True},
        'documentSymbol': {
            'dynamicRegistration': True,
            'hierarchicalDocumentSymbolSupport': True,
            'symbolKind': {
                'valueSet': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
            },
            'tagSupport': {'valueSet': [1]}
        },
        'documentLink': {
            'dynamicRegistration': True,
            'tooltipSupport': True
        },
        'formatting': {'dynamicRegistration': True},
        'rangeFormatting': {'dynamicRegistration': True, 'rangesSupport': True},
        'declaration': {'dynamicRegistration': True, 'linkSupport': True},
        'definition': {'dynamicRegistration': True, 'linkSupport': True},
        'typeDefinition': {'dynamicRegistration': True, 'linkSupport': True},
        'implementation': {'dynamicRegistration': True, 'linkSupport': True},
        'codeAction': {
            'dynamicRegistration': True,
            'codeActionLiteralSupport': {
                'codeActionKind': {
                    'valueSet': ['quickfix', 'refactor', 'refactor.extract', 'refactor.inline', 'refactor.rewrite', 'source.fixAll', 'source.organizeImports']
                }},
                'dataSupport': True,
                'isPreferredSupport': True,
                'resolveSupport': {'properties': ['edit']}
            },
        'rename': {
            'dynamicRegistration': True,
            'prepareSupport': True,
            'prepareSupportDefaultBehavior': 1
        },
        'colorProvider': {'dynamicRegistration': True},
        'publishDiagnostics': {
            'relatedInformation': True,
            'tagSupport': {
                'valueSet': [1, 2]
            },
            'versionSupport': True,
            'codeDescriptionSupport': True,
            'dataSupport': True
        },
        'diagnostic': {'dynamicRegistration': True, 'relatedDocumentSupport': True},
        'selectionRange': {'dynamicRegistration': True},
        'foldingRange': {
            'dynamicRegistration': True,
            'foldingRangeKind': {
                'valueSet': ['comment', 'imports', 'region']
            }
        },
        'codeLens': {'dynamicRegistration': True},
        'inlayHint': {
            'dynamicRegistration': True,
            'resolveSupport': {'properties': ['textEdits', 'label.command']}
        },
        'semanticTokens': {
            'dynamicRegistration': True,
            'requests': {'range': True, 'full': {'delta': True}},
            'tokenTypes': ['namespace', 'type', 'class', 'enum', 'interface', 'struct', 'typeParameter', 'parameter', 'variable', 'property', 'enumMember', 'event', 'function', 'method', 'macro', 'keyword', 'modifier', 'comment', 'string', 'number', 'regexp', 'operator', 'decorator', 'member'],
            'tokenModifiers': ['declaration', 'definition', 'readonly', 'static', 'deprecated', 'abstract', 'async', 'modification', 'documentation', 'defaultLibrary'],
            'formats': ['relative'],
            'overlappingTokenSupport': False,
            'multilineTokenSupport': True,
            'augmentsSyntaxTokens': True},
            'callHierarchy': {'dynamicRegistration': True},
            'typeHierarchy': {'dynamicRegistration': True}
        },
    'workspace': {
        'applyEdit': True,
        'didChangeConfiguration': {'dynamicRegistration': True},
        'executeCommand': {},
        'workspaceEdit': {
            'documentChanges': True,
            'failureHandling': 'abort'
        },
        'workspaceFolders': True,
        'symbol': {
            'dynamicRegistration': True,
            'resolveSupport': {'properties': ['location.range']},
            'symbolKind': {'valueSet': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]},
            'tagSupport': {
                'valueSet': [1]
            }
        },
        'configuration': True,
        'codeLens': {'refreshSupport': True},
        'inlayHint': {'refreshSupport': True},
        'semanticTokens': {'refreshSupport': True},
        'didChangeWatchedFiles': {
            'dynamicRegistration': True,
        }
    },
    'window': {
        'showDocument': {'support': True},
        'showMessage': {
            'messageActionItem': {
                'additionalPropertiesSupport': True
            }
        },
        'workDoneProgress': False
    }
}

ServerCapability = Literal[
    'callHierarchyProvider',
    'codeActionProvider',
    'codeLensProvider',
    'colorProvider',
    'completionProvider',
    'declarationProvider',
    'definitionProvider',
    'diagnosticProvider',
    'documentFormattingProvider',
    'documentOnTypeFormattingProvider',
    'documentHighlightProvider',
    'documentLinkProvider',
    'documentRangeFormattingProvider',
    'documentSymbolProvider',
    'executeCommandProvider',
    'foldingRangeProvider',
    'hoverProvider',
    'implementationProvider',
    'inlineValueProvider',
    'linkedEditingRangeProvider',
    'monikerProvider',
    'referencesProvider',
    'renameProvider',
    'selectionRangeProvider',
    'semanticTokensProvider',
    'signatureHelpProvider',
    'textDocumentSync',
    'textDocumentSync.change',
    'textDocumentSync.didClose',
    'textDocumentSync.didOpen',
    'textDocumentSync.save',
    'textDocumentSync.willSave',
    'textDocumentSync.willSaveWaitUntil',
    'typeDefinitionProvider',
    'workspace.didChangeWatchedFiles',
    'workspace.fileOperations.didCreate',
    'workspace.fileOperations.didDelete',
    'workspace.fileOperations.didRename',
    'workspace.workspaceFolders',
    'workspaceSymbolProvider',
    'workspace.didChangeConfiguration',
    'diagnosticProvider.identifier',
    'completionProvider.resolveProvider',
    'codeActionProvider.resolveProvider'
]

_METHOD_TO_CAPABILITY: dict[str, ServerCapability] = {
    'textDocument/completion': 'completionProvider',
    'textDocument/hover': 'hoverProvider',
    'textDocument/signatureHelp': 'signatureHelpProvider',
    'textDocument/declaration': 'declarationProvider',
    'textDocument/definition': 'definitionProvider',
    'textDocument/typeDefinition':  'typeDefinitionProvider',
    'textDocument/implementation':  'implementationProvider',
    'textDocument/references': 'referencesProvider',
    'textDocument/documentHighlight': 'documentHighlightProvider',
    'textDocument/documentSymbol': 'documentSymbolProvider',
    'textDocument/codeAction': 'codeActionProvider',
    'textDocument/codeLens': 'codeLensProvider',
    'textDocument/documentLink': 'documentLinkProvider',
    'textDocument/documentColor': 'colorProvider',
    'textDocument/formatting': 'documentFormattingProvider',
    'textDocument/rangeFormatting': 'documentRangeFormattingProvider',
    'textDocument/rename': 'renameProvider',
    'textDocument/foldingRange': 'foldingRangeProvider',
    'textDocument/selectionRange': 'selectionRangeProvider',
    'workspace/executeCommand': 'executeCommandProvider',
    'textDocument/linkedEditingRange': 'linkedEditingRangeProvider',
    'textDocument/prepareCallHierarchy': 'callHierarchyProvider',
    'textDocument/semanticTokens/full': 'semanticTokensProvider',
    'textDocument/moniker': 'monikerProvider',
    'textDocument/inlineValue': 'inlineValueProvider',
    'textDocument/diagnostic': 'diagnosticProvider',
    'workspace/symbol': 'workspaceSymbolProvider',
    'workspace/didChangeWorkspaceFolders': 'workspace.workspaceFolders',
    'textDocument/didOpen': 'textDocumentSync.didOpen',
    'textDocument/didClose': 'textDocumentSync.didClose',
    'textDocument/didChange': 'textDocumentSync.change',
    'textDocument/didSave': 'textDocumentSync.save',
    'textDocument/willSave': 'textDocumentSync.willSave',
    'textDocument/willSaveWaitUntil': 'textDocumentSync.willSaveWaitUntil',
    'workspace/didChangeWatchedFiles': 'workspace.didChangeWatchedFiles',
    'workspace/didChangeConfiguration': 'workspace.didChangeConfiguration',
    'textDocument/onTypeFormatting': 'documentOnTypeFormattingProvider'
}

def method_to_capability(method: str) -> ServerCapability:
    capability_path = _METHOD_TO_CAPABILITY.get(method, None)
    if capability_path is None:
        raise Exception(f'method_to_capability error. Fix: Add {method} to `_METHOD_TO_CAPABILITY`.')
    return cast(ServerCapability, capability_path)


class ServerCapabilities(DottedDict):
    def has(self, server_capability: ServerCapability) -> bool:
        value = self.get(server_capability)
        return value is not False and value is not None

    def get(self, server_capability: ServerCapability):
        return super().get(server_capability)

    def register(
        self,
        server_capability: ServerCapability,
        options: dict[str, Any]
    ) -> None:
        capability = self.get(server_capability)
        if isinstance(capability, str):
            msg = f"{server_capability} is already registered. Skipping."
            print(msg)
            return
        self.set(server_capability, options)

    def unregister(
        self,
        server_capability: ServerCapability,
    ) -> None:
        capability = self.get(server_capability)
        if not capability:
            print(f"{server_capability} is not present in the current capabilities. Skipping.")
            return
        self.remove(server_capability)
