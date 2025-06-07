from __future__ import annotations

# Code generated. DO NOT EDIT.
import Mir.types.lsp as lsp_types
from typing import TYPE_CHECKING, List, Union, TypeVar, Generic
import asyncio
import datetime

if TYPE_CHECKING:
    from .server import LanguageServer


T = TypeVar('T')
class Request(Generic[T]):
    def __init__(self, server: LanguageServer, id: int, method='', params=None) -> None:
        self.server: LanguageServer = server
        self.result: asyncio.Future[T] = asyncio.Future()
        self.id: int = id
        self.method = method
        self.params = params
        self.request_start_time = datetime.datetime.now()
        self.request_end_time: datetime.datetime | None = None

    @property
    def duration(self):
        if self.request_end_time is None:
            return None
        return round((self.request_end_time-self.request_start_time).total_seconds(), 2)

    def cancel(self):
        if self.request_end_time is not None:
            # ignore canceling finished requests
            return
        self.server.notify.cancel_request({
            'id': self.id
        })
        self.result.cancel()

class LspRequest:
    def __init__(self, send_request):
        self.send_request = send_request

    def implementation(self,  params: lsp_types.ImplementationParams) -> Request[Union['lsp_types.Definition', List['lsp_types.LocationLink'], None]]:
        """ A request to resolve the implementation locations of a symbol at a given text
        document position. The request's parameter is of type {@link TextDocumentPositionParams}
        the response is of type {@link Definition} or a Thenable that resolves to such. """
        return self.send_request("textDocument/implementation", params)

    def type_definition(self,  params: lsp_types.TypeDefinitionParams) -> Request[Union['lsp_types.Definition', List['lsp_types.LocationLink'], None]]:
        """ A request to resolve the type definition locations of a symbol at a given text
        document position. The request's parameter is of type {@link TextDocumentPositionParams}
        the response is of type {@link Definition} or a Thenable that resolves to such. """
        return self.send_request("textDocument/typeDefinition", params)

    def document_color(self,  params: lsp_types.DocumentColorParams) -> Request[List['lsp_types.ColorInformation']]:
        """ A request to list all color symbols found in a given text document. The request's
        parameter is of type {@link DocumentColorParams} the
        response is of type {@link ColorInformation ColorInformation[]} or a Thenable
        that resolves to such. """
        return self.send_request("textDocument/documentColor", params)

    def color_presentation(self,  params: lsp_types.ColorPresentationParams) -> Request[List['lsp_types.ColorPresentation']]:
        """ A request to list all presentation for a color. The request's
        parameter is of type {@link ColorPresentationParams} the
        response is of type {@link ColorInformation ColorInformation[]} or a Thenable
        that resolves to such. """
        return self.send_request("textDocument/colorPresentation", params)

    def folding_range(self,  params: lsp_types.FoldingRangeParams) -> Request[Union[List['lsp_types.FoldingRange'], None]]:
        """ A request to provide folding ranges in a document. The request's
        parameter is of type {@link FoldingRangeParams}, the
        response is of type {@link FoldingRangeList} or a Thenable
        that resolves to such. """
        return self.send_request("textDocument/foldingRange", params)

    def declaration(self,  params: lsp_types.DeclarationParams) -> Request[Union['lsp_types.Declaration', List['lsp_types.LocationLink'], None]]:
        """ A request to resolve the type definition locations of a symbol at a given text
        document position. The request's parameter is of type {@link TextDocumentPositionParams}
        the response is of type {@link Declaration} or a typed array of {@link DeclarationLink}
        or a Thenable that resolves to such. """
        return self.send_request("textDocument/declaration", params)

    def selection_range(self,  params: lsp_types.SelectionRangeParams) -> Request[Union[List['lsp_types.SelectionRange'], None]]:
        """ A request to provide selection ranges in a document. The request's
        parameter is of type {@link SelectionRangeParams}, the
        response is of type {@link SelectionRange SelectionRange[]} or a Thenable
        that resolves to such. """
        return self.send_request("textDocument/selectionRange", params)

    def prepare_call_hierarchy(self,  params: lsp_types.CallHierarchyPrepareParams) -> Request[Union[List['lsp_types.CallHierarchyItem'], None]]:
        """ A request to result a `CallHierarchyItem` in a document at a given position.
        Can be used as an input to an incoming or outgoing call hierarchy.

        @since 3.16.0 """
        return self.send_request("textDocument/prepareCallHierarchy", params)

    def incoming_calls(self,  params: lsp_types.CallHierarchyIncomingCallsParams) -> Request[Union[List['lsp_types.CallHierarchyIncomingCall'], None]]:
        """ A request to resolve the incoming calls for a given `CallHierarchyItem`.

        @since 3.16.0 """
        return self.send_request("callHierarchy/incomingCalls", params)

    def outgoing_calls(self,  params: lsp_types.CallHierarchyOutgoingCallsParams) -> Request[Union[List['lsp_types.CallHierarchyOutgoingCall'], None]]:
        """ A request to resolve the outgoing calls for a given `CallHierarchyItem`.

        @since 3.16.0 """
        return self.send_request("callHierarchy/outgoingCalls", params)

    def semantic_tokens_full(self,  params: lsp_types.SemanticTokensParams) -> Request[Union['lsp_types.SemanticTokens', None]]:
        """ @since 3.16.0 """
        return self.send_request("textDocument/semanticTokens/full", params)

    def semantic_tokens_delta(self,  params: lsp_types.SemanticTokensDeltaParams) -> Request[Union['lsp_types.SemanticTokens', 'lsp_types.SemanticTokensDelta', None]]:
        """ @since 3.16.0 """
        return self.send_request("textDocument/semanticTokens/full/delta", params)

    def semantic_tokens_range(self,  params: lsp_types.SemanticTokensRangeParams) -> Request[Union['lsp_types.SemanticTokens', None]]:
        """ @since 3.16.0 """
        return self.send_request("textDocument/semanticTokens/range", params)

    def linked_editing_range(self,  params: lsp_types.LinkedEditingRangeParams) -> Request[Union['lsp_types.LinkedEditingRanges', None]]:
        """ A request to provide ranges that can be edited together.

        @since 3.16.0 """
        return self.send_request("textDocument/linkedEditingRange", params)

    def will_create_files(self,  params: lsp_types.CreateFilesParams) -> Request[Union['lsp_types.WorkspaceEdit', None]]:
        """ The will create files request is sent from the client to the server before files are actually
        created as long as the creation is triggered from within the client.

        The request can return a `WorkspaceEdit` which will be applied to workspace before the
        files are created. Hence the `WorkspaceEdit` can not manipulate the content of the file
        to be created.

        @since 3.16.0 """
        return self.send_request("workspace/willCreateFiles", params)

    def will_rename_files(self,  params: lsp_types.RenameFilesParams) -> Request[Union['lsp_types.WorkspaceEdit', None]]:
        """ The will rename files request is sent from the client to the server before files are actually
        renamed as long as the rename is triggered from within the client.

        @since 3.16.0 """
        return self.send_request("workspace/willRenameFiles", params)

    def will_delete_files(self,  params: lsp_types.DeleteFilesParams) -> Request[Union['lsp_types.WorkspaceEdit', None]]:
        """ The did delete files notification is sent from the client to the server when
        files were deleted from within the client.

        @since 3.16.0 """
        return self.send_request("workspace/willDeleteFiles", params)

    def moniker(self,  params: lsp_types.MonikerParams) -> Request[Union[List['lsp_types.Moniker'], None]]:
        """ A request to get the moniker of a symbol at a given text document position.
        The request parameter is of type {@link TextDocumentPositionParams}.
        The response is of type {@link Moniker Moniker[]} or `null`. """
        return self.send_request("textDocument/moniker", params)

    def prepare_type_hierarchy(self,  params: lsp_types.TypeHierarchyPrepareParams) -> Request[Union[List['lsp_types.TypeHierarchyItem'], None]]:
        """ A request to result a `TypeHierarchyItem` in a document at a given position.
        Can be used as an input to a subtypes or supertypes type hierarchy.

        @since 3.17.0 """
        return self.send_request("textDocument/prepareTypeHierarchy", params)

    def type_hierarchy_supertypes(self,  params: lsp_types.TypeHierarchySupertypesParams) -> Request[Union[List['lsp_types.TypeHierarchyItem'], None]]:
        """ A request to resolve the supertypes for a given `TypeHierarchyItem`.

        @since 3.17.0 """
        return self.send_request("typeHierarchy/supertypes", params)

    def type_hierarchy_subtypes(self,  params: lsp_types.TypeHierarchySubtypesParams) -> Request[Union[List['lsp_types.TypeHierarchyItem'], None]]:
        """ A request to resolve the subtypes for a given `TypeHierarchyItem`.

        @since 3.17.0 """
        return self.send_request("typeHierarchy/subtypes", params)

    def inline_value(self,  params: lsp_types.InlineValueParams) -> Request[Union[List['lsp_types.InlineValue'], None]]:
        """ A request to provide inline values in a document. The request's parameter is of
        type {@link InlineValueParams}, the response is of type
        {@link InlineValue InlineValue[]} or a Thenable that resolves to such.

        @since 3.17.0 """
        return self.send_request("textDocument/inlineValue", params)

    def inlay_hint(self,  params: lsp_types.InlayHintParams) -> Request[Union[List['lsp_types.InlayHint'], None]]:
        """ A request to provide inlay hints in a document. The request's parameter is of
        type {@link InlayHintsParams}, the response is of type
        {@link InlayHint InlayHint[]} or a Thenable that resolves to such.

        @since 3.17.0 """
        return self.send_request("textDocument/inlayHint", params)

    def resolve_inlay_hint(self,  params: lsp_types.InlayHint) -> Request['lsp_types.InlayHint']:
        """ A request to resolve additional properties for an inlay hint.
        The request's parameter is of type {@link InlayHint}, the response is
        of type {@link InlayHint} or a Thenable that resolves to such.

        @since 3.17.0 """
        return self.send_request("inlayHint/resolve", params)

    def text_document_diagnostic(self,  params: lsp_types.DocumentDiagnosticParams) -> Request['lsp_types.DocumentDiagnosticReport']:
        """ The document diagnostic request definition.

        @since 3.17.0 """
        return self.send_request("textDocument/diagnostic", params)

    def workspace_diagnostic(self,  params: lsp_types.WorkspaceDiagnosticParams) -> Request['lsp_types.WorkspaceDiagnosticReport']:
        """ The workspace diagnostic request definition.

        @since 3.17.0 """
        return self.send_request("workspace/diagnostic", params)

    def inline_completion(self,  params: lsp_types.InlineCompletionParams) -> Request[Union['lsp_types.InlineCompletionList', List['lsp_types.InlineCompletionItem'], None]]:
        """ A request to provide inline completions in a document. The request's parameter is of
        type {@link InlineCompletionParams}, the response is of type
        {@link InlineCompletion InlineCompletion[]} or a Thenable that resolves to such.

        @since 3.18.0
        @proposed """
        return self.send_request("textDocument/inlineCompletion", params)

    def initialize(self,  params: lsp_types.InitializeParams) -> Request['lsp_types.InitializeResult']:
        """ The initialize request is sent from the client to the server.
        It is sent once as the request after starting up the server.
        The requests parameter is of type {@link InitializeParams}
        the response if of type {@link InitializeResult} of a Thenable that
        resolves to such. """
        return self.send_request("initialize", params)

    def shutdown(self) -> Request[None]:
        """ A shutdown request is sent from the client to the server.
        It is sent once when the client decides to shutdown the
        server. The only notification that is sent after a shutdown request
        is the exit event. """
        return self.send_request("shutdown")

    def will_save_wait_until(self,  params: lsp_types.WillSaveTextDocumentParams) -> Request[Union[List['lsp_types.TextEdit'], None]]:
        """ A document will save request is sent from the client to the server before
        the document is actually saved. The request can return an array of TextEdits
        which will be applied to the text document before it is saved. Please note that
        clients might drop results if computing the text edits took too long or if a
        server constantly fails on this request. This is done to keep the save fast and
        reliable. """
        return self.send_request("textDocument/willSaveWaitUntil", params)

    def completion(self,  params: lsp_types.CompletionParams) -> Request[Union[List['lsp_types.CompletionItem'], 'lsp_types.CompletionList', None]]:
        """ Request to request completion at a given text document position. The request's
        parameter is of type {@link TextDocumentPosition} the response
        is of type {@link CompletionItem CompletionItem[]} or {@link CompletionList}
        or a Thenable that resolves to such.

        The request can delay the computation of the {@link CompletionItem.detail `detail`}
        and {@link CompletionItem.documentation `documentation`} properties to the `completionItem/resolve`
        request. However, properties that are needed for the initial sorting and filtering, like `sortText`,
        `filterText`, `insertText`, and `textEdit`, must not be changed during resolve. """
        return self.send_request("textDocument/completion", params)

    def resolve_completion_item(self,  params: lsp_types.CompletionItem) -> Request['lsp_types.CompletionItem']:
        """ Request to resolve additional information for a given completion item.The request's
        parameter is of type {@link CompletionItem} the response
        is of type {@link CompletionItem} or a Thenable that resolves to such. """
        return self.send_request("completionItem/resolve", params)

    def hover(self,  params: lsp_types.HoverParams) -> Request[Union['lsp_types.Hover', None]]:
        """ Request to request hover information at a given text document position. The request's
        parameter is of type {@link TextDocumentPosition} the response is of
        type {@link Hover} or a Thenable that resolves to such. """
        return self.send_request("textDocument/hover", params)

    def signature_help(self,  params: lsp_types.SignatureHelpParams) -> Request[Union['lsp_types.SignatureHelp', None]]:
        return self.send_request("textDocument/signatureHelp", params)

    def definition(self,  params: lsp_types.DefinitionParams) -> Request[Union['lsp_types.Definition', List['lsp_types.LocationLink'], None]]:
        """ A request to resolve the definition location of a symbol at a given text
        document position. The request's parameter is of type {@link TextDocumentPosition}
        the response is of either type {@link Definition} or a typed array of
        {@link DefinitionLink} or a Thenable that resolves to such. """
        return self.send_request("textDocument/definition", params)

    def references(self,  params: lsp_types.ReferenceParams) -> Request[Union[List['lsp_types.Location'], None]]:
        """ A request to resolve project-wide references for the symbol denoted
        by the given text document position. The request's parameter is of
        type {@link ReferenceParams} the response is of type
        {@link Location Location[]} or a Thenable that resolves to such. """
        return self.send_request("textDocument/references", params)

    def document_highlight(self,  params: lsp_types.DocumentHighlightParams) -> Request[Union[List['lsp_types.DocumentHighlight'], None]]:
        """ Request to resolve a {@link DocumentHighlight} for a given
        text document position. The request's parameter is of type {@link TextDocumentPosition}
        the request response is an array of type {@link DocumentHighlight}
        or a Thenable that resolves to such. """
        return self.send_request("textDocument/documentHighlight", params)

    def document_symbol(self,  params: lsp_types.DocumentSymbolParams) -> Request[Union[List['lsp_types.SymbolInformation'], List['lsp_types.DocumentSymbol'], None]]:
        """ A request to list all symbols found in a given text document. The request's
        parameter is of type {@link TextDocumentIdentifier} the
        response is of type {@link SymbolInformation SymbolInformation[]} or a Thenable
        that resolves to such. """
        return self.send_request("textDocument/documentSymbol", params)

    def code_action(self,  params: lsp_types.CodeActionParams) -> Request[Union[List[Union['lsp_types.Command', 'lsp_types.CodeAction']], None]]:
        """ A request to provide commands for the given text document and range. """
        return self.send_request("textDocument/codeAction", params)

    def resolve_code_action(self,  params: lsp_types.CodeAction) -> Request['lsp_types.CodeAction']:
        """ Request to resolve additional information for a given code action.The request's
        parameter is of type {@link CodeAction} the response
        is of type {@link CodeAction} or a Thenable that resolves to such. """
        return self.send_request("codeAction/resolve", params)

    def workspace_symbol(self,  params: lsp_types.WorkspaceSymbolParams) -> Request[Union[List['lsp_types.SymbolInformation'], List['lsp_types.WorkspaceSymbol'], None]]:
        """ A request to list project-wide symbols matching the query string given
        by the {@link WorkspaceSymbolParams}. The response is
        of type {@link SymbolInformation SymbolInformation[]} or a Thenable that
        resolves to such.

        @since 3.17.0 - support for WorkspaceSymbol in the returned data. Clients
         need to advertise support for WorkspaceSymbols via the client capability
         `workspace.symbol.resolveSupport`.
 """
        return self.send_request("workspace/symbol", params)

    def resolve_workspace_symbol(self,  params: lsp_types.WorkspaceSymbol) -> Request['lsp_types.WorkspaceSymbol']:
        """ A request to resolve the range inside the workspace
        symbol's location.

        @since 3.17.0 """
        return self.send_request("workspaceSymbol/resolve", params)

    def code_lens(self,  params: lsp_types.CodeLensParams) -> Request[Union[List['lsp_types.CodeLens'], None]]:
        """ A request to provide code lens for the given text document. """
        return self.send_request("textDocument/codeLens", params)

    def resolve_code_lens(self,  params: lsp_types.CodeLens) -> Request['lsp_types.CodeLens']:
        """ A request to resolve a command for a given code lens. """
        return self.send_request("codeLens/resolve", params)

    def document_link(self,  params: lsp_types.DocumentLinkParams) -> Request[Union[List['lsp_types.DocumentLink'], None]]:
        """ A request to provide document links """
        return self.send_request("textDocument/documentLink", params)

    def resolve_document_link(self,  params: lsp_types.DocumentLink) -> Request['lsp_types.DocumentLink']:
        """ Request to resolve additional information for a given document link. The request's
        parameter is of type {@link DocumentLink} the response
        is of type {@link DocumentLink} or a Thenable that resolves to such. """
        return self.send_request("documentLink/resolve", params)

    def formatting(self,  params: lsp_types.DocumentFormattingParams) -> Request[Union[List['lsp_types.TextEdit'], None]]:
        """ A request to format a whole document. """
        return self.send_request("textDocument/formatting", params)

    def range_formatting(self,  params: lsp_types.DocumentRangeFormattingParams) -> Request[Union[List['lsp_types.TextEdit'], None]]:
        """ A request to format a range in a document. """
        return self.send_request("textDocument/rangeFormatting", params)

    def ranges_formatting(self,  params: lsp_types.DocumentRangesFormattingParams) -> Request[Union[List['lsp_types.TextEdit'], None]]:
        """ A request to format ranges in a document.

        @since 3.18.0
        @proposed """
        return self.send_request("textDocument/rangesFormatting", params)

    def on_type_formatting(self,  params: lsp_types.DocumentOnTypeFormattingParams) -> Request[Union[List['lsp_types.TextEdit'], None]]:
        """ A request to format a document on type. """
        return self.send_request("textDocument/onTypeFormatting", params)

    def rename(self,  params: lsp_types.RenameParams) -> Request[Union['lsp_types.WorkspaceEdit', None]]:
        """ A request to rename a symbol. """
        return self.send_request("textDocument/rename", params)

    def prepare_rename(self,  params: lsp_types.PrepareRenameParams) -> Request[Union['lsp_types.PrepareRenameResult', None]]:
        """ A request to test and perform the setup necessary for a rename.

        @since 3.16 - support for default behavior """
        return self.send_request("textDocument/prepareRename", params)

    def execute_command(self,  params: lsp_types.ExecuteCommandParams) -> Request[Union['lsp_types.LSPAny', None]]:
        """ A request send from the client to the server to execute a command. The request might return
        a workspace edit which the client will apply to the workspace. """
        return self.send_request("workspace/executeCommand", params)


