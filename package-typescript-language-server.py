from typing import TypedDict
from .api import LanguageServer
import sublime

class VtslsLanguageServer(LanguageServer):
    name='vtsls'
    # cmd='vtsls --stdio'
    cmd='typescript-language-server --stdio'
    activation_events={
        'selector': 'source.js, source.jsx, source.ts, source.tsx',
    }

    def before_initialize(self):
        self.on_request('custom_request', custom_request_handler)
        self.on_notification('$/typescriptVersion', on_typescript_version)


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
    sublime.status_message(params['source'] + f"({params['version']})")

