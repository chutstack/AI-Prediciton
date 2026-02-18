from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonStateStore:
    def __init__(self, path: str = "logs/paper_state.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"cash": 100000.0, "positions": {}, "equity_curve": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, state: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(state, indent=2), encoding="utf-8")
