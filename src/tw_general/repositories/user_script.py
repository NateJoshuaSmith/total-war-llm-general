import os
import time
from pathlib import Path

_ATTEMPTS = 10
_RETRY_WAIT_S = 0.05


def _decode(data: bytes) -> str:
    if not data:
        return ""
    if not data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise UnicodeError("not UTF-16 with a BOM")
    return data.decode("utf-16")


def _render(lines: list[str]) -> bytes:
    if not lines:
        return b"\xff\xfe"
    text = "\r\n".join(lines) + "\r\n"
    return b"\xff\xfe" + text.encode("utf-16-le")


class UserScriptRepository:
    def __init__(self, scripts_dir: Path) -> None:
        self._path = Path(scripts_dir) / "user.script.txt"
        self._backup = Path(str(self._path) + ".twllm-backup")

    @property
    def path(self) -> Path:
        return self._path

    def read_lines(self) -> list[str] | None:
        if not self._path.is_file():
            return None
        return _decode(self._path.read_bytes()).splitlines()

    def write_lines(self, lines: list[str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._backup_once()
        temporary = Path(str(self._path) + ".tmp")
        temporary.write_bytes(_render(lines))
        for attempt in range(1, _ATTEMPTS + 1):
            try:
                os.replace(temporary, self._path)
                return
            except PermissionError:
                if attempt == _ATTEMPTS:
                    raise
                time.sleep(_RETRY_WAIT_S)

    def _backup_once(self) -> None:
        if not self._path.is_file() or self._backup.exists():
            return
        self._backup.write_bytes(self._path.read_bytes())
