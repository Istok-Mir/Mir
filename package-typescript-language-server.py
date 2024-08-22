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


def custom_notification_handler(params: SomeExample):
    print(params['name'])


server.on_request('custom_request', custom_request_handler)
server.on_notification('some_custom_notification', custom_notification_handler)


def plugin_loaded() -> None:
    register_language_server(server)


def plugin_unloaded() -> None:
    unregister_language_server(server)
