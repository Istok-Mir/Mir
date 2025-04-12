from __future__ import annotations
import sublime
import uuid
import asyncio
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Mir.types import WorkspaceEdit

apply_edits_map: dict[uuid.UUID, asyncio.Future] = {}

async def apply_workspace_edit(view: sublime.View, workspace_edit: WorkspaceEdit):
    future = asyncio.Future()
    edit_id = str(uuid.uuid4())
    apply_edits_map[edit_id] = future
    view.run_command('mir_apply_workspace_edit', {
        'edit_id': edit_id,
        'workspace_edit': workspace_edit
    })
    return future


