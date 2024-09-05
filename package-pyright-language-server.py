from .api import LanguageServer, register_language_server, unregister_language_server

server = LanguageServer('pyright-langserver', {
    'cmd':'pyright-langserver --stdio',
    'activation_events': {
        'selector': 'source.python'
    }
})

def plugin_loaded() -> None:
    register_language_server(server)


def plugin_unloaded() -> None:
    unregister_language_server(server)
