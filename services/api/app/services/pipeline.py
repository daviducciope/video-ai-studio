from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.project import Project, Scene, VideoJob
from app.core.config import get_settings
from app.services.preview_generation import PreviewGenerationError, get_preview_generator, normalize_preview_backend
from app.services.rendering import LocalRenderExecutor
from app.services.video_generation import VideoGenerationError, get_video_generator, normalize_video_backend
from uuid import uuid4


def generate_previews(project: Project, variants_per_scene: int = 1, *, scene_id: str | None = None) -> Project:
    settings = get_settings()
    storyboard = project.storyboard
    if storyboard is None:
        raise ValueError("Storyboard missing")

    generator = get_preview_generator(settings)
    scenes_to_generate = storyboard.scenes if scene_id is None else [scene for scene in storyboard.scenes if scene.id == scene_id]
    if scene_id is not None and not scenes_to_generate:
        raise ValueError("Scene not found")

    latest_summary = None
    for scene in scenes_to_generate:
        previous_count = len(scene.previews)
        scene.previews = []
        if scene_id is None:
            scene.selected = False
        for variant_number in range(1, variants_per_scene + 1):
            try:
                preview, summary = generator.generate_preview(project, scene, variant_number)
            except PreviewGenerationError as exc:
                raise ValueError(str(exc)) from exc
            scene.previews.append(preview)
            latest_summary = summary
        if scene.previews:
            scene.selected_preview_id = scene.previews[0].id
            scene.preview_revision += 1
            scene.last_previews_generated_at = datetime.now(UTC)
            if previous_count and scene_id == scene.id:
                scene.preview_history_note = (
                    f"Revisione {scene.preview_revision}: sostituite {previous_count} preview precedenti con {len(scene.previews)} nuove varianti."
                )
            elif previous_count:
                scene.preview_history_note = (
                    f"Revisione {scene.preview_revision}: aggiornate {len(scene.previews)} preview."
                )
            else:
                scene.preview_history_note = (
                    f"Revisione {scene.preview_revision}: generate {len(scene.previews)} preview."
                )
    if latest_summary is not None:
        project.preview_backend = normalize_preview_backend(settings.preview_backend)
        project.preview_backend_effective = latest_summary.active_backend
        project.preview_generation_mode = latest_summary.generation_mode
        project.preview_backend_message = latest_summary.message
        project.preview_model_name = latest_summary.model_name
        project.preview_last_generated_at = datetime.now(UTC)
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


def generate_project_video(project: Project) -> Project:
    settings = get_settings()
    if project.storyboard is None:
        raise ValueError("Storyboard missing")
    generator = get_video_generator(settings)
    started_at = datetime.now(UTC)
    project.video_job = VideoJob(
        id=str(uuid4()),
        status="processing",
        target_type="project",
        target_id=project.id,
        backend=normalize_video_backend(settings.video_backend),
        active_backend="pending",
        generation_mode="pending",
        logs=["Video project job accepted"],
        started_at=started_at,
    )
    try:
        asset, summary = generator.generate_project_video(project)
    except VideoGenerationError as exc:
        project.video_job.status = "failed"
        project.video_job.logs.append(str(exc))
        project.video_job.completed_at = datetime.now(UTC)
        raise ValueError(str(exc)) from exc
    project.project_video = asset
    _apply_video_summary(project, summary=summary, target_scene=None)
    return project


def generate_scene_video(project: Project, scene_id: str) -> Project:
    settings = get_settings()
    if project.storyboard is None:
        raise ValueError("Storyboard missing")
    generator = get_video_generator(settings)
    scene = next((item for item in project.storyboard.scenes if item.id == scene_id), None)
    if scene is None:
        raise ValueError("Scene not found")
    started_at = datetime.now(UTC)
    project.video_job = VideoJob(
        id=str(uuid4()),
        status="processing",
        target_type="scene",
        target_id=scene.id,
        backend=normalize_video_backend(settings.video_backend),
        active_backend="pending",
        generation_mode="pending",
        logs=[f"Scene video job accepted for {scene.title}"],
        started_at=started_at,
    )
    try:
        asset, summary = generator.generate_scene_video(project, scene)
    except VideoGenerationError as exc:
        project.video_job.status = "failed"
        project.video_job.logs.append(str(exc))
        project.video_job.completed_at = datetime.now(UTC)
        raise ValueError(str(exc)) from exc
    scene.generated_video = asset
    _apply_video_summary(project, summary=summary, target_scene=scene)
    return project


def _apply_video_summary(project: Project, *, summary, target_scene: Scene | None) -> None:
    now = datetime.now(UTC)
    project.video_backend = summary.configured_backend
    project.video_backend_effective = summary.active_backend
    project.video_generation_mode = summary.generation_mode
    project.video_backend_message = summary.message
    project.video_model_name = summary.model_name
    project.video_last_generated_at = now
    if project.video_job is not None:
        project.video_job.status = _map_video_job_status(summary.provider_status, summary.generation_mode)
        project.video_job.active_backend = summary.active_backend
        project.video_job.generation_mode = summary.generation_mode
        project.video_job.provider_request_id = summary.provider_request_id
        project.video_job.provider_status = summary.provider_status
        project.video_job.output_asset_id = target_scene.generated_video.id if target_scene is not None else project.project_video.id if project.project_video is not None else None
        project.video_job.fallback_message = summary.message
        if summary.logs:
            project.video_job.logs.extend(summary.logs)
        project.video_job.completed_at = now
    if target_scene is not None and target_scene.generated_video is not None:
        target_scene.generated_video.video_backend = summary.active_backend
        target_scene.generated_video.video_generation_mode = summary.generation_mode
        target_scene.generated_video.provider_request_id = summary.provider_request_id
        target_scene.generated_video.provider_status = summary.provider_status
        target_scene.generated_video.provider_model_name = summary.model_name
        target_scene.generated_video.source_mode = summary.source_mode
        target_scene.generated_video.duration_seconds = summary.duration_seconds
        target_scene.generated_video.aspect_ratio = summary.aspect_ratio
        target_scene.generated_video.resolution = summary.resolution
        target_scene.generated_video.prompt_used = summary.prompt_used
        target_scene.generated_video.identity_mode = summary.identity_mode
        target_scene.generated_video.fallback_message = summary.message
        target_scene.generated_video.updated_at = now
    if target_scene is None and project.project_video is not None:
        project.project_video.video_backend = summary.active_backend
        project.project_video.video_generation_mode = summary.generation_mode
        project.project_video.provider_request_id = summary.provider_request_id
        project.project_video.provider_status = summary.provider_status
        project.project_video.provider_model_name = summary.model_name
        project.project_video.source_mode = summary.source_mode
        project.project_video.duration_seconds = summary.duration_seconds
        project.project_video.aspect_ratio = summary.aspect_ratio
        project.project_video.resolution = summary.resolution
        project.project_video.prompt_used = summary.prompt_used
        project.project_video.identity_mode = summary.identity_mode
        project.project_video.fallback_message = summary.message
        project.project_video.updated_at = now
    project.status = "video_ready"


def _map_video_job_status(provider_status: str, generation_mode: str) -> str:
    if generation_mode == "mock_fallback":
        return "fallback"
    normalized = (provider_status or "").strip().lower()
    if normalized == "expired":
        return "expired"
    if normalized in {"done", "completed", "generated"}:
        return "done"
    if normalized in {"failed", "error"}:
        return "failed"
    if normalized in {"pending", "processing", "queued", "running"}:
        return "processing"
    if generation_mode == "mock":
        return "done"
    return normalized or "done"
