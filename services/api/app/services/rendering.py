from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.schemas.project import OutputAsset, Project
from video_ai_shared.mock_media import build_render_manifest


class RenderExecutor(Protocol):
    def assert_ready(self) -> None:
        """Validate backend readiness before starting a render job."""

    def run(self, project: Project) -> tuple[Project, list[str]]:
        """Execute the render and return updated project outputs plus logs."""


class LocalRenderExecutor:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def assert_ready(self) -> None:
        return None

    def run(self, project: Project) -> tuple[Project, list[str]]:
        storyboard = project.storyboard
        if storyboard is None:
            raise ValueError("Storyboard missing")

        selected_scenes = [
            {
                "title": scene.title,
                "voiceover": scene.voiceover,
                "visual_prompt": scene.visual_prompt,
            }
            for scene in storyboard.scenes
            if scene.selected or scene.selected_preview_id
        ]
        if not selected_scenes:
            selected_scenes = [
                {
                    "title": scene.title,
                    "voiceover": scene.voiceover,
                    "visual_prompt": scene.visual_prompt,
                }
                for scene in storyboard.scenes
            ]

        artifacts = build_render_manifest(
            output_dir=self.settings.renders_dir,
            project_id=project.id,
            title=storyboard.refined_title,
            script=storyboard.script,
            selected_scenes=selected_scenes,
        )
        created_at = datetime.now(UTC)
        outputs = [
            OutputAsset(
                id=str(uuid4()),
                file_name=artifact.file_name,
                relative_path=artifact.relative_path,
                url=f"/files/{artifact.relative_path}",
                resolved_url=f"/files/{artifact.relative_path}",
                mime_type=artifact.mime_type,
                summary=artifact.summary,
                created_at=created_at,
            )
            for artifact in artifacts
        ]
        logs = [
            "Preview selection resolved",
            "Mock render completed",
            f"{len(outputs)} output artifact(s) available",
        ]
        return project.model_copy(update={"outputs": outputs}), logs


class RemoteRenderExecutorStub:
    def assert_ready(self) -> None:
        raise NotImplementedError(
            "RENDER_BACKEND=remote_stub e' solo predisposto in questo step. Nessun render remoto e' stato avviato."
        )

    def run(self, project: Project) -> tuple[Project, list[str]]:
        self.assert_ready()
        return project, []


def get_render_executor(settings: Settings | None = None) -> RenderExecutor:
    current_settings = settings or get_settings()
    if current_settings.render_backend == "local":
        return LocalRenderExecutor(current_settings)
    if current_settings.render_backend == "remote_stub":
        return RemoteRenderExecutorStub()
    raise ValueError(f"Render backend non supportato: {current_settings.render_backend}")
