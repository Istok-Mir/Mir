from __future__ import annotations


class MirCommand:
    _commands: dict[str, list[str]] = {}
    @staticmethod
    def register_command(command: str, sublime_command: str):
        MirCommand._commands.setdefault(command, []).append(sublime_command)

    @staticmethod
    def to_sublime_commands(command: str) -> list[str]:
        return MirCommand._commands.get(command, [])
