from __future__ import annotations
from pathlib import Path
from Mir import LanguageServer
from .package_storage import PackageStorage, run_command
import sublime
import sys
import re
import os
from .runtime import deno

server_storage = PackageStorage(__package__, tag='0.0.2', sync_folder="./language-server")

class PyrightLanguageServer(LanguageServer):
    name='pyright-langserver'
    activation_events={
        'selector': 'source.python',
    }

    async def activate(self):
        # setup runtime and install dependecies
        await deno.setup()
        server_path = server_storage / "language-server" / "node_modules" / "pyright" / "langserver.index.js"
        if not server_path.exists():
            await run_command([deno.path, "install"], cwd=str(server_storage / "language-server"))

        # start process
        await self.connect('stdio', {
            'cmd': [deno.path, 'run', '-A', server_path, '--stdio'],
            'initialization_options': {'completionDisableFilterText': True, 'disableAutomaticTypingAcquisition': False, 'locale': 'en', 'maxTsServerMemory': 0, 'npmLocation': '', 'plugins': [], 'preferences': {'allowIncompleteCompletions': True, 'allowRenameOfImportPath': True, 'allowTextChangesInNewFiles': True, 'autoImportFileExcludePatterns': [], 'disableSuggestions': False, 'displayPartsForJSDoc': True, 'excludeLibrarySymbolsInNavTo': True, 'generateReturnInDocTemplate': True, 'importModuleSpecifierEnding': 'auto', 'importModuleSpecifierPreference': 'shortest', 'includeAutomaticOptionalChainCompletions': True, 'includeCompletionsForImportStatements': True, 'includeCompletionsForModuleExports': True, 'includeCompletionsWithClassMemberSnippets': True, 'includeCompletionsWithInsertText': True, 'includeCompletionsWithObjectLiteralMethodSnippets': True, 'includeCompletionsWithSnippetText': True, 'includePackageJsonAutoImports': 'auto', 'interactiveInlayHints': True, 'jsxAttributeCompletionStyle': 'auto', 'lazyConfiguredProjectsFromExternalProject': False, 'organizeImportsAccentCollation': True, 'organizeImportsCaseFirst': False, 'organizeImportsCollation': 'ordinal', 'organizeImportsCollationLocale': 'en', 'organizeImportsIgnoreCase': 'auto', 'organizeImportsNumericCollation': False, 'providePrefixAndSuffixTextForRename': True, 'provideRefactorNotApplicableReason': True, 'quotePreference': 'auto', 'useLabelDetailsInCompletionEntries': True}, 'tsserver': {'fallbackPath': '', 'logDirectory': '', 'logVerbosity': 'off', 'path': '', 'trace': 'off', 'useSyntaxServer': 'auto'}},
            'settings': {
                "statusText": "{% set parts = [] %}{% if server_version %}{% do parts.append('v' + server_version) %}{% endif %}{% if venv %}{% do parts.append('venv: ' + venv.venv_prompt) %}{% do parts.append('py: ' + venv.python_version) %}{% do parts.append('by: ' + venv.finder_name) %}{% endif %}{{ parts|join('; ') }}",
                "venvStrategies": [
                    "local_dot_venv",
                    "env_var_conda_prefix",
                    "env_var_virtual_env",
                    "rye",
                    "poetry",
                    "pdm",
                    "hatch",
                    "pipenv",
                    "pyenv",
                    "any_subdirectory",
                ],
                "pyright.dev_environment": "",
                "pyright.dev_environment_blender.binary": "blender",
                "pyright.dev_environment_gdb.binary": "gdb",
                "python.analysis.autoImportCompletions": True,
                "python.analysis.autoSearchPaths": True,
                "python.analysis.extraPaths": [],
                "python.analysis.stubPath": "./typings",
                "python.analysis.diagnosticMode": "openFilesOnly",
                "python.analysis.diagnosticSeverityOverrides": {
                },
                "python.analysis.logLevel": "Information",
                "python.analysis.typeCheckingMode": "standard",
                "python.analysis.typeshedPaths": [],
                "python.analysis.useLibraryCodeForTypes": True,
                "pyright.disableLanguageServices": False,
                "pyright.disableOrganizeImports": False,
                "pyright.disableTaggedHints": False,
                "python.pythonPath": "",
                "python.venvPath": "",
            }
        })


    def on_settings_change(self):
        dev_environment = self.settings.get("pyright.dev_environment")
        extraPaths: list[str] = self.settings.get("python.analysis.extraPaths") or []
        # if dev_environment in {"sublime_text_33", "sublime_text_38"}:
        if dev_environment in {"sublime_text_38"}:
            py_ver = self.detect_st_py_ver(dev_environment)
            # add package dependencies into "python.analysis.extraPaths"
            extraPaths.extend(self.find_package_dependency_dirs(py_ver))
        self.settings.set("python.analysis.extraPaths", extraPaths)

    def detect_st_py_ver(self, dev_environment: str) -> tuple[int, int]:
        # default = (3, 3)
        # if dev_environment == "sublime_text_33":
        #     return (3, 3)
        # if dev_environment == "sublime_text_38":
        #     return (3, 8)
        # return default
        return (3, 8)

    def find_package_dependency_dirs(self, py_ver: tuple[int, int] = (3, 3)) -> list[str]:
        dep_dirs = sys.path.copy()
        # replace paths for target Python version
        # @see https://github.com/sublimelsp/LSP-pyright/issues/28
        re_pattern = re.compile(r"(python3\.?)[38]", flags=re.IGNORECASE)
        re_replacement = r"\g<1>8" if py_ver == (3, 8) else r"\g<1>3"
        dep_dirs = [re_pattern.sub(re_replacement, dep_dir) for dep_dir in dep_dirs]

        # move the "Packages/" to the last
        # @see https://github.com/sublimelsp/LSP-pyright/pull/26#discussion_r520747708
        packages_path = sublime.packages_path()
        dep_dirs.remove(packages_path)
        dep_dirs.append(packages_path)

        # # sublime stubs - add as first
        # if py_ver == (3, 3) and (server_dir := self._server_directory_path()):
        #     dep_dirs.insert(0, os.path.join(server_dir, "resources", "typings", "sublime_text_py33"))

        return list(filter(os.path.isdir, dep_dirs))
