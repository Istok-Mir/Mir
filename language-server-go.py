from Mir import LanguageServer

class GoplsLanguageServer(LanguageServer):
    name='gopls'
    activation_events={
        'selector': 'source.go',
    }

    async def activate(self):
        await self.connect('stdio', {
            'cmd': ["/Users/predrag/Library/Caches/Sublime\ Text/Package\ Storage/LSP-gopls/bin/gopls"],
            'settings': {
                "manageGoplsBinary": True,
                "closeTestResultsWhenFinished": False,
                "runTestsInPanel": True,
                "gopls.buildFlags": [],
                "gopls.env": {},
                "gopls.directoryFilters": [
                  "-**/node_modules"
                ],
                "gopls.templateExtensions": [],
                "gopls.memoryMode": "",
                "gopls.expandWorkspaceToModule": True,
                "gopls.standaloneTags": [
                  "ignore"
                ],
                "gopls.hoverKind": "FullDocumentation",
                "gopls.linkTarget": "pkg.go.dev",
                "gopls.linksInHover": True,
                "gopls.usePlaceholders": False,
                "gopls.completionBudget": "100ms",
                "gopls.matcher": "Fuzzy",
                "gopls.experimentalPostfixCompletions": True,
                "gopls.completeFunctionCalls": True,
                "gopls.importShortcut": "Both",
                "gopls.symbolMatcher": "FastFuzzy",
                "gopls.symbolStyle": "Dynamic",
                "gopls.symbolScope": "all",
                "gopls.analyses": {},
                "gopls.staticcheck": False,
                "gopls.annotations": {
                  "bounds": True,
                  "escape": True,
                  "inline": True,
                  "nil": True
                },
                "gopls.vulncheck": "Off",
                "gopls.diagnosticsDelay": "1s",
                "gopls.diagnosticsTrigger": "Edit",
                "gopls.analysisProgressReporting": True,
                "gopls.hints": {},
                "gopls.codelenses": {
                  "gc_details": False,
                  "generate": True,
                  "regenerate_cgo": True,
                  "run_govulncheck": False,
                  "tidy": True,
                  "upgrade_dependency": True,
                  "vendor": True
                },
                "gopls.semanticTokens": False,
                "gopls.noSemanticString": False,
                "gopls.noSemanticNumber": False,
                "gopls.local": "",
                "gopls.gofumpt": False,
                "gopls.verboseOutput": False,
            }
        })



