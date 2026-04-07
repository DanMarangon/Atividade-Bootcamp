from __future__ import annotations

import json
from pathlib import Path

from estoque_solidario.models import Lote


class JsonRepository:
    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or self._default_data_path()

    def load_lotes(self) -> list[Lote]:
        self._ensure_data_file()
        with self.file_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return [Lote.from_dict(item) for item in payload.get("lotes", [])]

    def save_lotes(self, lotes: list[Lote]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"lotes": [lote.to_dict() for lote in lotes]}
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def _ensure_data_file(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.save_lotes([])

    @staticmethod
    def _default_data_path() -> Path:
        for candidate in (Path.cwd(), Path(__file__).resolve()):
            current = candidate if candidate.is_dir() else candidate.parent
            for path in (current, *current.parents):
                if (path / "pyproject.toml").exists():
                    return path / "data" / "dados.json"
        return Path.cwd() / "data" / "dados.json"
