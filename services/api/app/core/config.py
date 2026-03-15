from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class Settings:
    api_host: str
    api_port: int
    data_root: Path

    @property
    def projects_dir(self) -> Path:
        return self.data_root / "projects"

    @property
    def previews_dir(self) -> Path:
        return self.data_root / "previews"

    @property
    def renders_dir(self) -> Path:
        return self.data_root / "renders"

    @property
    def temp_dir(self) -> Path:
        return self.data_root / "temp"


def get_settings() -> Settings:
    data_root = Path(os.getenv("DATA_ROOT", "./data")).resolve()
    return Settings(
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        data_root=data_root,
    )


def ensure_data_dirs() -> None:
    settings = get_settings()
    for path in [
        settings.data_root,
        settings.projects_dir,
        settings.previews_dir,
        settings.renders_dir,
        settings.temp_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
