from __future__ import annotations

from pathlib import Path
import asyncio
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "shared"))

from app.core.config import get_settings
from app.schemas.project import ProjectCreate
from app.services.assets import attach_identity_images
from app.services.creative import generate_storyboard
from app.services.pipeline import generate_project_video, generate_scene_video
from app.services.repository import ProjectRepository
from app.services.storage import LocalStorageAdapter
from app.services.video_generation import (
    MockVideoGenerator,
    VideoGenerationError,
    XaiVideoGenerator,
    get_video_generator,
    normalize_video_backend,
)
from app.services.video_prompting import VideoPromptBuilder


class FakeUploadFile:
    def __init__(self, *, filename: str, content_type: str, payload: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


class FakeResponse:
    def __init__(
        self,
        payload: dict[str, object] | None = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        content: bytes = b"",
    ) -> None:
        self._payload = payload or {}
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content

    def json(self) -> dict[str, object]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


class FakeXaiClient:
    def __init__(
        self,
        *,
        submit_payload: dict[str, object] | None = None,
        poll_payloads: list[dict[str, object]] | None = None,
        video_content: bytes | None = None,
    ) -> None:
        self.submit_payload = submit_payload or {"request_id": "req-123"}
        self.poll_payloads = poll_payloads or [{"status": "done", "model": "grok-imagine-video", "video": {"url": "https://tmp.example/video.mp4"}}]
        self.video_content = video_content or _fake_mp4()
        self.post_calls: list[dict[str, object]] = []
        self.get_calls: list[str] = []

    def post(self, url: str, *, json: dict[str, object], headers: dict[str, str]) -> FakeResponse:
        self.post_calls.append({"url": url, "json": json, "headers": headers})
        return FakeResponse(self.submit_payload)

    def get(self, url: str, *, headers: dict[str, str] | None = None) -> FakeResponse:
        self.get_calls.append(url)
        if "/videos/" in url:
            payload = self.poll_payloads.pop(0)
            return FakeResponse(payload)
        return FakeResponse(headers={"content-type": "video/mp4"}, content=self.video_content)


def _fake_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _fake_mp4() -> bytes:
    return b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isommock-video"


def _build_project(tmp_path: Path, monkeypatch, *, with_primary: bool = False) -> ProjectRepository:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))
    repo = ProjectRepository()
    project = repo.create_project(
        ProjectCreate(
            title="Video System",
            prompt="Create a premium launch clip with a recognizable hero avatar and polished cinematic motion.",
            style="cinematic premium",
            duration_target=24,
            aspect_ratio="16:9",
            character_notes="Founder in navy tailoring, calm confident expression, consistent face silhouette.",
            lock_identity=True,
        )
    )
    if with_primary:
        project = asyncio.run(
            attach_identity_images(
                project=project,
                files=[FakeUploadFile(filename="avatar.png", content_type="image/png", payload=_fake_png())],
                role="primary",
                storage=LocalStorageAdapter(tmp_path / "data"),
            )
        )
    project.storyboard = generate_storyboard(project)
    repo.save_project(project)
    return repo


