from .api import LanguageServer

class BiomeLanguageServer(LanguageServer):
    name='biome'
    cmd='node "/Users/predrag/Library/Caches/Sublime Text/Package Storage/LSP-biome/20.18.0/language-server/node_modules/@biomejs/biome/bin/biome" lsp-proxy'
    activation_events={
        'selector': 'source.js | source.ts | source.jsx | source.tsx | source.js.jsx | source.js.react | source.ts.react | source.json | source.css | text.html.basic',
    }

    def on_settings_change(self):
        self.settings.update({"biome.lspBin": None, "biome.rename": None})

