# this is just a concept
from lsp.types import Hover, MarkupKind
from .api import register_provider, unregister_provider, HoverProvider
import sublime

class ExampleHoverProvider(HoverProvider):
    name= 'Package Json Enhancer'
    activation_events = {
        'selector': 'source.json',
        'on_uri': ['file://**/package.json'],
    }
    async def provide_hover(self, view: sublime.View, hover_point: int) -> Hover:
        if hover_point % 2 == 0:
            return {
            'contents': {
                'kind': MarkupKind.Markdown,
                'value': '\n'.join([
                    '# Header',
                    f'Some text {view.file_name()}',
                    '```typescript',
                    'someCode();',
                    '```',
                    'Or this:',
                    '```diff',
                    '- someCode();',
                    '+ someCodeAsd();',
                    '// some comment',
                    '```'
                 ])
            }
        }
        return {
          'contents': ['Hover Content ']
        }

example_hover_provider = ExampleHoverProvider()


def plugin_loaded() -> None:
    register_provider(example_hover_provider)


def plugin_unloaded() -> None:
    unregister_provider(example_hover_provider)
