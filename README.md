# ZENit

Zenit is a Sublime Text package that implements LSP.
Features:
- registering/unregistering capabilities
- request cancelling
- hover
- completions
- logs in panel
- people can create **language server packages**: see package-package-version-server.py, package-typescript-language-server.py, package-tailwindcss-language-server.py
- people can create **Provider packages**. Provider packages can hook into Zenit and provide additional data. see  package-hover-provider-concept.py

Make sure to have "typescript-language-server" globaly installed (https://github.com/typescript-language-server/typescript-language-server).

Open the example.js file and trigger the autocomplete.
