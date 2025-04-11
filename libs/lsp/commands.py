from __future__ import annotations


class MirCommand:
    _commands: dict[str, list[str]] = {}
    @staticmethod
    def register_command(cmd: str, sublime_command: str):
        MirCommand._commands.setdefault(cmd, []).append(sublime_command)

    @staticmethod
    def to_sublime_commands(cmd: str) -> list[str]:
        return MirCommand._commands.get(cmd, [])
