from __future__ import annotations
from os import path
import sublime
from pathlib import Path
import shutil
import hashlib
import asyncio
import os
import zipfile
import urllib.request
import subprocess

class PackageStorage:
    def __init__(self, *pathsegments: str):
        first, *rest = pathsegments
        self.name = first
        self.storage_dir = (Path(sublime.cache_path()) / ".." / "Package Storage" / self.name).joinpath(*rest).resolve()
        self.package_dir = Path(sublime.packages_path()) / self.name
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def is_same(self, file_path: str):
        """Compare file in "Package Storage/MyPackage/file_path" and in "Packages/MyPackage/file_path" to see if the content is the same. """
        try:
            print(str("Packages" / Path(self.name) / file_path))
            package_file_contents = sublime.load_resource(str("Packages" / Path(self.name) / file_path))
        except:
            return False

        storage_file = self.storage_dir / file_path
        if not storage_file.exists():
            return False

        with open(storage_file) as my_file:
            storage_file_contents = my_file.read()
        return self._hash_file(package_file_contents) == self._hash_file(storage_file_contents)

    def rm(self, relative_path):
        """ Remove folder/file from Package Storage """
        target = self.storage_dir / relative_path
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

    def exists(self, filename: str) -> bool:
        return path.isfile(self.storage_dir / filename) or path.isdir(self.storage_dir / filename)

    async def download(self, url: str, file_name: str) -> str:
        file_path = (self.storage_dir / file_name)
        if file_path.exists():
            return str(file_path)
        async def download_sync():
            with urllib.request.urlopen(url) as response:
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(response, f)
                    return
        await download_sync()
        return str(file_path)

    def copy(self, relative_path: str):
        """Copy file from `Packages/MyPackage/relative_path` to `Package Storage/MyPackage/relative_path` """
        source = self.package_dir / relative_path
        target = self.storage_dir / relative_path

        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, target)

    async def run_command(self, command_dict):
        cwd = command_dict.get('cwd')
        cmd = command_dict.get('cmd')

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"Command failed: {cmd}")
            if stdout:
                print(f"stdout: {stdout.decode()}")
            if stderr:
                print(f"stderr: {stderr.decode()}")
            raise Exception(f"Command failed with return code {process.returncode}")

    def __truediv__(self, other): # used to define the behavior of the true division operator /
        return self.storage_dir / other

    def _hash_file(self, content: str):
        hasher = hashlib.sha256()
        hasher.update(content.encode('utf-8')) #important to encode the string
        return hasher.hexdigest()


def unzip(archive: str, new_name: str | None=None) -> None: # archive will be `folder/some.zip`
    archive_path = Path(archive)
    filename: str = archive_path.name # file name will be `some.zip`
    where_to_extract: str = str(archive_path.parent / archive_path.stem) # will be `folder/some` if new_name is not provided
    if new_name:
        where_to_extract = str(archive_path.parent / new_name)
    try:
        if sublime.platform() == 'windows':
             with zipfile.ZipFile(archive) as f:
                names = f.namelist()
                _, _ = next(x for x in names if '/' in x).split('/', 1)
                bad_members = [x for x in names if x.startswith('/') or x.startswith('..')]
                if bad_members:
                    raise Exception('{} appears to be malicious, bad filenames: {}'.format(filename, bad_members))
                f.extractall(where_to_extract)
        else:
            _, error = run_command_sync(['unzip', archive, '-d', where_to_extract], cwd=str(archive_path.parent))
            if error:
                raise Exception('Error unzipping electron archive: {}'.format(error))

    except Exception as ex:
        raise ex
    finally:
        ...
        # os.remove(archive)                



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
