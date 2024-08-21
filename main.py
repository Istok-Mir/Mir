from __future__ import annotations
import asyncio
import os
from re import sub

from event_loop import run_future
from lsp.server import LanguageServer, OnRequestPayload
from lsp.types import CompletionParams, HoverParams, RegistrationParams
from lsp.capabilities import client_capabilities, method_to_capability
import sublime
from html import escape

import sublime_plugin
from sublime_types import Point

servers: list[LanguageServer] = []

async def main():
    global servers
    ts_ls = LanguageServer('typescript-language-server --stdio')
    await ts_ls.start()
    servers.append(ts_ls)
    tailwind_ls = LanguageServer('tailwindcss-language-server --stdio')
    await tailwind_ls.start()
    servers.append(tailwind_ls)

    def on_log_message(payload: OnRequestPayload):
        print('log:', payload)

    async def workspace_configuration(payload: OnRequestPayload):
        return []

    async def register_capability(payload: OnRequestPayload[RegistrationParams]):
        params = payload.params
        registrations = params["registrations"]
        for registration in registrations:
            capability_path = method_to_capability(registration["method"])
            options = registration.get("registerOptions")
            if not isinstance(options, dict):
                options = {}
            payload.server.capabilities.register(capability_path, options)

    for s in servers:
        s.on_request('workspace/configuration', workspace_configuration)
        s.on_request('client/registerCapability', register_capability)
        s.on_notification('window/logMessage', on_log_message)

    folders = sublime.active_window().folders()
    root_folder = folders[0] if folders else ''
    result = await ts_ls.send.initialize({
        'processId': os.getpid(),
        'rootUri': 'file://' + root_folder,
        'rootPath': root_folder,
        'workspaceFolders': [{'name': 'OLSP', 'uri': 'file://' + root_folder}],
        'capabilities': client_capabilities,
        'initializationOptions': {'completionDisableFilterText': True, 'disableAutomaticTypingAcquisition': False, 'locale': 'en', 'maxTsServerMemory': 0, 'npmLocation': '', 'plugins': [], 'preferences': {'allowIncompleteCompletions': True, 'allowRenameOfImportPath': True, 'allowTextChangesInNewFiles': True, 'autoImportFileExcludePatterns': [], 'disableSuggestions': False, 'displayPartsForJSDoc': True, 'excludeLibrarySymbolsInNavTo': True, 'generateReturnInDocTemplate': True, 'importModuleSpecifierEnding': 'auto', 'importModuleSpecifierPreference': 'shortest', 'includeAutomaticOptionalChainCompletions': True, 'includeCompletionsForImportStatements': True, 'includeCompletionsForModuleExports': True, 'includeCompletionsWithClassMemberSnippets': True, 'includeCompletionsWithInsertText': True, 'includeCompletionsWithObjectLiteralMethodSnippets': True, 'includeCompletionsWithSnippetText': True, 'includePackageJsonAutoImports': 'auto', 'interactiveInlayHints': True, 'jsxAttributeCompletionStyle': 'auto', 'lazyConfiguredProjectsFromExternalProject': False, 'organizeImportsAccentCollation': True, 'organizeImportsCaseFirst': False, 'organizeImportsCollation': 'ordinal', 'organizeImportsCollationLocale': 'en', 'organizeImportsIgnoreCase': 'auto', 'organizeImportsNumericCollation': False, 'providePrefixAndSuffixTextForRename': True, 'provideRefactorNotApplicableReason': True, 'quotePreference': 'auto', 'useLabelDetailsInCompletionEntries': True}, 'tsserver': {'fallbackPath': '', 'logDirectory': '', 'logVerbosity': 'off', 'path': '', 'trace': 'off', 'useSyntaxServer': 'auto'}}
    })
    ts_ls.notify.initialized({})
    ts_ls.capabilities.assign(result['capabilities'])
    result2 =await tailwind_ls.send.initialize({
        'processId': os.getpid(),
        'rootUri': 'file://' + root_folder,
        'rootPath': root_folder,
        'workspaceFolders': [{'name': 'OLSP', 'uri': 'file://' + root_folder}],
        'capabilities': client_capabilities,
        'initializationOptions': {},
    })
    tailwind_ls.capabilities.assign(result2['capabilities'])
    tailwind_ls.notify.initialized({})
    tailwind_ls.notify.workspace_did_change_configuration({'settings': {'tailwindCSS': {'classAttributes': ['class', 'className', 'ngClass'], 'colorDecorators': True, 'emmetCompletions': False, 'experimental': {'classRegex': []}, 'files': {'exclude': ['**/.git/**', '**/node_modules/**', '**/.hg/**']}, 'includeLanguages': {'elixir': 'html'}, 'lint': {'cssConflict': 'warning', 'invalidApply': 'error', 'invalidConfigPath': 'error', 'invalidScreen': 'error', 'invalidTailwindDirective': 'error', 'invalidVariant': 'error', 'recommendedVariantOrder': 'warning'}, 'rootFontSize': 16, 'showPixelEquivalents': True, 'validate': True}}})

