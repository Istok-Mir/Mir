from Mir import LanguageServer

class BiomeLanguageServer(LanguageServer):
    name='biome'
    activation_events={
        'selector': 'source.js | source.ts | source.jsx | source.tsx | source.js.jsx | source.js.react | source.ts.react | source.json | source.css | text.html.basic',
    }

    async def activate(self):
        await self.connect('stdio', {
            'cmd': ['node', "/Users/predrag/Library/Caches/Sublime Text/Package Storage/LSP-biome/20.18.0/language-server/node_modules/@biomejs/biome/bin/biome", 'lsp-proxy'],
            'settings': {"biome.lspBin": None, "biome.rename": None}
        })

