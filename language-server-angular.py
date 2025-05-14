from __future__ import annotations
from Mir import LanguageServer
import sublime
import sys
import re
import os

class AngularLanguageServer(LanguageServer):
    name='angular'
    activation_events={
        'selector': 'text.html.ngx | source.ts | source.js',
    }
    async def activate(self):
        await self.connect('stdio', {
            'cmd': ['node', "/Users/predrag/Library/Caches/Sublime Text/Package Storage/LSP-angular/20.18.0/server/node_modules/@angular/language-server/index.js", "--logFile", "/Users/predrag/Library/Caches/Sublime Text/Package Storage/LSP-angular/20.18.0/server/node_modules/@angular/language-server/ngls.log",  "--ngProbeLocations", "/Users/predrag/Library/Caches/Sublime Text/Package Storage/LSP-angular/20.18.0/server/node_modules/@angular/language-server/node_modules", "--tsProbeLocations", "/Users/predrag/Library/Caches/Sublime Text/Package Storage/LSP-angular/20.18.0/server/node_modules/@angular/language-server/node_modules", "--stdio"]
        })

