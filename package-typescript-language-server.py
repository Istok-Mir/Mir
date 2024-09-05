from typing import TypedDict
from .api import LanguageServer, register_language_server, unregister_language_server

server = LanguageServer('typescript-language-server', {
    'cmd':'typescript-language-server --stdio',
    'activation_events': {
        'selector': 'source.js, source.jsx, source.ts, source.tsx'
    }
})

class SomeExample(TypedDict):
    name: str
    age: int

def custom_request_handler(params: SomeExample):
    print(params['name'])

class TypescriptVersionParams(TypedDict):
    source: str
    version: str

def on_typescript_version(params: TypescriptVersionParams):
    print(params['source'] + f"({params['version']})")


server.on_request('custom_request', custom_request_handler)
server.on_notification('$/typescriptVersion', on_typescript_version)


def plugin_loaded() -> None:
    register_language_server(server)


def plugin_unloaded() -> None:
    unregister_language_server(server)
