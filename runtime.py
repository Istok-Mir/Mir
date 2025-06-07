from __future__ import annotations
from typing import Literal
from .package_storage import PackageStorage, unzip
import sublime
import os
from Mir import LoaderInStatusBar
from pathlib import Path

runtime_storage_path = PackageStorage(tag='runtime')

class Yarn:
    def __init__(self) -> None:
        self.package_storage = runtime_storage_path / 'yarn'

    @property
    def path(self) -> str:
        return self.package_storage / 'yarn.js'

    async def setup(self):
        with LoaderInStatusBar(f'Downloading Yarn'):
            yarn_url = 'https://github.com/yarnpkg/yarn/releases/download/v1.22.22/yarn-1.22.22.js'
            save_to = self.package_storage / 'yarn.js'
            await runtime_storage_path.download(yarn_url, save_to)


DenoVersion = Literal['2.2',]
deno_versions: list[DenoVersion] = ['2.2']
class Deno:
    def __init__(self, deno_version: DenoVersion) -> None:
        if deno_version not in deno_versions:
            raise Exception(f'{deno_version} is not supported, please specify one of f{deno_versions}')
        self.deno_version = deno_version
        self.package_storage = runtime_storage_path / 'deno' / self.deno_version

    @property
    def path(self) -> str:
        return str(self.package_storage / 'deno' / 'deno')

    async def setup(self):
        with LoaderInStatusBar(f'Downloading Deno {self.deno_version}'):
            fetch_url, archive_filename = self._archive_on_github()
            if not Path(self.path).exists():
                save_to = self.package_storage / archive_filename
                await runtime_storage_path.download(fetch_url, save_to)
                unzip(save_to, new_name='deno')
            
    def _archive_on_github(self) -> tuple[str, str]:
        platform = sublime.platform()
        arch = sublime.arch()
        if platform == 'windows':
            platform_code = 'pc-windows-msvc'
        elif platform == 'linux':
            platform_code = 'unknown-linux-gnu'
        elif platform == 'osx':
            platform_code = 'apple-darwin'
        else:
            raise Exception('{} {} is not supported'.format(arch, platform))
        if arch == 'x32':
            arch_code = 'x86_64'  # GitHub doesn't seem to have explicit x32 builds, using x64 as a fallback or error case
        elif arch == 'x64':
            arch_code = 'x86_64'
        elif arch == 'arm64':
            arch_code = 'aarch64'
        else:
            raise Exception('Unsupported architecture: {}'.format(arch))
        archive_filename = 'deno-{}-{}.zip'.format(arch_code, platform_code) # Using 'deno-' prefix
        release_version = {
            '2.2': 'v2.2.12', 
        }

        fetch_url = 'https://github.com/denoland/deno/releases/download/{version}/{filename}'.format( # Changed URL to denoland/deno
            version=release_version[self.deno_version], # Assuming self.deno_version holds the correct version tag
            filename=archive_filename
        )
        return fetch_url, archive_filename



NodeVersion = Literal['22', '20', '18']
node_versions: list[NodeVersion] = ['22', '20', '18']
# https://www.electronjs.org/docs/latest/tutorial/electron-timelines#timeline
node_version_to_electron_version = {
    '22': '35.2.0', # NodeJS 22.14
    '20': '34.4.0', # NodeJS 20.18
    '18': '28.0.0', # NodeJS 18.18
}

class Electron:
    def __init__(self, node_version: NodeVersion) -> None:
        if node_version not in node_versions:
            raise Exception(f'{node_version} is not supported, please specify one of f{node_versions}')
        self.node_version = node_version
        self.package_storage = runtime_storage_path / 'electron_node' / self.node_version

    @property
    def path(self) -> str:
        binary_path: str | None = None
        platform = sublime.platform()
        if platform == 'osx':
            binary_path = str(self.package_storage / 'electron' / 'Electron.app' / 'Contents' / 'MacOS' / 'Electron')
        elif platform == 'windows':
            binary_path = str(self.package_storage / 'electron' / 'electron.exe')
        else:
            binary_path = str(self.package_storage / 'electron' / 'electron')
        return binary_path

    async def setup(self):
        with LoaderInStatusBar(f'Downloading Node.js {self.node_version}'):
            fetch_url, archive_filename = self._archive_on_github()
            if not Path(self.path).exists():
                save_to = self.package_storage / archive_filename
                await runtime_storage_path.download(fetch_url, save_to)
                unzip(save_to, new_name='electron')

            
    def _archive_on_github(self) -> tuple[str, str]:
        platform = sublime.platform()
        arch = sublime.arch()
        if platform == 'windows':
            platform_code = 'win32'
        elif platform == 'linux':
            platform_code = 'linux'
        elif platform == 'osx':
            platform_code = 'darwin'
        else:
            raise Exception('{} {} is not supported'.format(arch, platform))
        electron_version = node_version_to_electron_version[self.node_version]
        archive_filename = 'electron-v{}-{}-{}.zip'.format(electron_version, platform_code, arch)
        fetch_url = 'https://github.com/electron/electron/releases/download/v{version}/{filename}'.format(
            version=electron_version, 
            filename=archive_filename
        )
        return fetch_url, archive_filename
        

os.environ.update({'ELECTRON_RUN_AS_NODE': 'true'})
electron_node_22 = Electron('22')
electron_node_20 = Electron('20')
electron_node_18 = Electron('18')
# electron_node is always latest
electron_node = electron_node_22

deno2_2 = Deno('2.2')
# deno is always latest
deno = deno2_2

yarn = Yarn()
