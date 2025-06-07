from __future__ import annotations
from .maintainers.clone_projects import CloneMirProjectsCommand, OpenMirProjectsCommand
from .libs.lsp.manage_servers import ManageServers
from .libs.lsp.text_change_listener import MirTextChangeListener
from .libs.lsp.providers import callbacks_when_ready
from .libs.lsp.server import server_callbacks_when_ready
from Mir import mir_logger
mir_logger.debug('hello')

def plugin_loaded():
    [cb() for cb in callbacks_when_ready]
    [cb() for cb in server_callbacks_when_ready]
