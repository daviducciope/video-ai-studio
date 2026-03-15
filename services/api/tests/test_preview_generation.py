from __future__ import annotations

from base64 import b64encode
from pathlib import Path
import sys

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "shared"))

from app.core.config import get_settings
from app.schemas.project import ProjectCreate
from app.services.creative import generate_storyboard
from app.services.pipeline import generate_previews, select_scene_preview
from app.services.preview_generation import (
    ExternalGenericPreviewGenerator,
    MockPreviewGenerator,
    PreviewGenerationError,
    RealProviderPreviewGenerator,
    get_preview_generator,
    normalize_preview_backend,
)
from app.services.preview_prompting import PromptBuilder
from app.services.repository import ProjectRepository


class FakeResponse:
    def __init__(
        self,
        payload: dict[str, object] | None = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        content: bytes = b"",
        text: str = "",
    ) -> None:
        self._payload = payload or {}
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        self.text = text

    def json(self) -> dict[str, object]:
        return self._payload


class FakeClient:
    def __init__(
        self,
        *,
        post_payload: dict[str, object] | None = None,
        get_response: FakeResponse | None = None,
        fail_times: int = 0,
        status_code: int = 200,
    ) -> None:
        self.post_payload = post_payload or {}
        self.get_response = get_response or FakeResponse(content=b"")
        self.fail_times = fail_times
        self.status_code = status_code
        self.post_calls: list[dict[str, object]] = []
        self.get_calls: list[str] = []

    def post(self, url: str, *, json: dict[str, object], headers: dict[str, str]) -> FakeResponse:
        self.post_calls.append({"url": url, "json": json, "headers": headers})
        if self.fail_times > 0:
            self.fail_times -= 1
            raise httpx.ConnectError("service down")
        return FakeResponse(self.post_payload, status_code=self.status_code, text="backend error")

    def get(self, url: str) -> FakeResponse:
        self.get_calls.append(url)
        return self.get_response


def _fake_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _build_project(tmp_path: Path, monkeypatch) -> ProjectRepository:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))
    repo = ProjectRepository()
    project = repo.create_project(
        ProjectCreate(
            title="Preview System",
            prompt="Create a premium video concept with a highly consistent protagonist and cinematic scene choices.",
            style="cinematic",
            duration_target=30,
            aspect_ratio="16:9",
            character_notes="Female founder, tailored navy jacket, clean hair silhouette, warm confidence.",
            lock_identity=True,
        )
    )
    project.storyboard = generate_storyboard(project)
    repo.save_project(project)
    return repo


