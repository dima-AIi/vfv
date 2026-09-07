"""Shared helpers for case-insensitive LIKE search.

``like_contains`` escapes SQL LIKE wildcards in user input so a query such as
"%" matches a literal percent sign instead of every row, and returns a
contains-pattern. Callers compare with ``func.lower(column).like(pattern,
escape=LIKE_ESCAPE)``; the SQLite ``lower`` is Unicode-aware (registered in the
connect handler) and PostgreSQL ``lower`` is Unicode-aware natively.
"""

LIKE_ESCAPE = "\\"


def like_contains(term: str) -> str:
    lowered = term.lower()
    escaped = (
        lowered.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"
