from __future__ import annotations
from Mir import mir_logger
import sublime
from pathlib import Path
import shutil
import asyncio
import os
import zipfile
import urllib.request
import subprocess
import sublime_aio
import tarfile
import sys

class PackageStorage:
    def __init__(self, tag: str):
        # Initially PackageStorage was instanced in code like:
        # PackageStorage('Mir', tag='0.0.1', sync_folder='./some-folder')
        # but            ^^^^^ always needed to match the actual package name, in order to copy files successufly
        # so Package authors could write
        # PackageStorage(__package__, tag='0.0.1', sync_folder='./some-folder')
        # but it got repetitive and bolilerplaty, so the latest API is
        # PackageStorage(tag='0.0.1', sync_folder='./some-folder')
        # it the "package name" is inferred by the sys._getframe(1).f_globals.get('__package__')
        caller_frame = sys._getframe(1)
        package_name =caller_frame.f_globals.get('__package__')
        self.name = package_name.split('.')[0] # if called inside Mir-XYS.some_nested_filem, grab just 'Mir-XYS'

        self.tag = tag
        self._storage_dir = (Path(sublime.cache_path()) / ".." / "Package Storage" / self.name / tag).resolve()
        self._package_dir = Path(sublime.packages_path()) / self.name
        if not self._package_dir.exists():
            raise Exception(f'"NAME" must match Package Name, but it was called with PackageStorage("{self.name}")')
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    async def download(self, url: str, save_to_path: Path) -> None:
        if save_to_path.exists():
            return
        async def download_sync():
            with urllib.request.urlopen(url) as response:
                save_to_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_to_path, 'wb') as f:
                    shutil.copyfileobj(response, f)
                    return
        await download_sync()

    def rm(self, relative_path):
        """ Remove folder/file from Package Storage """
        target = self.storage_dir / relative_path
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

    def copy(self, relative_path: str) -> None:
        """Copy file from `Packages/MyPackage/relative_path` to `Package Storage/MyPackage/relative_path` """
        source = self._package_dir / relative_path
        target = self._storage_dir / relative_path
        if target.exists():
            return
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, target)

    def __truediv__(self, other): # used to define the behavior of the true division operator /
        return self._storage_dir / other


def unzip(archive_path: Path, new_name: str | None=None) -> None: # archive will be `folder/some.zip`
    filename: str = archive_path.name # file name will be `some.zip`
    where_to_extract: str = str(archive_path.parent / archive_path.stem) # will be `folder/some` if new_name is not provided
    if new_name:
        where_to_extract = str(archive_path.parent / new_name)
    try:
        if sublime.platform() == 'windows':
             with zipfile.ZipFile(str(archive_path)) as f:
                names = f.namelist()
                _, _ = next(x for x in names if '/' in x).split('/', 1)
                bad_members = [x for x in names if x.startswith('/') or x.startswith('..')]
                if bad_members:
                    raise Exception('{} appears to be malicious, bad filenames: {}'.format(filename, bad_members))
                f.extractall(where_to_extract)
        elif str(archive_path).endswith('.zip'):
            _, error = run_command_sync(['unzip', str(archive_path), '-d', where_to_extract], cwd=str(archive_path.parent))
            if error:
                raise Exception('Error unzipping electron archive: {}'.format(error))
        elif str(archive_path).endswith('.tar.gz'):
             with tarfile.open(archive_path) as f:
                 f.extractall(where_to_extract)
        else:
            raise Exception(f'Mir: Failed unzipping this file: {archive_path}')

    except Exception as ex:
        raise ex


is_windows = sublime.platform() == 'windows'
def run_command_sync(
    args: list[str],
    cwd: str | None = None,
    extra_env: dict[str, str] | None = None,
    extra_paths: list[str] = [],
    shell: bool = is_windows,
) -> tuple[str, str | None]:
    """
    Runs the given command synchronously.

    :returns: A two-element tuple with the returned value and an optional error. If running the command has failed, the
              first tuple element will be empty string and the second will contain the potential `stderr` output. If the
              command has succeeded then the second tuple element will be `None`.
    """
    try:
        env = None
        if extra_env or extra_paths:
            env = os.environ.copy()
            if extra_env:
                env.update(extra_env)
            if extra_paths:
                env['PATH'] = os.path.pathsep.join(extra_paths) + os.path.pathsep + env['PATH']
        startupinfo = None
        if is_windows:
            startupinfo = subprocess.STARTUPINFO()  # type: ignore
            startupinfo.dwFlags |= subprocess.SW_HIDE | subprocess.STARTF_USESHOWWINDOW  # type: ignore
        output = subprocess.check_output(
            args, cwd=cwd, shell=shell, stderr=subprocess.STDOUT, env=env, startupinfo=startupinfo)
        return (output.decode('utf-8', 'ignore').strip(), None)
    except subprocess.CalledProcessError as error:
        return ('', error.output.decode('utf-8', 'ignore').strip())


async def command(cmd: list[str], cwd=None):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        mir_logger.error(f"Command failed: {cmd}")
        if stdout:
            mir_logger.error(f"stdout: {stdout.decode()}")
        if stderr:
            mir_logger.error(f"stderr: {stderr.decode()}")
        raise Exception(f"Command failed with return code {process.returncode}")
