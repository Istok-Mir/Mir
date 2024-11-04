import sublime_plugin 
import sublime
import http.client
import json
import threading
import re
from pathlib import Path
import os

path_pattern = r"File:\s+/?(.+)"

code_pattern = r'```([\s|\w]+)'


class MirAiViewEventListenerCommand(sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings: sublime.Settings) -> bool:
        return settings.get('ai_chat')

    def on_hover(self, hover_point, hover_zone):
        window = self.view.window()
        if not window:
            return
        line_region = self.view.line(hover_point)
        line = self.view.substr(line_region)
        match = re.search(path_pattern, line)

        content = self.view.substr(self.view.find(code_pattern, line_region.end()))
        content = content.replace('```', '').strip()

        if match:
            filepath = Path(match.group(1))
            folders = window.folders() if window else []
            first_folder = Path(folders[0] if folders else '')
            full_path = first_folder.joinpath(filepath)
            exists = os.path.exists(full_path)
            self.view.show_popup(
                f"""<html style='box-sizing:border-box; background-color:var(--background); padding:0rem; margin:0'><body style='padding:0.3rem; margin:0; border-radius:4px; border: 1px solid color(var(--foreground) blend(var(--background) 20%));'><div style='padding: 0.0rem 0.2rem; font-size: 0.9rem;'><a style="text-decoration: none" href="{sublime.html_format_command('subl:mir_create_file', {'file_name': str(full_path), 'content': content})}">{'Goto File' if exists else 'Create File'}</a></div></body></html>""",
                sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY,
                hover_point,
                max_width=800,
            )
        print('hover', line)

class MirCreateFileCommand(sublime_plugin.TextCommand):
    def run(self, edit, file_name: str, content: str):
        w = self.view.window()
        if not w:
            return
        exists = os.path.exists(file_name)
        if exists:
            v = w.open_file(file_name)
            insert_into_first_column(w, v)
            return
        os.makedirs(str(Path(file_name).parent), exist_ok=True)
        with open(file_name, "w") as file:
            file.write(content)
        print('create file:', file_name)


class MirAiCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        w = self.view.window()
        if not w:
            return
        view = next(iter([v for v in w.views() if v.name() == 'Mir']), None)
        two_columns(w)
        if view is None:
            view = w.new_file()
            view.settings().set('ai_chat', True)
            view.set_name('Mir')
            view.set_scratch(True)
            view.settings().set('syntax', 'Packages/Markdown/Markdown.sublime-syntax')
        w.focus_view(view)
        insert_into_second_column(w, view)

class MirAiSubmitCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        end_point = get_point(self.view)
        if not end_point:
            return
        start_point = self.view.find('---', end_point, sublime.FindFlags.REVERSE)
        tasks_prompt = self.view.substr(sublime.Region(start_point.end(), end_point))
        final_prompt = prepared_prompt.format(tasks=tasks_prompt)
        t = threading.Thread(target=stream_response, args=(self.view,final_prompt))
        t.start()



        


def get_point(view: sublime.View):
    sel = view.sel()
    region = sel[0] if sel else None
    if region is None:
        return
    return region.b


def two_columns(window: sublime.Window) -> None:
    ''' Set two column layout. '''
    grid = {
            "cols": [0.0, 0.6, 1.0],
            "rows": [0.0, 1.0],
            "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
        }
    window.run_command('set_layout', grid)


def insert_into_first_column(window: sublime.Window, view: sublime.View) -> None:
    ''' Insert into first column a view. '''
    insert_into_column(window, 0, view)


def insert_into_second_column(window: sublime.Window, view: sublime.View) -> None:
    ''' Insert into second column a view. '''
    insert_into_column(window, 1, view)

def insert_into_column(window: sublime.Window, column: int, view: sublime.View) -> None:
    ''' Insert into a given column a view.
    Where column index starts at `0`. '''
    window.set_view_index(view, column, 0)



# Ollama server endpoint details
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
OLLAMA_PATH = "/api/generate"
OLLAMA_MODEL = "qwen2.5-coder"

def stream_response(view: sublime.View, prompt):
    connection = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT)
    headers = {
        "Content-Type": "application/json",
    }

    # Request payload as JSON string
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "options": {
            "stop": [],
        },
        "raw": True,
        "stream": True,
    })

    # Send POST request
    connection.request("POST", OLLAMA_PATH, body=payload, headers=headers)

    # Get response and ensure status is OK
    response = connection.getresponse()
    if response.status != 200:
        print("Failed to connect to Ollama API:", response.status)
        return

    # Read and decode the response in chunks
    text_result = ""
    view.run_command("append", {
        'characters': '\n\n',
        'force': False,
        'scroll_to_end': False
    })
    while True:
        # Read a chunk of data
        chunk = response.readline()
        
        # Break if no more data
        if not chunk:
            break

        # Decode and parse JSON response if chunk is not empty
        chunk_text = chunk.decode("utf-8").strip()
        if chunk_text:
            try:
                chunk_json = json.loads(chunk_text)
                text_chunk = chunk_json.get("response", "")
                text_result += text_chunk
                view.run_command("append", {
                    'characters': text_chunk,
                    'force': False,
                    'scroll_to_end': False
                })
            except json.JSONDecodeError:
                print("Failed to decode JSON chunk:", chunk_text)

    # Close the connection
    connection.close()
    view.run_command("append", {
        'characters': '\n---',
        'force': False,
        'scroll_to_end': True
    })

