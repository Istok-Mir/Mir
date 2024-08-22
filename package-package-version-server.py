from .api import LanguageServer, register_language_server, unregister_language_server

server = LanguageServer('package-version-server', {
    'cmd': '/Users/predrag/Downloads/package-version-server',
    'activation_events': {
        'selector': 'source.json',
        'on_uri': ['file://**/package.json'],
    }
})


def plugin_loaded() -> None:
    register_language_server(server)


def plugin_unloaded() -> None:
    unregister_language_server(server)
