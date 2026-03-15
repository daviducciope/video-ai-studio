from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.project import PreviewAsset, Project
from app.core.config import get_settings
from app.services.rendering import LocalRenderExecutor
from video_ai_shared.mock_media import build_preview_svg


def generate_previews(project: Project, variants_per_scene: int = 1) -> Project:
    settings = get_settings()
    storyboard = project.storyboard
    if storyboard is None:
        raise ValueError("Storyboard missing")

    for scene in storyboard.scenes:
        scene.previews = []
        scene.selected = False
        for variant_index in range(variants_per_scene):
            prompt = f"{scene.visual_prompt} Variant {variant_index + 1}"
            artifact = build_preview_svg(
                output_dir=settings.previews_dir,
                project_id=project.id,
                scene_id=scene.id,
                title=storyboard.refined_title,
                prompt=prompt,
                style=project.style,
            )
            created_at = datetime.now(UTC)
            scene.previews.append(
                PreviewAsset(
                    id=str(uuid4()),
                    scene_id=scene.id,
                    file_name=artifact.file_name,
                    relative_path=artifact.relative_path,
                    url=f"/files/{artifact.relative_path}",
                    resolved_url=f"/files/{artifact.relative_path}",
                    mime_type=artifact.mime_type,
                    prompt=artifact.prompt,
                    status="generated",
                    created_at=created_at,
                )
            )
        if scene.previews:
            scene.selected_preview_id = scene.previews[0].id
    project.status = "previews_ready"
    return project


def select_scene_preview(project: Project, scene_id: str, preview_id: str | None) -> Project:
    storyboard = project.storyboard
    if storyboard is None:
        raise ValueError("Storyboard missing")

    for scene in storyboard.scenes:
        if scene.id != scene_id:
            continue
        if not scene.previews:
            raise ValueError("Scene previews missing")
        selected_preview = preview_id or scene.previews[0].id
        if selected_preview not in {preview.id for preview in scene.previews}:
            raise ValueError("Preview not found")
        scene.selected = True
        scene.selected_preview_id = selected_preview
        return project
    raise ValueError("Scene not found")


def run_render(project: Project) -> tuple[Project, list[str]]:
    return LocalRenderExecutor().run(project)
