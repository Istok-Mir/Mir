from .api import LanguageServer

class EslintLanguageServer(LanguageServer):
    name='eslint'
    cmd='node "/Users/predrag/Library/Application Support/Sublime Text/Packages/LSP-eslint/language-server/out/eslintServer.js" --stdio'
    activation_events={
        'selector': 'source.js, source.jsx, source.ts, source.tsx',
    }

    # def before_initialize(self):
    #     self.initialization_options.assign({'completionDisableFilterText': True, 'disableAutomaticTypingAcquisition': False, 'locale': 'en', 'maxTsServerMemory': 0, 'npmLocation': '', 'plugins': [], 'preferences': {'allowIncompleteCompletions': True, 'allowRenameOfImportPath': True, 'allowTextChangesInNewFiles': True, 'autoImportFileExcludePatterns': [], 'disableSuggestions': False, 'displayPartsForJSDoc': True, 'excludeLibrarySymbolsInNavTo': True, 'generateReturnInDocTemplate': True, 'importModuleSpecifierEnding': 'auto', 'importModuleSpecifierPreference': 'shortest', 'includeAutomaticOptionalChainCompletions': True, 'includeCompletionsForImportStatements': True, 'includeCompletionsForModuleExports': True, 'includeCompletionsWithClassMemberSnippets': True, 'includeCompletionsWithInsertText': True, 'includeCompletionsWithObjectLiteralMethodSnippets': True, 'includeCompletionsWithSnippetText': True, 'includePackageJsonAutoImports': 'auto', 'interactiveInlayHints': True, 'jsxAttributeCompletionStyle': 'auto', 'lazyConfiguredProjectsFromExternalProject': False, 'organizeImportsAccentCollation': True, 'organizeImportsCaseFirst': False, 'organizeImportsCollation': 'ordinal', 'organizeImportsCollationLocale': 'en', 'organizeImportsIgnoreCase': 'auto', 'organizeImportsNumericCollation': False, 'providePrefixAndSuffixTextForRename': True, 'provideRefactorNotApplicableReason': True, 'quotePreference': 'auto', 'useLabelDetailsInCompletionEntries': True}, 'tsserver': {'fallbackPath': '', 'logDirectory': '', 'logVerbosity': 'off', 'path': '', 'trace': 'off', 'useSyntaxServer': 'auto'}})
    def on_settings_change(self):
        self.settings.update({'codeAction': {'disableRuleComment': {'commentStyle': 'line', 'enable': True, 'location': 'separateLine'}, 'showDocumentation': {'enable': True}}, 'codeActionOnSave': {'enable': True, 'mode': 'all'}, 'format': False, 'ignoreUntitled': False, 'nodePath': None, 'onIgnoredFiles': 'off', 'options': {}, 'problems': {'shortenToSingleLine': False}, 'quiet': False, 'rulesCustomizations': [], 'run': 'onType', 'useESLintClass': False, 'validate': 'probe'}) # 'workspaceFolder': {'name': 'bejst', 'uri': 'file:///Users/predrag/Downloads/bejst'}

def plugin_loaded() -> None:
    EslintLanguageServer.setup()


def plugin_unloaded() -> None:
    EslintLanguageServer.cleanup()
