# start a fastapi server with uvicorn

import glob
from langchain_searxng.settings.settings import settings
from langchain_searxng.constants import PROJECT_ROOT_PATH

from uvicorn import Config, Server
from uvicorn.supervisors.watchfilesreload import WatchFilesReload

from pathlib import Path
import hashlib
from socket import socket
from typing import Callable
from watchfiles import Change, watch


"""
自定义uvicorn启动类
"""


class FileFilter:
    def __init__(self, config: Config):
        default_includes = ["*.py"]
        self.includes = [
            default
            for default in default_includes
            if default not in config.reload_excludes
        ]
        self.includes.extend(config.reload_includes)
        self.includes = list(set(self.includes))

        default_excludes = [".*", ".py[cod]", ".sw.*", "~*"]
        self.excludes = [
            default
            for default in default_excludes
            if default not in config.reload_includes
        ]
        self.exclude_dirs = []
        for e in config.reload_excludes:
            p = Path(e)
            try:
                is_dir = p.is_dir()
            except OSError:  # pragma: no cover
                # gets raised on Windows for values like "*.py"
                is_dir = False

            if is_dir:
                self.exclude_dirs.append(p)
            else:
                self.excludes.append(e)
        self.excludes = list(set(self.excludes))

    def __call__(self, change: "Change", path: Path | str) -> bool:
        if isinstance(path, str):
            path = Path(path)
        for include_pattern in self.includes:
            if path.match(include_pattern):
                if str(path).endswith(include_pattern):
                    return True

                for exclude_dir in self.exclude_dirs:
                    if exclude_dir in path.parents:
                        return False

                for exclude_pattern in self.excludes:
                    if path.match(exclude_pattern):
                        return False

                return True
        return False


class CustomWatchFilesReload(WatchFilesReload):

    def __init__(
        self,
        config: Config,
        target: Callable[[list[socket] | None], None],
        sockets: list[socket],
    ) -> None:
        super().__init__(config, target, sockets)
        self.reloader_name = "WatchFiles"
        self.reload_dirs = []
        self.ignore_paths = []
        for directory in config.reload_dirs:
            self.reload_dirs.append(directory)

        self.watch_filter = FileFilter(config)
        self.watcher = watch(
            *self.reload_dirs,
            watch_filter=self.watch_filter,
            stop_event=self.should_exit,
            # using yield_on_timeout here mostly to make sure tests don't
            # hang forever, won't affect the class's behavior
            yield_on_timeout=True,
        )

        self.file_hashes = {}  # Store file hashes

        # Calculate and store hashes for initial files
        for directory in self.reload_dirs:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and self.watch_filter(None, file_path):
                    self.file_hashes[str(file_path)] = self.calculate_file_hash(
                        file_path
                    )

    def should_restart(self) -> list[Path] | None:
        self.pause()

        changes = next(self.watcher)
        if changes:
            changed_paths = []
            for event_type, path in changes:
                if event_type == Change.modified or event_type == Change.added:
                    file_hash = self.calculate_file_hash(path)
                    if (
                        path not in self.file_hashes
                        or self.file_hashes[path] != file_hash
                    ):
                        changed_paths.append(Path(path))
                        self.file_hashes[path] = file_hash

            if changed_paths:
                return [p for p in changed_paths if self.watch_filter(None, p)]

        return None

    def calculate_file_hash(self, file_path: str) -> str:
        with open(file_path, "rb") as file:
            file_contents = file.read()
            return hashlib.md5(file_contents).hexdigest()


non_yaml_files = [
    f
    for f in glob.glob("**", root_dir=PROJECT_ROOT_PATH, recursive=True)
    if not f.lower().endswith((".yaml", ".yml"))
]
try:
    config = Config(
        app="langchain_searxng.main:app",
        host="0.0.0.0",
        port=settings().server.port,
        reload=True,
        reload_dirs=str(PROJECT_ROOT_PATH),
        reload_excludes=non_yaml_files,
        reload_includes="*.yaml",
        log_config=None,
    )

    server = Server(config=config)

    sock = config.bind_socket()
    CustomWatchFilesReload(config, target=server.run, sockets=[sock]).run()
except KeyboardInterrupt:
    ...
