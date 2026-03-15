from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class Settings:
    api_host: str
    api_port: int
    data_root: Path
    storage_backend: str
    aws_region: str | None
    s3_bucket_name: str | None
    s3_prefix: str
    presigned_url_ttl_seconds: int
    preview_backend: str
    preview_external_url: str | None
    preview_external_api_key: str | None
    preview_external_timeout_seconds: float
    preview_external_model_name: str | None
    preview_external_max_retries: int
    preview_fallback_to_mock: bool
    video_backend: str
    xai_video_model: str
    xai_api_key: str | None
    xai_api_base_url: str
    xai_poll_interval_seconds: float
    xai_poll_timeout_seconds: float
    xai_video_default_duration: int
    xai_video_default_resolution: str
    xai_video_default_aspect_ratio: str
    xai_download_to_storage: bool
    video_fallback_to_mock: bool
    render_backend: str

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
    def assets_dir(self) -> Path:
        return self.data_root / "assets"

    @property
    def temp_dir(self) -> Path:
        return self.data_root / "temp"


def get_settings() -> Settings:
    data_root = Path(os.getenv("DATA_ROOT", "./data")).resolve()
    preview_backend = (os.getenv("PREVIEW_BACKEND", "mock").strip().lower() or "mock")
    return Settings(
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        data_root=data_root,
        storage_backend=os.getenv("STORAGE_BACKEND", "local").strip().lower() or "local",
        aws_region=(os.getenv("AWS_REGION") or "").strip() or None,
        s3_bucket_name=(os.getenv("S3_BUCKET_NAME") or "").strip() or None,
        s3_prefix=(os.getenv("S3_PREFIX") or "").strip().strip("/"),
        presigned_url_ttl_seconds=int(os.getenv("PRESIGNED_URL_TTL_SECONDS", "900")),
        preview_backend=preview_backend,
        preview_external_url=(os.getenv("PREVIEW_EXTERNAL_URL") or "").strip() or None,
        preview_external_api_key=(os.getenv("PREVIEW_EXTERNAL_API_KEY") or "").strip() or None,
        preview_external_timeout_seconds=float(os.getenv("PREVIEW_EXTERNAL_TIMEOUT_SECONDS", "30")),
        preview_external_model_name=(os.getenv("PREVIEW_EXTERNAL_MODEL_NAME") or "").strip() or None,
        preview_external_max_retries=max(0, int(os.getenv("PREVIEW_EXTERNAL_MAX_RETRIES", "1"))),
        preview_fallback_to_mock=(os.getenv("PREVIEW_FALLBACK_TO_MOCK", "true").strip().lower() != "false"),
        video_backend=(os.getenv("VIDEO_BACKEND", "mock").strip().lower() or "mock"),
        xai_video_model=(os.getenv("XAI_VIDEO_MODEL", "grok-imagine-video").strip() or "grok-imagine-video"),
        xai_api_key=(os.getenv("XAI_API_KEY") or "").strip() or None,
        xai_api_base_url=(os.getenv("XAI_API_BASE_URL", "https://api.x.ai/v1").strip().rstrip("/") or "https://api.x.ai/v1"),
        xai_poll_interval_seconds=float(os.getenv("XAI_POLL_INTERVAL_SECONDS", "5")),
        xai_poll_timeout_seconds=float(os.getenv("XAI_POLL_TIMEOUT_SECONDS", "600")),
        xai_video_default_duration=int(os.getenv("XAI_VIDEO_DEFAULT_DURATION", "5")),
        xai_video_default_resolution=(os.getenv("XAI_VIDEO_DEFAULT_RESOLUTION", "720p").strip() or "720p"),
        xai_video_default_aspect_ratio=(os.getenv("XAI_VIDEO_DEFAULT_ASPECT_RATIO", "16:9").strip() or "16:9"),
        xai_download_to_storage=(os.getenv("XAI_DOWNLOAD_TO_STORAGE", "true").strip().lower() != "false"),
        video_fallback_to_mock=(os.getenv("VIDEO_FALLBACK_TO_MOCK", "true").strip().lower() != "false"),
        render_backend=os.getenv("RENDER_BACKEND", "local").strip().lower() or "local",
    )


def ensure_data_dirs() -> None:
    settings = get_settings()
    for path in [
        settings.data_root,
        settings.projects_dir,
        settings.previews_dir,
        settings.renders_dir,
        settings.assets_dir,
        settings.temp_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
