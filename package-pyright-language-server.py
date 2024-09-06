from .api import LanguageServer

class PyrightLanguageServer(LanguageServer):
    name='pyright-langserver'
    cmd='pyright-langserver --stdio'
    activation_events={
        'selector': 'source.python',
    }


def plugin_loaded() -> None:
    PyrightLanguageServer.setup()


def plugin_unloaded() -> None:
    PyrightLanguageServer.cleanup()