def test_video_generator_factory_supports_xai_and_mock(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("VIDEO_BACKEND", "mock")
    assert isinstance(get_video_generator(get_settings()), MockVideoGenerator)

    monkeypatch.setenv("VIDEO_BACKEND", "grok")
    assert isinstance(get_video_generator(get_settings()), XaiVideoGenerator)
    assert normalize_video_backend("grok-imagine-video") == "xai"


def test_video_prompt_builder_prefers_primary_image(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch, with_primary=True)
    project = repo.list_projects()[0]
    builder = VideoPromptBuilder(default_duration=5, default_resolution="720p", default_aspect_ratio="16:9")

    prompt = builder.build_scene_video_prompt(project, project.storyboard.scenes[0])

    assert prompt.source_mode == "image_to_video"
    assert prompt.identity_mode == "locked_primary_image"
    assert "primary character image" in prompt.prompt_used
    assert "identity drift" in prompt.negative_prompt


def test_video_prompt_builder_uses_text_to_video_without_primary_image(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch, with_primary=False)
    project = repo.list_projects()[0]
    builder = VideoPromptBuilder(default_duration=5, default_resolution="720p", default_aspect_ratio="16:9")

    prompt = builder.build_project_video_prompt(project)

    assert prompt.source_mode == "text_to_video"
    assert prompt.identity_mode == "text_only_identity"


def test_xai_project_video_downloads_and_persists_storage(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch, with_primary=False)
    project = repo.list_projects()[0]
    monkeypatch.setenv("VIDEO_BACKEND", "xai")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    settings = get_settings()
    generator = XaiVideoGenerator(settings, fallback_generator=MockVideoGenerator(settings), client=FakeXaiClient())

    asset, summary = generator.generate_project_video(project)

    assert asset.relative_path.endswith(".mp4")
    assert (settings.data_root / asset.relative_path).exists()
    assert asset.video_backend == "xai"
    assert asset.provider_request_id == "req-123"
    assert summary.active_backend == "xai"
    assert summary.provider_status == "done"


def test_xai_scene_video_uses_primary_image_payload(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch, with_primary=True)
    project = repo.list_projects()[0]
    scene = project.storyboard.scenes[0]
    monkeypatch.setenv("VIDEO_BACKEND", "xai")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    client = FakeXaiClient()
    settings = get_settings()
    generator = XaiVideoGenerator(settings, fallback_generator=MockVideoGenerator(settings), client=client)

    generator.generate_scene_video(project, scene)

    payload = client.post_calls[0]["json"]
    assert payload["model"] == "grok-imagine-video"
    assert "image" in payload
    assert str(payload["image"]["url"]).startswith("data:image/png;base64,")


def test_xai_video_timeout_falls_back_to_mock(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch, with_primary=False)
    project = repo.list_projects()[0]
    monkeypatch.setenv("VIDEO_BACKEND", "xai")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("XAI_POLL_TIMEOUT_SECONDS", "0")
    settings = get_settings()
    generator = XaiVideoGenerator(
        settings,
        fallback_generator=MockVideoGenerator(settings),
        client=FakeXaiClient(poll_payloads=[{"status": "processing"}]),
    )

    asset, summary = generator.generate_project_video(project)

    assert asset.video_generation_mode == "mock_fallback"
    assert "Timeout polling xAI" in (asset.fallback_message or "")
    assert summary.generation_mode == "mock_fallback"


def test_xai_video_expired_falls_back_to_mock(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch, with_primary=False)
    project = repo.list_projects()[0]
    monkeypatch.setenv("VIDEO_BACKEND", "xai")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    settings = get_settings()
    generator = XaiVideoGenerator(
        settings,
        fallback_generator=MockVideoGenerator(settings),
        client=FakeXaiClient(poll_payloads=[{"status": "expired"}]),
    )

    asset, summary = generator.generate_project_video(project)

    assert asset.video_generation_mode == "mock_fallback"
    assert "scaduta" in (summary.message or "")


def test_video_generation_without_fallback_raises(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch, with_primary=False)
    project = repo.list_projects()[0]
    monkeypatch.setenv("VIDEO_BACKEND", "xai")
    monkeypatch.setenv("VIDEO_FALLBACK_TO_MOCK", "false")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    settings = get_settings()
    generator = XaiVideoGenerator(settings, fallback_generator=None, client=FakeXaiClient())

    with pytest.raises(VideoGenerationError):
        generator.generate_project_video(project)


def test_pipeline_persists_video_metadata(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch, with_primary=False)
    project = repo.list_projects()[0]
    monkeypatch.setenv("VIDEO_BACKEND", "mock")

    updated = generate_project_video(project)
    updated = generate_scene_video(updated, updated.storyboard.scenes[0].id)
    repo.save_project(updated)
    stored = repo.get_project(updated.id)

    assert stored.project_video is not None
    assert stored.project_video.video_backend == "mock"
    assert stored.video_job is not None
    assert stored.storyboard.scenes[0].generated_video is not None
    assert stored.storyboard.scenes[0].generated_video.prompt_used is not None
