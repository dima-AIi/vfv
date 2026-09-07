from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings

ALLOWED_SUFFIXES = frozenset({".md", ".markdown"})


class DocumentPathError(Exception):
    pass


@dataclass(frozen=True)
class ResolvedPath:
    absolute: Path
    relative: str
    root_name: str


class LocalDocumentStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._roots = self._settings.resolved_document_roots
        self._max_bytes = self._settings.document_max_bytes
        self._repo_root = self._roots[0].parent if self._roots else Path.cwd()

    @property
    def roots(self) -> list[Path]:
        return list(self._roots)

    def resolve(self, relative_path: str) -> ResolvedPath:
        normalized = relative_path.strip().replace("\\", "/").lstrip("/")
        if not normalized:
            raise DocumentPathError("Путь не задан.")
        candidate = Path(normalized)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise DocumentPathError("Выход за пределы каталога запрещён.")

        root_names = {root.name: root for root in self._roots}
        if len(candidate.parts) < 2 or candidate.parts[0] not in root_names:
            raise DocumentPathError(
                "Путь должен начинаться с одного из разрешённых корней документации: "
                f"{', '.join(sorted(root_names))}.",
            )

        root = root_names[candidate.parts[0]]
        absolute = (self._repo_root / candidate).resolve()
        try:
            is_within = absolute.is_relative_to(root)
        except ValueError:
            is_within = False
        if not is_within:
            raise DocumentPathError("Путь выходит за пределы своего корня документации.")
        if not absolute.is_file():
            raise DocumentPathError(f"Файл не найден: {normalized}")
        if absolute.suffix.lower() not in ALLOWED_SUFFIXES:
            raise DocumentPathError(
                f"Неподдерживаемый тип файла: {absolute.suffix}",
            )
        size = absolute.stat().st_size
        if size > self._max_bytes:
            raise DocumentPathError(
                f"Файл превышает допустимый размер ({size} > {self._max_bytes} байт).",
            )
        return ResolvedPath(
            absolute=absolute,
            relative=candidate.as_posix(),
            root_name=root.name,
        )

    def read(self, resolved: ResolvedPath) -> str:
        return resolved.absolute.read_text(encoding="utf-8", errors="replace")

    def catalog(self, descending: bool = True) -> list[dict[str, object]]:
        collected: list[tuple[float, str, str, str, int]] = []
        for root in self._roots:
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*.md")) + sorted(root.rglob("*.markdown")):
                relative = path.relative_to(self._repo_root).as_posix()
                stat = path.stat()
                collected.append(
                    (stat.st_mtime, root.name, relative, path.name, stat.st_size),
                )
        collected.sort(key=lambda item: (-item[0], item[1], item[2]), reverse=not descending)
        return [
            {
                "relative_path": relative,
                "name": name,
                "root_name": root_name,
                "size_bytes": size,
            }
            for _mtime, root_name, relative, name, size in collected
        ]
