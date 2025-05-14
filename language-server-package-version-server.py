from Mir import LanguageServer

class PackageVersionServer(LanguageServer):
    name='package-version-server'
    activation_events={
        'selector': 'source.json',
        'on_uri': ['file://**/package.json'],
    }

    async def activate(self):
        await self.connect('stdio', {
            'cmd': ['/Users/predrag/Downloads/package-version-server']
        })
