from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO


class _TeeStream:
    def __init__(self, primary: TextIO, mirror: TextIO) -> None:
        self._primary = primary
        self._mirror = mirror

    def write(self, data: str) -> int:
        self._primary.write(data)
        self._mirror.write(data)
        return len(data)

    def flush(self) -> None:
        self._primary.flush()
        self._mirror.flush()

    def isatty(self) -> bool:
        return bool(getattr(self._primary, "isatty", lambda: False)())

    @property
    def encoding(self) -> str | None:
        return getattr(self._primary, "encoding", None)


def configure_console_tee(log_path: str | Path | None) -> Path | None:
    if not log_path:
        return None

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mirror = path.open("a", encoding="utf-8")
    sys.stdout = _TeeStream(sys.stdout, mirror)
    sys.stderr = _TeeStream(sys.stderr, mirror)
    print(f"console_log_path={path}")
    return path
