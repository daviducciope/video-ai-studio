from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
import json

from app.core.config import get_settings
from app.schemas.project import OutputAsset, Project, ProjectCreate, RenderJob


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
        project = Project(
            id=str(uuid4()),
            title=payload.title,
            prompt=payload.prompt,
            style=payload.style,
            duration_target=payload.duration_target,
            aspect_ratio=payload.aspect_ratio,
            avatar_notes=payload.avatar_notes,
            status="draft",
            created_at=now,
            updated_at=now,
        )
        self.save_project(project)
        return project

    def save_project(self, project: Project) -> Project:
        project.updated_at = datetime.now(UTC)
        self._path(project.id).write_text(
            project.model_dump_json(indent=2),
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
        return Project.model_validate(raw)
