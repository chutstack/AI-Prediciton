from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any


class ArtifactStore:
    def __init__(self, model_dir: str = "models") -> None:
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def save(self, asset: str, model: Any, meta: dict[str, Any]) -> None:
        with (self.model_dir / f"{asset}_model.pkl").open("wb") as fh:
            pickle.dump(model, fh)
        (self.model_dir / f"{asset}_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def load(self, asset: str) -> tuple[Any, dict[str, Any]]:
        with (self.model_dir / f"{asset}_model.pkl").open("rb") as fh:
            model = pickle.load(fh)
        meta = json.loads((self.model_dir / f"{asset}_meta.json").read_text(encoding="utf-8"))
        return model, meta
