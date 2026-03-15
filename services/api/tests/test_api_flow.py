from __future__ import annotations

from pathlib import Path
import asyncio
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "shared"))

from app.main import app
from app.schemas.project import ProjectCreate
from app.services.assets import attach_identity_images
from app.services.creative import generate_storyboard
from app.services.pipeline import generate_previews, run_render, select_scene_preview
from app.services.repository import ProjectRepository
from app.services.storage import LocalStorageAdapter


class FakeUploadFile:
    def __init__(self, *, filename: str, content_type: str, payload: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


def _fake_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_full_backend_flow_with_identity_pack(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "data"
    monkeypatch.setenv("DATA_ROOT", str(data_root))
    repo = ProjectRepository()
    storage = LocalStorageAdapter(data_root)

    project = repo.create_project(
        ProjectCreate(
            title="Launch Campaign Hero",
            prompt="Create a bold launch video for a wearable AI assistant with a recognizable founder avatar.",
            style="cinematic",
            duration_target=45,
            aspect_ratio="16:9",
            character_notes="Founder in a navy blazer, warm rim light, highly consistent facial features.",
            lock_identity=True,
        )
    )
    assert project.status == "draft"
    assert project.identity_pack is not None
    assert project.identity_pack.lock_identity is True

    primary_upload = FakeUploadFile(filename="avatar.png", content_type="image/png", payload=_fake_png())
    project = asyncio.run(
        attach_identity_images(project=project, files=[primary_upload], role="primary", storage=storage)
    )
    assert project.identity_pack.primary_image is not None
    assert project.identity_pack.primary_image.relative_path.startswith("assets/")

    reference_uploads = [
        FakeUploadFile(filename="ref-a.png", content_type="image/png", payload=_fake_png()),
        FakeUploadFile(filename="ref-b.png", content_type="image/png", payload=_fake_png()),
    ]
    project = asyncio.run(
        attach_identity_images(project=project, files=reference_uploads, role="reference", storage=storage)
    )
    project = repo.save_project(project)
    assert len(project.identity_pack.reference_images) == 2

    reloaded_project = repo.get_project(project.id)
    assert reloaded_project.identity_pack is not None
    assert reloaded_project.identity_pack.character_notes.startswith("Founder")
    assert reloaded_project.identity_pack.primary_image is not None

    reloaded_project.storyboard = generate_storyboard(reloaded_project)
    reloaded_project.status = "storyboard_ready"
    reloaded_project = repo.save_project(reloaded_project)
    assert len(reloaded_project.storyboard.scenes) == 4

    reloaded_project = generate_previews(reloaded_project, variants_per_scene=3)
    reloaded_project = repo.save_project(reloaded_project)
    first_scene = reloaded_project.storyboard.scenes[0]
    assert len(first_scene.previews) == 3

    selected_preview = first_scene.previews[1]
    reloaded_project = select_scene_preview(reloaded_project, first_scene.id, selected_preview.id)
    reloaded_project = repo.save_project(reloaded_project)
    assert reloaded_project.storyboard.scenes[0].selected_preview_id == selected_preview.id

    reloaded_project = repo.start_render_job(reloaded_project)
    rendered_project, logs = run_render(reloaded_project)
    final_project = repo.update_outputs(rendered_project, rendered_project.outputs, logs)

    assert final_project.render_job.status == "completed"
    assert final_project.status == "ready"
    assert len(final_project.outputs) == 2
    assert any(route.path == "/projects/{project_id}/assets" for route in app.routes)
