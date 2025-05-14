from Mir import LanguageServer

class EslintLanguageServer(LanguageServer):
    name='eslint'
    activation_events={
        'selector': 'source.js, source.jsx, source.ts, source.tsx',
    }

    async def activate(self):
        await self.connect('stdio', {
            'cmd': ['node', "/Users/predrag/Library/Caches/Sublime Text/Package Storage/LSP-eslint/20.18.0/language-server/out/eslintServer.js", '--stdio'],
            'initialization_options': {'completionDisableFilterText': True, 'disableAutomaticTypingAcquisition': False, 'locale': 'en', 'maxTsServerMemory': 0, 'npmLocation': '', 'plugins': [], 'preferences': {'allowIncompleteCompletions': True, 'allowRenameOfImportPath': True, 'allowTextChangesInNewFiles': True, 'autoImportFileExcludePatterns': [], 'disableSuggestions': False, 'displayPartsForJSDoc': True, 'excludeLibrarySymbolsInNavTo': True, 'generateReturnInDocTemplate': True, 'importModuleSpecifierEnding': 'auto', 'importModuleSpecifierPreference': 'shortest', 'includeAutomaticOptionalChainCompletions': True, 'includeCompletionsForImportStatements': True, 'includeCompletionsForModuleExports': True, 'includeCompletionsWithClassMemberSnippets': True, 'includeCompletionsWithInsertText': True, 'includeCompletionsWithObjectLiteralMethodSnippets': True, 'includeCompletionsWithSnippetText': True, 'includePackageJsonAutoImports': 'auto', 'interactiveInlayHints': True, 'jsxAttributeCompletionStyle': 'auto', 'lazyConfiguredProjectsFromExternalProject': False, 'organizeImportsAccentCollation': True, 'organizeImportsCaseFirst': False, 'organizeImportsCollation': 'ordinal', 'organizeImportsCollationLocale': 'en', 'organizeImportsIgnoreCase': 'auto', 'organizeImportsNumericCollation': False, 'providePrefixAndSuffixTextForRename': True, 'provideRefactorNotApplicableReason': True, 'quotePreference': 'auto', 'useLabelDetailsInCompletionEntries': True}, 'tsserver': {'fallbackPath': '', 'logDirectory': '', 'logVerbosity': 'off', 'path': '', 'trace': 'off', 'useSyntaxServer': 'auto'}},
            'settings': {'codeAction': {'disableRuleComment': {'commentStyle': 'line', 'enable': True, 'location': 'separateLine'}, 'showDocumentation': {'enable': True}}, 'codeActionOnSave': {'enable': True, 'mode': 'all'}, 'format': False, 'ignoreUntitled': False, 'nodePath': None, 'onIgnoredFiles': 'off', 'options': {}, 'problems': {'shortenToSingleLine': False}, 'quiet': False, 'rulesCustomizations': [], 'run': 'onType', 'useESLintClass': False, 'validate': 'probe'}
        })
