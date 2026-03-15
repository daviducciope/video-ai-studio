from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
import json

from app.core.config import get_settings
from app.schemas.project import IdentityPack, OutputAsset, Project, ProjectCreate, RenderJob
from app.services.preview_generation import normalize_preview_backend


class ProjectRepository:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.projects_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, project_id: str) -> Path:
        return self.settings.projects_dir / f"{project_id}.json"

    def list_projects(self) -> list[Project]:
        projects = [self._load(path) for path in self.settings.projects_dir.glob("*.json")]
        return sorted(projects, key=lambda item: item.updated_at, reverse=True)

    def get_project(self, project_id: str) -> Project:
        path = self._path(project_id)
        if not path.exists():
            raise FileNotFoundError(project_id)
        return self._load(path)

    def create_project(self, payload: ProjectCreate) -> Project:
        now = datetime.now(UTC)
        character_notes = payload.character_notes or payload.avatar_notes
        project = Project(
            id=str(uuid4()),
            title=payload.title,
            prompt=payload.prompt,
            style=payload.style,
            duration_target=payload.duration_target,
            aspect_ratio=payload.aspect_ratio,
            avatar_notes=character_notes,
            identity_pack=IdentityPack(
                character_notes=character_notes,
                lock_identity=payload.lock_identity,
                created_at=now,
                updated_at=now,
            ),
            preview_backend=normalize_preview_backend(self.settings.preview_backend),
            preview_backend_effective="mock",
            preview_generation_mode="mock" if normalize_preview_backend(self.settings.preview_backend) == "mock" else "pending",
            video_backend=(self.settings.video_backend if self.settings.video_backend in {"mock", "xai"} else "mock"),
            video_backend_effective="mock",
            video_generation_mode="mock" if self.settings.video_backend == "mock" else "pending",
            status="draft",
            created_at=now,
            updated_at=now,
        )
        self.save_project(project)
        return project

    def save_project(self, project: Project) -> Project:
        project.updated_at = datetime.now(UTC)
        serialized_project = self._project_for_storage(project)
        self._path(project.id).write_text(
            serialized_project.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return project

    def start_render_job(self, project: Project) -> Project:
        project.render_job = RenderJob(
            id=str(uuid4()),
            status="processing",
            logs=["Render job accepted", "Preparing scene manifest"],
            started_at=datetime.now(UTC),
        )
        project.status = "rendering"
        return self.save_project(project)

    def update_outputs(self, project: Project, outputs: list[OutputAsset], logs: list[str]) -> Project:
        if project.render_job is None:
            raise ValueError("Render job not initialized")
        project.outputs = outputs
        project.render_job.status = "completed"
        project.render_job.output_asset_ids = [item.id for item in outputs]
        project.render_job.logs.extend(logs)
        project.render_job.completed_at = datetime.now(UTC)
        project.status = "ready"
        return self.save_project(project)

    def _load(self, path: Path) -> Project:
        raw = json.loads(path.read_text(encoding="utf-8"))
        project = Project.model_validate(raw)
        if project.identity_pack is None:
            timestamp = project.created_at
            project.identity_pack = IdentityPack(
                character_notes=project.avatar_notes,
                lock_identity=False,
                created_at=timestamp,
                updated_at=timestamp,
            )
        if project.avatar_notes is None and project.identity_pack.character_notes:
            project.avatar_notes = project.identity_pack.character_notes
        if not getattr(project, "video_backend", None):
            project.video_backend = self.settings.video_backend if self.settings.video_backend in {"mock", "xai"} else "mock"
        if not getattr(project, "video_backend_effective", None):
            project.video_backend_effective = "mock"
        if not getattr(project, "video_generation_mode", None):
            project.video_generation_mode = "mock" if project.video_backend == "mock" else "pending"
        return project

    def _project_for_storage(self, project: Project) -> Project:
        sanitized = project.model_copy(deep=True)
        if sanitized.identity_pack is not None:
            if sanitized.identity_pack.primary_image is not None:
                sanitized.identity_pack.primary_image.resolved_url = None
            for asset in sanitized.identity_pack.reference_images:
                asset.resolved_url = None
        if sanitized.storyboard is not None:
            for scene in sanitized.storyboard.scenes:
                for preview in scene.previews:
                    preview.resolved_url = None
                if scene.generated_video is not None:
                    scene.generated_video.resolved_url = None
                    scene.generated_video.provider_asset_url = None
        if sanitized.project_video is not None:
            sanitized.project_video.resolved_url = None
            sanitized.project_video.provider_asset_url = None
        for output in sanitized.outputs:
            output.resolved_url = None
            output.provider_asset_url = None
        return sanitized
