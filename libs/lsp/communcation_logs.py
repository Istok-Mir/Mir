import datetime
from typing import Any
from sublime_plugin import sublime

class CommmunicationLogs:
    def __init__(self, name: str):
        self.name = name
        self.logs: list[str] = []
        self.panel = sublime.active_window().create_output_panel(name)

    def append(self, log: str):
        time = datetime.datetime.now().strftime('%H:%M:%S')
        log_with_time = f"({time}) {log}"
        self.logs.append(log_with_time)
        self.panel.set_read_only(False)
        self.panel.run_command("append", {
            'characters': log_with_time + '\n',
            'force': False,
            'scroll_to_end': True
        })
        last_bracket_point = self.panel.find(r'^(})', self.panel.size(), sublime.FindFlags.REVERSE)
        start_bracket_point = self.panel.find(r'^({|Params: {)', last_bracket_point.end(), sublime.FindFlags.REVERSE)
        if last_bracket_point is not None and start_bracket_point is not None:
            self.panel.fold(sublime.Region(start_bracket_point.end(), last_bracket_point.begin() - 1))
        self.panel.settings().set('scroll_past_end', False)
        self.panel.clear_undo_stack()
        self.panel.set_read_only(True)


def format_payload(value: Any):
    return sublime.encode_value(value, pretty=True)
