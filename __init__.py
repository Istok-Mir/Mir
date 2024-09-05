# typing_extensions hack
import sublime_plugin

# setup event loop
from .libs.event_loop import setup_event_loop, shutdown_event_loop

setup_event_loop()

class EventListener(sublime_plugin.EventListener):
    def on_exit(self) -> None:
        shutdown_event_loop()
# end of setup event loop