prepared_prompt = """
- Only answer the question, if you don't know, ask what info you need.
- **Output Requirements:** Return generated code in a code block with an appropriate file name. No explanations or comments.
- **ORM Setup:** Use Drizzle ORM to define PostgreSQL tables by default, avoiding direct SQL.
- **Always generate the least amount of code:** 
- **Schema Imports and Definitions:** Import `{{ createInsertSchema, createSelectSchema }}` from `"drizzle-zod"` and apply `createInsertSchema` and `createSelectSchema` to generate schemas.
- Example:
```typescript
import {{ uuid, pgTable, timestamp, boolean, text }} from "drizzle-orm/pg-core"

export const userTable = pgTable("user", {{}}
  id: uuid().primaryKey().defaultRandom(),
  createdAt: timestamp().defaultNow(),
  updatedAt: timestamp()
  .defaultNow()
  .$onUpdate(() => new Date()),
  isBlocked: boolean().default(false).notNull(),
  firstName: text().notNull(),
  lastName: text().notNull(),
  email: text().notNull(),
  emailVerified: boolean().default(false).notNull(),
  role: text().notNull().$type<Role>(),
}})

export const selectTableSchema = createSelectSchema(userTable)
export type User = z.infer<typeof selectTableSchema>

export const insertUserSchema = createInsertSchema(userTable)
export type UserInsert = z.infer<typeof insertUserSchema>
```
- In input and output, prefer using, the generated insertUserSchema or selectTableSchema when applicable, and use the zod schema `.pick` method on it to get the fields.
- **Make sure to call `assertPermission(can(permission))`** when implementing a CRUD usecase. Permission has the following shape `[create|read|update|delete]:[entity_name]:[own|all]?"`. For example `update:book`, `delete:book:own`
- **References in Tables:** Use Drizzle syntax for references with `references(() => targetTable.column, {{ onDelete: 'cascade' }})` format.
- Don't write sql column names in parents. Don't `id: integer('id')`. Do `id: integer()`
- **UseCase Requirements:**
- Use Zod and `useCase` from `"@/framework/router/UseCase"` to define use cases.
- Each `useCase` should include:
- `input`: Zod schema specifying input parameters.
- `output`: Zod schema specifying return structure.
- `run` function containing logic, using `tx` (transaction) for database operations when applicable.

- **UseCase Examples:** Below are minimal use case templates:
- **Basic UseCase Template:**
```typescript
import {{ assertPermission }} from "@/framework/security/Permissions"
import {{ useCase }} from "@/framework/router/UseCase"
import {{ z }} from 'zod'

export default useCase({{}}
  input: z.object({{}}}}),
  output: z.void(),
  async run() {{}}}}
}})
```
- **With Input:**
```typescript
import {{ assertPermission }} from "@/framework/security/Permissions"
import {{ useCase }} from "@/framework/router/UseCase"
import {{ z }} from 'zod'

export default useCase({{}}
  input: z.object({{}}
    search: z.string(),
    limit: z.coerce.number().default(10),
    offset: z.coerce.number().default(0),
  }}),
  output: z.void(),
  async run({{ input, can }}, tx) {{}}
    assertPermission(can("book:view:all"))
    // use input parameters
  }},
}})
```
- **Returning Data:**
```typescript
import {{ assertPermission }} from "@/framework/security/Permissions"
import {{ useCase }} from "@/framework/router/UseCase"
import {{ z }} from 'zod'

export default useCase({{}}
  input: z.object({{}}}}),
  output: z.object({{ message: z.string() }}),
  async run(_context, tx) {{}}
    return {{ message: 'Hello' }}
  }},
}})
```
- **Database Operations:**
- **Inserting:**
```typescript
import {{ assertPermission }} from "@/framework/security/Permissions"
import {{ useCase }} from "@/framework/router/UseCase"
import {{ z }} from 'zod'
import {{ noteTable }} from "@/db/schema/noteTable"

export default useCase({{}}
  input: z.object({{ note: z.string() }}),
  output: z.object({{ id: z.string() }}),
  async run({{ input, can }}, tx) {{}}
    assertPermission(can('create:note'))
    const [savedNote] = await tx.insert(noteTable).values({{ note: input.note }}).returning()
    return {{ id: savedNote.id }}
  }},
}})
```
- **Querying:** 
```typescript
import {{ assertPermission }} from "@/framework/security/Permissions"
import {{ useCase }} from "@/framework/router/UseCase"
import {{ z }} from 'zod'

export default useCase({{}}
  input: z.object({{ id: z.string() }}),
  output: z.object({{ id: z.string(), note: z.string() }}),
  async run({{ input, can }}, tx) {{}}
    assertPermission(can('view:note'))
    const note = await tx.query.noteTable.findFirst({{ where: eq(noteTable.id, input.id) }})
    return note
  }},
}})
```
- **Updating:**
```typescript
import {{ assertPermission }} from "@/framework/security/Permissions"
import {{ useCase }} from "@/framework/router/UseCase"
import {{ z }} from 'zod'

export default useCase({{}}
    input: z.object({{ id: z.string(), note: z.string() }}),
    output: z.void(),
    async run({{ input, can }}, tx) {{}}
      assertPermission(can('update:note:all'))
      // assertPermission(can('update:note:own'))
      await tx.update(noteTable).set({{ note: input.note }}).where(eq(noteTable.id, input.id))
    }},
}})
```
- **Deleting:**
  ```typescript
import {{ assertPermission }} from "@/framework/security/Permissions"
import {{ useCase }} from "@/framework/router/UseCase"
import {{ z }} from 'zod'

export default useCase({{}}
  input: z.object({{ id: z.string() }}),
  output: z.void(),
  async run({{ input, can }}, tx) {{}}
    assertPermission(can('delete:note:own'))
    await tx.delete(noteTable).where(eq(noteTable.id, input.id))
  }},
}})
```

- **Paginated Response Requirements:**
- Structure paginated responses using:
```typescript
output: z.object({{}}
  items: z.array(z.object({{ /* define fields here */ }})),
  totalCount: z.number(),
}})
```
- Use the exact `"items"` key name without modification.

- **Paginated Example:**
- Always name `limit` and `offset`, `limit` and `offset`. Use name `page` instead of `offset` when explicitly asked.
- Always use `items` and `totalCount` in the output when returning paginated items.
- **User List:**
```typescript
import {{ assertPermission }} from "@/framework/security/Permissions"
import {{ useCase }} from "@/framework/router/UseCase"
import {{ z }} from 'zod'
import {{ userTable }} from "@/db/schema/userTable"
import {{ and, eq, or, asc, desc }} from "drizzle-orm"
import {{ createSearchArray, ILikeAnyArray }} from "@/framework/utils/ILikeAnyArray"

export default useCase({{}}
  input: z.object({{}}
    search: z.string().default(""),
    limit: z.coerce.number().default(10),
    offset: z.coerce.number().default(0),
  }}),
  output: z.object({{}}
    items: z.array(
      z.object({{}}
        id: z.string(),
        firstName: z.string(),
        lastName: z.string(),
        email: z.string(),
        isBlocked: z.boolean(),
      }}),
    ),
    totalCount: z.number(),
  }}),
  async run({{ input, can }}, tx) {{}}
    assertPermission(can('view:admins'))
    const whereOptions = and(
      eq(userTable.role, 'admin'),
      or(
        ILikeAnyArray(userTable.firstName, createSearchArray(input.search)),
        ILikeAnyArray(userTable.lastName, createSearchArray(input.search)),
        ILikeAnyArray(userTable.email, createSearchArray(input.search))
      )
    )
    const [adminUsers, totalCount] = await Promise.all([
      tx.query.userTable.findMany({{}}
        where: whereOptions,
        orderBy: [asc(userTable.isBlocked), desc(userTable.firstName)],
        offset: input.offset,
        limit: input.limit,
      }}),
      tx.$count(userTable, whereOptions)
    ])

    return {{ items: adminUsers, totalCount }}
  }},
}})
```

# List of Task:
{tasks}
- **Skip code block generation if not asked to create!**
- **Only generate what was asked for**
- Group this code change like. 

File: server/src/db/schema/bookTable.ts
```typescript
// generated cide
```

File: server/src/usecase/book/createBook.ts
```typescript
// put code here
```

File: server/src/usecase/book/updateBook.ts
```typescript
// put code here
```

File: server/src/usecase/book/getBook.ts
```typescript
// put code here
```

File: server/src/usecase/book/getBooks.ts
```typescript
// put code here
```

File: server/src/usecase/book/deleteBooks.ts
```typescript
// put code here
```

DON'T group code changes like this:
```typescript
// File: server/src/usecase/book/deleteBooks.ts
// put code here
```
Instead do
// File: server/src/usecase/book/deleteBooks.ts
```typescript
// put code here
```

# Solution For Given Tasks:

Here is the generated code for the tasks grouped by file names:
"""
