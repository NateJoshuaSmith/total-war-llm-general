from pathlib import Path


def _has_end_line(text: str) -> bool:
    return any(line.strip() == "end" for line in text.splitlines())


class StateFileRepository:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def read(self) -> str | None:
        try:
            data = self._path.read_bytes()
        except OSError:
            return None
        try:
            text = data.decode("ascii")
        except UnicodeError:
            return None
        if not _has_end_line(text):
            return None
        return text
