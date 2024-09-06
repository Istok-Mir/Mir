from typing import TypedDict
from .api import LanguageServer

class VtslsLanguageServer(LanguageServer):
    name='vtsls'
    cmd='vtsls --stdio'
    activation_events={
        'selector': 'source.js, source.jsx, source.ts, source.tsx',
    }

    def before_initialize(self, server: LanguageServer):
        server.on_request('custom_request', custom_request_handler)
        server.on_notification('$/typescriptVersion', on_typescript_version)


def plugin_loaded() -> None:
    VtslsLanguageServer.setup()


def plugin_unloaded() -> None:
    VtslsLanguageServer.cleanup()


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

