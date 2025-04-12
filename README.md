Simply, don't use it now:
- Mir API will change without notice, the features that it exposes will change or be removed without notice, it is experimental not stable and not usable for most people (except for the one developer working on this).
- Registering/unregistering capabilities is not implemented properly.
- Windows and Linux is not tested and probably doesn't work.
- It has some code that it should not have, for example ai.py.
- `language-server-*.py` files should not be part of this repo.
- the commit messages will most likely be gibberish `'asd'` and will stay that way until things start to become serious.

Don't forget the LSP package for Sublime Text works. 
If you like something from Mir move it just to LSP.

The only thing that this code can give are ideas.

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
from Mir import mir
import sublime
import sublime_aio


class MirCompletionListener(sublime_aio.ViewEventListener):
    async def on_query_completions(self, _prefix: str, locations: list[Point]):
        completion_list = sublime.CompletionList()
        results = await mir.completions(self.view, point)
        completions: list[sublime.CompletionValue] = []
        for name, result in results:
            if isinstance(result, dict):
                items = result['items']
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
            elif isinstance(result, list):
                items = result
                for i in items:
                    completions.append(sublime.CompletionItem(i['label']))
        completion_list.set_completions(completions, sublime.INHIBIT_WORD_COMPLETIONS)
        return completion_list
```
See `Mir/package-implemenation-*.py` files for examples.

---

Example of a language server for Mir:
```py
from Mir import LanguageServer

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

Hover provider example:
```py
# this is just a concept
from Mir import HoverProvider, mir
from Mir.types import Hover, MarkupKind, Diagnostic
from Mir.api import range_to_region
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

Completion provider example:
```py
from __future__ import annotations
from Mir import CompletionProvider
from Mir.types import CompletionItem, CompletionList


class ExampleCompletionProvider(CompletionProvider):
    name='HellooCompletionsGoodbyeMyTime'
    activation_events={
        'selector': 'source.js'
    }

    async def provide_completion_items(self, view, prefix, locations) -> list[CompletionItem] | CompletionList | None:
        return [{
            'label': 'Helloo',
        }]
```

See `Mir/package-provider-*.py` files for examples.
