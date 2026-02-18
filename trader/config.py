from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(slots=True)
class AppConfig:
    raw: dict[str, Any]

    @property
    def assets(self) -> list[str]:
        return list(self.raw["assets"])


def load_config(config_path: str | Path) -> AppConfig:
    load_dotenv()
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return AppConfig(raw=data)
