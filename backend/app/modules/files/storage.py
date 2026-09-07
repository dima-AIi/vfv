"""Replaceable file storage backend for the Files module.

Business logic depends only on the ``FileStorage`` protocol; ``LocalFileStorage``
is the local MVP implementation. The user-supplied filename never participates
in the on-disk path: the physical key is a generated uuid plus a sanitized
extension, so path traversal through filenames is structurally impossible.
"""

import re
import uuid
from pathlib import Path
from typing import Protocol

_EXT_PATTERN = re.compile(r"[^a-z0-9]")
_MAX_EXT_LENGTH = 10


class StorageError(Exception):
    pass


class FileStorage(Protocol):
    def save(self, data: bytes, ext: str) -> str: ...

    def read(self, storage_key: str) -> bytes: ...


def sanitize_extension(ext: str) -> str:
    cleaned = _EXT_PATTERN.sub("", ext.lower().lstrip("."))
    return f".{cleaned[:_MAX_EXT_LENGTH]}" if cleaned else ""


class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self._root = root

    @property
    def root(self) -> Path:
        return self._root

    def save(self, data: bytes, ext: str) -> str:
        self._root.mkdir(parents=True, exist_ok=True)
        storage_key = f"{uuid.uuid4().hex}{sanitize_extension(ext)}"
        (self._root / storage_key).write_bytes(data)
        return storage_key

    def read(self, storage_key: str) -> bytes:
        if not storage_key or Path(storage_key).name != storage_key:
            raise StorageError("Некорректный ключ хранилища.")
        absolute = (self._root / storage_key).resolve()
        if not absolute.is_relative_to(self._root.resolve()):
            raise StorageError("Некорректный ключ хранилища.")
        if not absolute.is_file():
            raise StorageError("Содержимое файла недоступно.")
        return absolute.read_bytes()
