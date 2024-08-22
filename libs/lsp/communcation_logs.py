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
        log_with_time = f"[{time}] {log}"
        self.logs.append(log_with_time)
        self.panel.set_read_only(False)
        self.panel.run_command("append", {
            'characters': log_with_time + '\n\n',
            'force': False,
            'scroll_to_end': True
        })
        self.panel.clear_undo_stack()
        self.panel.set_read_only(True)


def format_payload(value: Any):
    return one_level_indent(sublime.encode_value(value))

def one_level_indent(text):
    return replace_last(text.replace('{', '{\n\t', 1).replace('[', '[\n\t', 1), '}', '\n}')

def replace_last(text:str, old_char: str, new_char: str):
    k = text.rfind(old_char)
    return text[:k] + new_char