class LspNotification:
    def __init__(self, send_notification):
        self.send_notification = send_notification

    def did_change_workspace_folders(self,  params: lsp_types.DidChangeWorkspaceFoldersParams) -> None:
        """ The `workspace/didChangeWorkspaceFolders` notification is sent from the client to the server when the workspace
        folder configuration changes. """
        return self.send_notification("workspace/didChangeWorkspaceFolders", params)

    def cancel_work_done_progress(self,  params: lsp_types.WorkDoneProgressCancelParams) -> None:
        """ The `window/workDoneProgress/cancel` notification is sent from  the client to the server to cancel a progress
        initiated on the server side. """
        return self.send_notification("window/workDoneProgress/cancel", params)

    def did_create_files(self,  params: lsp_types.CreateFilesParams) -> None:
        """ The did create files notification is sent from the client to the server when
        files were created from within the client.

        @since 3.16.0 """
        return self.send_notification("workspace/didCreateFiles", params)

    def did_rename_files(self,  params: lsp_types.RenameFilesParams) -> None:
        """ The did rename files notification is sent from the client to the server when
        files were renamed from within the client.

        @since 3.16.0 """
        return self.send_notification("workspace/didRenameFiles", params)

    def did_delete_files(self,  params: lsp_types.DeleteFilesParams) -> None:
        """ The will delete files request is sent from the client to the server before files are actually
        deleted as long as the deletion is triggered from within the client.

        @since 3.16.0 """
        return self.send_notification("workspace/didDeleteFiles", params)

    def did_open_notebook_document(self,  params: lsp_types.DidOpenNotebookDocumentParams) -> None:
        """ A notification sent when a notebook opens.

        @since 3.17.0 """
        return self.send_notification("notebookDocument/didOpen", params)

    def did_change_notebook_document(self,  params: lsp_types.DidChangeNotebookDocumentParams) -> None:
        return self.send_notification("notebookDocument/didChange", params)

    def did_save_notebook_document(self,  params: lsp_types.DidSaveNotebookDocumentParams) -> None:
        """ A notification sent when a notebook document is saved.

        @since 3.17.0 """
        return self.send_notification("notebookDocument/didSave", params)

    def did_close_notebook_document(self,  params: lsp_types.DidCloseNotebookDocumentParams) -> None:
        """ A notification sent when a notebook closes.

        @since 3.17.0 """
        return self.send_notification("notebookDocument/didClose", params)

    def initialized(self,  params: lsp_types.InitializedParams) -> None:
        """ The initialized notification is sent from the client to the
        server after the client is fully initialized and the server
        is allowed to send requests from the server to the client. """
        return self.send_notification("initialized", params)

    def exit(self) -> None:
        """ The exit event is sent from the client to the server to
        ask the server to exit its process. """
        return self.send_notification("exit")

    def workspace_did_change_configuration(self,  params: lsp_types.DidChangeConfigurationParams) -> None:
        """ The configuration change notification is sent from the client to the server
        when the client's configuration has changed. The notification contains
        the changed configuration as defined by the language client. """
        return self.send_notification("workspace/didChangeConfiguration", params)

    def did_open_text_document(self,  params: lsp_types.DidOpenTextDocumentParams) -> None:
        """ The document open notification is sent from the client to the server to signal
        newly opened text documents. The document's truth is now managed by the client
        and the server must not try to read the document's truth using the document's
        uri. Open in this sense means it is managed by the client. It doesn't necessarily
        mean that its content is presented in an editor. An open notification must not
        be sent more than once without a corresponding close notification send before.
        This means open and close notification must be balanced and the max open count
        is one. """
        return self.send_notification("textDocument/didOpen", params)

    def did_change_text_document(self,  params: lsp_types.DidChangeTextDocumentParams) -> None:
        """ The document change notification is sent from the client to the server to signal
        changes to a text document. """
        return self.send_notification("textDocument/didChange", params)

    def did_close_text_document(self,  params: lsp_types.DidCloseTextDocumentParams) -> None:
        """ The document close notification is sent from the client to the server when
        the document got closed in the client. The document's truth now exists where
        the document's uri points to (e.g. if the document's uri is a file uri the
        truth now exists on disk). As with the open notification the close notification
        is about managing the document's content. Receiving a close notification
        doesn't mean that the document was open in an editor before. A close
        notification requires a previous open notification to be sent. """
        return self.send_notification("textDocument/didClose", params)

    def did_save_text_document(self,  params: lsp_types.DidSaveTextDocumentParams) -> None:
        """ The document save notification is sent from the client to the server when
        the document got saved in the client. """
        return self.send_notification("textDocument/didSave", params)

    def will_save_text_document(self,  params: lsp_types.WillSaveTextDocumentParams) -> None:
        """ A document will save notification is sent from the client to the server before
        the document is actually saved. """
        return self.send_notification("textDocument/willSave", params)

    def did_change_watched_files(self,  params: lsp_types.DidChangeWatchedFilesParams) -> None:
        """ The watched files notification is sent from the client to the server when
        the client detects changes to file watched by the language client. """
        return self.send_notification("workspace/didChangeWatchedFiles", params)

    def set_trace(self,  params: lsp_types.SetTraceParams) -> None:
        return self.send_notification("$/setTrace", params)

    def cancel_request(self,  params: lsp_types.CancelParams) -> None:
        return self.send_notification("$/cancelRequest", params)

    def progress(self,  params: lsp_types.ProgressParams) -> None:
        return self.send_notification("$/progress", params)
