from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from trader.utils import ensure_dir


class JsonlLogger:
    def __init__(self, logs_dir: str = "logs") -> None:
        ensure_dir(logs_dir)
        stamp = pd.Timestamp.now().strftime("%Y%m%d")
        self.path = Path(logs_dir) / f"run_{stamp}.jsonl"

    def log(self, event: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, default=str) + "\n")
