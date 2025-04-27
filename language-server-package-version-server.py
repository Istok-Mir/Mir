from Mir import LanguageServer

class PackageVersionServer(LanguageServer):
    name='package-version-server'
    cmd=['/Users/predrag/Downloads/package-version-server']
    activation_events={
        'selector': 'source.json',
        'on_uri': ['file://**/package.json'],
    }
