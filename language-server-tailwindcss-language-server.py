from Mir import LanguageServer

class TailwindcssLanguageServer(LanguageServer):
    name='tailwindcss'
    cmd='tailwindcss-language-server --stdio'
    activation_events={
        'selector': 'source.jsx | source.js.react | source.js | source.tsx | source.ts | source.css | source.scss | source.less | text.html.vue | text.html.svelte | text.html.basic | text.html.twig | text.blade | text.html.blade | embedding.php | text.html.rails | text.html.erb | text.haml | text.jinja | text.django | text.html.elixir | source.elixir | text.html.ngx | source.astro',
        'workspace_contains': ['**/tailwind.config.{ts,js,cjs,mjs}'],
    }
