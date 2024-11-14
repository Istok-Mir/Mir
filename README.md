# Mir

Mir is a Sublime Text package that speaks the LSP language but provides more on top of that.

What is Mir?

Mir collects data from "Langauge Servers" and from "Providers" pacakges.

```py
# To read the data that Mir collected
completions = await mir.completions(self.view, point)
hovers = await mir.hover(self.view, hover_point)
definitions = await mir.definitions(self.view, point)
```

Example completion package implementation:
```py
from __future__ import annotations
import sublime
import sublime_plugin
from .api import mir, run_future

class MirCompletionListener(sublime_plugin.ViewEventListener):
    def on_query_completions(self, _prefix: str, locations: list[Point]):
        completion_list = sublime.CompletionList()
        run_future(self.do_completions(completion_list, locations[0]))
        return completion_list

    async def do_completions(self, completion_list: sublime.CompletionList, point: int):
        completions_results = await mir.completions(self.view, point)
        completions: list[sublime.CompletionValue] = []
        for name, result in completions_results:
            if isinstance(result, dict):
                items = result['items']
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
            elif isinstance(result, list):
                items = result
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
        completion_list.set_completions(completions, sublime.INHIBIT_WORD_COMPLETIONS)
```
See `Mir/package-implemenation-*.py` files for examples.

---

Example of a language server for Mir:
```py
from .api import LanguageServer

class PackageVersionServer(LanguageServer):
    name='package-version-server'
    cmd='/Users/predrag/Downloads/package-version-server'
    activation_events={
        'selector': 'source.json',
        'on_uri': ['file://**/package.json'],
    }

```
See `Mir/package-language-server-*.py` files for examples.

---

Language servers are not the only way to provide data to Mir.
Provider packages can be written to enhance mir.

```py
# this is just a concept
from .api.types import Hover, MarkupKind, Diagnostic
from .api import HoverProvider, mir
from .api.helpers import range_to_region
import sublime

class ExampleHoverProvider(HoverProvider):
    name= 'Package Json Enhancer'
    activation_events = {
        'selector': 'source.json',
        'on_uri': ['file://**/package.json'],
    }
    async def provide_hover(self, view: sublime.View, hover_point: int, hover_zone: sublime.HoverZone) -> Hover:
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
          'contents': ['Hover Content']
        }

```

See `Mir/package-provider-*.py` files for examples.


---

Features:
- registering/unregistering capabilities
- request cancelling
- logs in panel

Open the example.js file and trigger the autocomplete.
