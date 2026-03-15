from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "shared"))

from app.main import app
from app.schemas.project import ProjectCreate
from app.services.creative import generate_storyboard
from app.services.pipeline import generate_previews, run_render, select_scene_preview
from app.services.repository import ProjectRepository


def test_full_backend_flow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))
    repo = ProjectRepository()

    project = repo.create_project(
        ProjectCreate(
            title="Launch Campaign",
            prompt="Create a bold launch video for a wearable AI assistant",
            style="cinematic",
            duration_target=45,
            aspect_ratio="16:9",
            avatar_notes="Confident founder",
        )
    )
    assert project.status == "draft"

    project.storyboard = generate_storyboard(project)
    project.status = "storyboard_ready"
    project = repo.save_project(project)
    assert len(project.storyboard.scenes) == 4

    project = generate_previews(project, variants_per_scene=1)
    project = repo.save_project(project)
    first_scene = project.storyboard.scenes[0]
    assert len(first_scene.previews) == 1

    project = select_scene_preview(project, first_scene.id, first_scene.previews[0].id)
    project = repo.save_project(project)
    assert project.storyboard.scenes[0].selected is True

    project = repo.start_render_job(project)
    rendered_project, logs = run_render(project)
    project = repo.update_outputs(rendered_project, rendered_project.outputs, logs)

    assert project.render_job.status == "completed"
    assert len(project.outputs) == 2
    assert any(route.path == "/projects" for route in app.routes)
