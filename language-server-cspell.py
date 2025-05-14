from __future__ import annotations
import sublime_plugin
from Mir.types import URI, DocumentUri, TextEdit
from Mir import LanguageServer, mir
from typing import Dict, List, Optional, Tuple, TypedDict
from .runtime import deno

class CspellLanguageServer(LanguageServer):
    name='cSpell'
    activation_events={
        'selector': 'source.dosbatch | source.c | source.c++ | source.objc | source.objc++ | source.clojure | source.cs | source.cake | source.css | source.dart | source.diff | source.dockerfile | source.elixir | source.erlang | source.fsharp | text.git-commit | source.go | source.gomod | source.graphql | source.haskell | text.html.basic | source.ini | source.java | source.jsx | source.js.react | source.js | source.tsx | source.ts | source.json | source.julia | text.tex.latex | source.less | source.lua | source.makefile | text.html.markdown | source.perl | text.html.twig | text.blade | embedding.php | text.plain | source.powershell | source.python | source.r | source.ruby | source.rust | source.scala | source.scss | source.sql | source.swift | text.html.vue | text.xml | text.html.svelte | source.yml | source.yaml',
    }

    async def activate(self):
        await deno.setup()
        async def on_workspace_config_for_document(params: WorkspaceConfigForDocumentRequest) -> WorkspaceConfigForDocumentResponse:
            # It looks like this method is necessary to enable code actions...
            return {
                'uri': None,
                'workspaceFile': None,
                'workspaceFolder': None,
                'words': {},
                'ignoreWords': {}
            }
        self.on_request('onWorkspaceConfigForDocumentRequest', on_workspace_config_for_document)
        await self.connect('stdio', {
            'cmd': [deno.path, 'run', '-A', "/Users/predrag/Library/Caches/Sublime Text/Package Storage/LSP-cspell/20.18.0/language-server/_server/main.cjs", '--stdio'],
            'settings': {
                "cSpell.allowCompoundWords": False,
                "cSpell.allowedSchemas": [
                    "file",
                    "buffer"
                ],
                "cSpell.blockCheckingWhenLineLengthGreaterThan": 10000,
                "cSpell.blockCheckingWhenTextChunkSizeGreaterThan": 500,
                "cSpell.caseSensitive": False,
                "cSpell.checkLimit": 500,
                "cSpell.customDictionaries": {},
                "cSpell.diagnosticLevel": "Information",
                "cSpell.dictionaries": [],
                "cSpell.dictionaryDefinitions": [],
                "cSpell.enableFiletypes": [],
                "cSpell.enabled": True,
                "cSpell.enabledLanguageIds": [
                    "asciidoc",
                    "bat",
                    "c",
                    "clojure",
                    "coffeescript",
                    "cpp",
                    "csharp",
                    "css",
                    "dart",
                    "diff",
                    "dockerfile",
                    "elixir",
                    "erlang",
                    "fsharp",
                    "git-commit",
                    "git-rebase",
                    "github-actions-workflow",
                    "go",
                    "graphql",
                    "groovy",
                    "handlebars",
                    "haskell",
                    "html",
                    "ini",
                    "jade",
                    "java",
                    "javascript",
                    "javascriptreact",
                    "json",
                    "jsonc",
                    "julia",
                    "jupyter",
                    "latex",
                    "less",
                    "lua",
                    "makefile",
                    "markdown",
                    "objective-c",
                    "perl",
                    "perl6",
                    "php",
                    "plaintext",
                    "powershell",
                    "properties",
                    "pug",
                    "python",
                    "r",
                    "razor",
                    "restructuredtext",
                    "ruby",
                    "rust",
                    "scala",
                    "scminput",
                    "scss",
                    "shaderlab",
                    "shellscript",
                    "sql",
                    "swift",
                    "text",
                    "typescript",
                    "typescriptreact",
                    "vb",
                    "vue",
                    "xml",
                    "xsl",
                    "yaml"
                ],
                "cSpell.suggestWords": [],
                "cSpell.experimental.enableRegexpView": False,
                "cSpell.files": [],
                "cSpell.flagWords": [],
                "cSpell.globRoot": "",
                "cSpell.ignorePaths":[
                    "package-lock.json",
                    "node_modules",
                    "vscode-extension",
                    ".git/objects",
                    ".vscode",
                    ".vscode-insiders"
                ],
                "cSpell.ignoreRegExpList": [],
                "cSpell.ignoreWords": [],
                "cSpell.import": [],
                "cSpell.includeRegExpList": [],
                "cSpell.language": "en",
                "cSpell.languageSettings": [],
                "cSpell.logLevel": "Error",
                "cSpell.hideAddToDictionaryCodeActions": False,
                "cSpell.maxDuplicateProblems": 5,
                "cSpell.maxNumberOfProblems": 100,
                "cSpell.minWordLength": 4,
                "cSpell.noConfigSearch": False,
                "cSpell.noSuggestDictionaries": [],
                "cSpell.numSuggestions": 8,
                "cSpell.overrides": [],
                "cSpell.patterns": [],
                "cSpell.spellCheckDelayMs": 50,
                "cSpell.spellCheckOnlyWorkspaceFiles": False,
                "cSpell.suggestionNumChanges": 3,
                "cSpell.suggestionsTimeout": 400,
                "cSpell.useGitignore": True,
                "cSpell.usePnP": False,
                "cSpell.userWords": [],
                "cSpell.words": [],
                "cSpell.workspaceRootPath": ""
            }
        })


WorkspaceConfigForDocumentRequest = TypedDict('WorkspaceConfigForDocumentRequest', {
    'uri': DocumentUri
})

FieldExistsInTarget = Dict[str, bool]

WorkspaceConfigForDocumentResponse = TypedDict('WorkspaceConfigForDocumentResponse', {
    'uri': Optional[DocumentUri],
    'workspaceFile': Optional[URI],
    'workspaceFolder': Optional[URI],
    'words': FieldExistsInTarget,
    'ignoreWords': FieldExistsInTarget
})

DocumentVersion = int
EditTextArguments = Tuple[URI, DocumentVersion, List[TextEdit]]


mir.commands.register_command('cSpell.editText', 'cspell_edit_text')

class CspellEditTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, arguments: EditTextArguments): 
        _uri, document_version, text_edits = arguments
        self.view.run_command('mir_apply_text_edits', {
            'text_edits': text_edits
        })