def test_preview_generator_factory_supports_aliases(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("PREVIEW_BACKEND", "external")
    assert isinstance(get_preview_generator(get_settings()), ExternalGenericPreviewGenerator)

    monkeypatch.setenv("PREVIEW_BACKEND", "real")
    assert isinstance(get_preview_generator(get_settings()), RealProviderPreviewGenerator)

    assert normalize_preview_backend("mock") == "mock"
    assert normalize_preview_backend("external") == "external_generic"
    assert normalize_preview_backend("real_provider") == "real_provider"


def test_prompt_builder_includes_pro_sections(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch)
    project = repo.list_projects()[0]
    scene = project.storyboard.scenes[0]

    prompt = PromptBuilder().build_scene_preview_prompt(project, scene, variant_index=2)

    assert "Subject identity consistency:" in prompt.positive_prompt
    assert "Lens feel:" in prompt.positive_prompt
    assert "Wardrobe continuity:" in prompt.positive_prompt
    assert "identity drift" in prompt.negative_prompt
    assert prompt.style_notes is not None


def test_mock_preview_generation_persists_metadata(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch)
    project = repo.list_projects()[0]

    project = generate_previews(project, variants_per_scene=2)
    repo.save_project(project)
    stored = repo.get_project(project.id)
    preview = stored.storyboard.scenes[0].previews[0]

    assert preview.generation_backend == "mock"
    assert preview.generation_mode == "mock"
    assert preview.positive_prompt
    assert preview.negative_prompt
    assert preview.prompt_signature
    assert preview.generation_duration_ms is not None
    assert preview.identity_strength_label in {"basso", "medio", "alto"}
    assert preview.relative_path.startswith(f"previews/{project.id}/scene-1/")


def test_real_provider_preview_generator_persists_real_asset(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch)
    project = repo.list_projects()[0]
    scene = project.storyboard.scenes[0]
    payload = {
        "image_base64": b64encode(_fake_png()).decode("ascii"),
        "mime_type": "image/png",
        "seed": 42,
        "model_name": "preview-xl",
    }

    monkeypatch.setenv("PREVIEW_BACKEND", "real_provider")
    monkeypatch.setenv("PREVIEW_EXTERNAL_URL", "https://preview.example/generate")
    settings = get_settings()
    generator = RealProviderPreviewGenerator(
        settings,
        fallback_generator=MockPreviewGenerator(settings),
        client=FakeClient(post_payload=payload),
    )

    preview, summary = generator.generate_preview(project, scene, 2)

    assert preview.generation_backend == "real_provider"
    assert preview.generation_mode == "real"
    assert preview.seed == 42
    assert preview.model_name == "preview-xl"
    assert preview.relative_path.endswith(".png")
    assert preview.configured_backend == "real_provider"
    assert summary.active_backend == "real_provider"


def test_external_generic_preview_falls_back_to_mock(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch)
    project = repo.list_projects()[0]
    scene = project.storyboard.scenes[0]

    monkeypatch.setenv("PREVIEW_BACKEND", "external_generic")
    monkeypatch.setenv("PREVIEW_EXTERNAL_URL", "https://preview.example/generate")
    monkeypatch.setenv("PREVIEW_EXTERNAL_MAX_RETRIES", "2")
    settings = get_settings()
    generator = ExternalGenericPreviewGenerator(
        settings,
        fallback_generator=MockPreviewGenerator(settings),
        client=FakeClient(fail_times=3),
    )

    preview, summary = generator.generate_preview(project, scene, 1)

    assert preview.generation_backend == "mock"
    assert preview.generation_mode == "mock_fallback"
    assert preview.status == "fallback_to_mock"
    assert preview.retry_count == 2
    assert summary.configured_backend == "external_generic"
    assert summary.generation_mode == "mock_fallback"
    assert summary.message is not None


def test_error_without_fallback_raises(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch)
    project = repo.list_projects()[0]
    scene = project.storyboard.scenes[0]

    monkeypatch.setenv("PREVIEW_BACKEND", "real_provider")
    monkeypatch.setenv("PREVIEW_EXTERNAL_URL", "https://preview.example/generate")
    monkeypatch.setenv("PREVIEW_FALLBACK_TO_MOCK", "false")
    settings = get_settings()
    generator = RealProviderPreviewGenerator(settings, fallback_generator=None, client=FakeClient(status_code=503))

    with pytest.raises(PreviewGenerationError):
      generator.generate_preview(project, scene, 1)


def test_select_scene_preview_remains_explicit_with_new_metadata(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch)
    project = generate_previews(repo.list_projects()[0], variants_per_scene=3)
    scene = project.storyboard.scenes[0]

    updated = select_scene_preview(project, scene.id, scene.previews[2].id)

    assert updated.storyboard.scenes[0].selected_preview_id == scene.previews[2].id


def test_scene_regeneration_replaces_only_target_scene(tmp_path: Path, monkeypatch) -> None:
    repo = _build_project(tmp_path, monkeypatch)
    project = generate_previews(repo.list_projects()[0], variants_per_scene=2)
    first_scene_before = [preview.id for preview in project.storyboard.scenes[0].previews]
    second_scene_before = [preview.id for preview in project.storyboard.scenes[1].previews]

    regenerated = generate_previews(project, variants_per_scene=1, scene_id=project.storyboard.scenes[0].id)

    assert len(regenerated.storyboard.scenes[0].previews) == 1
    assert regenerated.storyboard.scenes[0].preview_revision == 2
    assert [preview.id for preview in regenerated.storyboard.scenes[0].previews] != first_scene_before
    assert [preview.id for preview in regenerated.storyboard.scenes[1].previews] == second_scene_before
    assert regenerated.storyboard.scenes[0].selected_preview_id == regenerated.storyboard.scenes[0].previews[0].id
