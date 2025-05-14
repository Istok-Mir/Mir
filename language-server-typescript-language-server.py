from typing import TypedDict
from Mir import LanguageServer
import sublime
from .runtime import deno
from .package_storage import PackageStorage, run_command_sync


server_storage = PackageStorage(__package__, tag='0.0.2', sync_folder="./language-server")
server_path = server_storage / "language-server" / 'node_modules' / 'typescript-language-server' / 'lib' / 'cli.mjs'
if not server_path.exists():
    run_command_sync([deno.path, "install"], cwd=str(server_storage / "language-server"))

class VtslsLanguageServer(LanguageServer):
    name='vtsls'
    cmd=[deno.path, 'run', '-A', server_path, '--stdio']
    activation_events={
        'selector': 'source.js, source.jsx, source.ts, source.tsx',
    }

    def before_initialize(self):
        self.initialization_options.assign({'completionDisableFilterText': True, 'disableAutomaticTypingAcquisition': False, 'locale': 'en', 'maxTsServerMemory': 0, 'npmLocation': '', 'plugins': [], 'preferences': {'allowIncompleteCompletions': True, 'allowRenameOfImportPath': True, 'allowTextChangesInNewFiles': True, 'autoImportFileExcludePatterns': [], 'disableSuggestions': False, 'displayPartsForJSDoc': True, 'excludeLibrarySymbolsInNavTo': True, 'generateReturnInDocTemplate': True, 'importModuleSpecifierEnding': 'auto', 'importModuleSpecifierPreference': 'shortest', 'includeAutomaticOptionalChainCompletions': True, 'includeCompletionsForImportStatements': True, 'includeCompletionsForModuleExports': True, 'includeCompletionsWithClassMemberSnippets': True, 'includeCompletionsWithInsertText': True, 'includeCompletionsWithObjectLiteralMethodSnippets': True, 'includeCompletionsWithSnippetText': True, 'includePackageJsonAutoImports': 'auto', 'interactiveInlayHints': True, 'jsxAttributeCompletionStyle': 'auto', 'lazyConfiguredProjectsFromExternalProject': False, 'organizeImportsAccentCollation': True, 'organizeImportsCaseFirst': False, 'organizeImportsCollation': 'ordinal', 'organizeImportsCollationLocale': 'en', 'organizeImportsIgnoreCase': 'auto', 'organizeImportsNumericCollation': False, 'providePrefixAndSuffixTextForRename': True, 'provideRefactorNotApplicableReason': True, 'quotePreference': 'auto', 'useLabelDetailsInCompletionEntries': True}, 'tsserver': {'fallbackPath': '', 'logDirectory': '', 'logVerbosity': 'off', 'path': '', 'trace': 'off', 'useSyntaxServer': 'auto'}})
        self.on_request('custom_request', custom_request_handler)
        self.on_notification('$/typescriptVersion', on_typescript_version)


class SomeExample(TypedDict):
    name: str
    age: int

def custom_request_handler(params: SomeExample):
    print(params['name'])

class TypescriptVersionParams(TypedDict):
    source: str
    version: str

def on_typescript_version(params: TypescriptVersionParams):
    sublime.status_message(params['source'] + f"({params['version']})")