def plugin_loaded() -> None:
    run_future(main())

class DocumentListener3(sublime_plugin.EventListener):
    def on_exit(self):
        global servers
        for server in servers:
            server.stop()

class DocumentListener(sublime_plugin.ViewEventListener):
    def on_load(self):
        file_name = self.view.file_name()
        if not file_name:
            return
        for server in servers:
            server.notify.did_open_text_document({
                'textDocument': {
                    'version': self.view.change_count(),
                    'languageId': 'typescriptreact',
                    'text': self.view.substr(sublime.Region(0, self.view.size())),
                    'uri': 'file://' + file_name
                }
            })

    def on_close(self):
        file_name = self.view.file_name()
        if not file_name:
            return
        for server in servers:
            server.notify.did_close_text_document({
                'textDocument': {
                    'uri': 'file://' + file_name
                }
            })

    def on_query_completions(self, _prefix: str, locations: list[Point]):
        completion_list = sublime.CompletionList()
        file_name = self.view.file_name()
        if not file_name:
            return
        row, col = self.view.rowcol(locations[0])
        params: CompletionParams = {
            'position': {'line': row, 'character': col},
            'textDocument': {
                'uri': 'file://' + file_name
            }
        }
        run_future(self.do_completions(completion_list, params))
        return completion_list

    def on_hover(self, point, hover_zone):
        if hover_zone == 1:
            file_name = self.view.file_name()
            if not file_name:
                return
            row, col = self.view.rowcol(point)
            run_future(self.do_hover({
                'position': { 'line': row,'character': col },
                'textDocument': {
                    'uri': 'file://' + file_name
                },
            }, point))

    async def do_hover(self, params: HoverParams, hover_point):
        for server in servers:
            res = None
            try:
                res = await server.send.hover(params)
            except Exception as e:
                print('HoverError:', e)
            if isinstance(res, dict):
                content = res['contents']
                if isinstance(content, dict) and 'value' in content:
                    self.view.show_popup(
                        "<pre style='white-space: pre'>"+escape(content['value']).replace('\n', '<br>')+"</pre>",
                        sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                        hover_point,
                        max_width=1200,
                    )

    async def do_completions(self, completion_list: sublime.CompletionList, params: CompletionParams):
        completions: list[sublime.CompletionValue] = []
        for server in servers:
            if not server.capabilities.has('completionProvider'):
                continue
            server.notify.did_change_text_document({
                'textDocument': {
                    'uri': params['textDocument']['uri'],
                    'version': self.view.change_count()
                },
                'contentChanges': [{
                    'text': self.view.substr(sublime.Region(0, self.view.size()))
                }]
            })
            res=None
            try:
                res = await server.send.completion(params)
            except Exception as e:
                print('CompletionError:', e)
            if isinstance(res, dict):
                items = res['items']
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
        completion_list.set_completions(completions, sublime.INHIBIT_WORD_COMPLETIONS)
