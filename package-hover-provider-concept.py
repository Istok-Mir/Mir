# this is just a concept
from .api.types import Hover, MarkupKind
from .api import HoverProvider
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


def plugin_loaded() -> None:
    ExampleHoverProvider.setup()


def plugin_unloaded() -> None:
    ExampleHoverProvider.cleanup()
