from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic, sleep
from typing import Any, Protocol
from uuid import uuid4

import httpx

from app.core.config import Settings, get_settings
from app.schemas.project import IdentityImageAsset, OutputAsset, Project, Scene
from app.services.storage import StorageError, get_storage_adapter
from app.services.video_prompting import BuiltVideoPrompt, VideoPromptBuilder

ALLOWED_VIDEO_MIME_TYPES = {"video/mp4": ".mp4"}
PENDING_VIDEO_STATUSES = {"pending", "processing", "queued", "running"}


class VideoGenerationError(RuntimeError):
    """Readable video generation failure."""


class VideoExpiredError(VideoGenerationError):
    """Provider request expired."""


class VideoTimeoutError(VideoGenerationError):
    """Provider request timed out."""


@dataclass(slots=True)
class VideoGenerationSummary:
    configured_backend: str
    active_backend: str
    generation_mode: str
    provider_status: str
    model_name: str | None
    source_mode: str
    duration_seconds: int
    aspect_ratio: str
    resolution: str
    prompt_used: str
    identity_mode: str
    provider_request_id: str | None = None
    provider_asset_url: str | None = None
    message: str | None = None
    logs: list[str] | None = None


class VideoGenerator(Protocol):
    configured_backend: str

    def generate_project_video(self, project: Project) -> tuple[OutputAsset, VideoGenerationSummary]:
        """Generate a project-level video."""

    def generate_scene_video(self, project: Project, scene: Scene) -> tuple[OutputAsset, VideoGenerationSummary]:
        """Generate a scene-level video clip."""


class MockVideoGenerator:
    configured_backend = "mock"

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        prompt_builder: VideoPromptBuilder | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.prompt_builder = prompt_builder or VideoPromptBuilder(
            default_duration=self.settings.xai_video_default_duration,
            default_resolution=self.settings.xai_video_default_resolution,
            default_aspect_ratio=self.settings.xai_video_default_aspect_ratio,
        )
        self.storage = get_storage_adapter(self.settings)

    def generate_project_video(
        self,
        project: Project,
        *,
        status: str = "done",
        message: str | None = None,
        configured_backend: str | None = None,
    ) -> tuple[OutputAsset, VideoGenerationSummary]:
        prompt_data = self.prompt_builder.build_project_video_prompt(project)
        return self._generate_output(
            project=project,
            scene=None,
            prompt_data=prompt_data,
            status=status,
            message=message,
            configured_backend=configured_backend or self.configured_backend,
        )

    def generate_scene_video(
        self,
        project: Project,
        scene: Scene,
        *,
        status: str = "done",
        message: str | None = None,
        configured_backend: str | None = None,
    ) -> tuple[OutputAsset, VideoGenerationSummary]:
        prompt_data = self.prompt_builder.build_scene_video_prompt(project, scene)
        return self._generate_output(
            project=project,
            scene=scene,
            prompt_data=prompt_data,
            status=status,
            message=message,
            configured_backend=configured_backend or self.configured_backend,
        )

    def _generate_output(
        self,
        *,
        project: Project,
        scene: Scene | None,
        prompt_data: BuiltVideoPrompt,
        status: str,
        message: str | None,
        configured_backend: str,
    ) -> tuple[OutputAsset, VideoGenerationSummary]:
        started = monotonic()
        target_id = scene.id if scene is not None else "project"
        target_label = scene.title if scene is not None else project.title
        relative_path = f"renders/{project.id}/videos/{target_id}-{uuid4().hex}.mp4"
        content = self._build_mock_video_bytes(project=project, label=target_label, prompt_data=prompt_data)
        stored = self.storage.save_bytes(
            relative_path=relative_path,
            content=content,
            content_type="video/mp4",
            metadata={"project-id": project.id, "target-id": target_id, "mode": prompt_data.source_mode},
        )
        now = datetime.now(UTC)
        generation_mode = "mock_fallback" if status == "fallback" else "mock"
        asset = OutputAsset(
            id=str(uuid4()),
            file_name=stored.file_name,
            relative_path=stored.relative_path,
            url=f"/files/{stored.relative_path}",
            resolved_url=f"/files/{stored.relative_path}",
            mime_type="video/mp4",
            summary=f"Mock video clip per {target_label}",
            video_backend="mock",
            video_generation_mode=generation_mode,
            provider_status=status,
            provider_model_name="mock-video",
            source_mode=prompt_data.source_mode,
            duration_seconds=prompt_data.duration_seconds,
            aspect_ratio=prompt_data.aspect_ratio,
            resolution=prompt_data.resolution,
            prompt_used=prompt_data.prompt_used,
            identity_mode=prompt_data.identity_mode,
            fallback_message=message if generation_mode == "mock_fallback" else None,
            created_at=now,
            updated_at=now,
        )
        summary = VideoGenerationSummary(
            configured_backend=configured_backend,
            active_backend="mock",
            generation_mode=generation_mode,
            provider_status=status,
            model_name="mock-video",
            source_mode=prompt_data.source_mode,
            duration_seconds=prompt_data.duration_seconds,
            aspect_ratio=prompt_data.aspect_ratio,
            resolution=prompt_data.resolution,
            prompt_used=prompt_data.prompt_used,
            identity_mode=prompt_data.identity_mode,
            message=message,
            logs=[f"Mock video generated in {int((monotonic() - started) * 1000)} ms"],
        )
        return asset, summary

    def _build_mock_video_bytes(self, *, project: Project, label: str, prompt_data: BuiltVideoPrompt) -> bytes:
        payload = [
            "VIDEO-AI-STUDIO MOCK MP4 PLACEHOLDER",
            f"project={project.id}",
            f"label={label}",
            f"source_mode={prompt_data.source_mode}",
            f"duration_seconds={prompt_data.duration_seconds}",
            f"aspect_ratio={prompt_data.aspect_ratio}",
            f"resolution={prompt_data.resolution}",
            prompt_data.prompt_used,
        ]
        return "\n".join(payload).encode("utf-8")


class XaiVideoGenerator:
    configured_backend = "xai"

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        prompt_builder: VideoPromptBuilder | None = None,
        fallback_generator: MockVideoGenerator | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.prompt_builder = prompt_builder or VideoPromptBuilder(
            default_duration=self.settings.xai_video_default_duration,
            default_resolution=self.settings.xai_video_default_resolution,
            default_aspect_ratio=self.settings.xai_video_default_aspect_ratio,
        )
        self.fallback_generator = fallback_generator
        timeout = httpx.Timeout(self.settings.xai_poll_interval_seconds + 30)
        self.client = client or httpx.Client(timeout=timeout)
        self.storage = get_storage_adapter(self.settings)

    def generate_project_video(self, project: Project) -> tuple[OutputAsset, VideoGenerationSummary]:
        prompt_data = self.prompt_builder.build_project_video_prompt(project)
        return self._generate(project=project, scene=None, prompt_data=prompt_data)

    def generate_scene_video(self, project: Project, scene: Scene) -> tuple[OutputAsset, VideoGenerationSummary]:
        prompt_data = self.prompt_builder.build_scene_video_prompt(project, scene)
        return self._generate(project=project, scene=scene, prompt_data=prompt_data)

    def _generate(
        self,
        *,
        project: Project,
        scene: Scene | None,
        prompt_data: BuiltVideoPrompt,
    ) -> tuple[OutputAsset, VideoGenerationSummary]:
        try:
            self._assert_ready()
            request_payload = self._build_request_payload(project=project, prompt_data=prompt_data)
            request_id = self._submit_generation(request_payload)
            status_body = self._poll_until_complete(request_id)
            video_url = self._extract_video_url(status_body)
            asset = self._download_to_storage(
                project=project,
                scene=scene,
                prompt_data=prompt_data,
                request_id=request_id,
                status_body=status_body,
                video_url=video_url,
            )
            return asset, self._build_summary(prompt_data=prompt_data, request_id=request_id, status_body=status_body, video_url=video_url)
        except (VideoGenerationError, StorageError, httpx.HTTPError) as exc:
            return self._fallback(project=project, scene=scene, message=str(exc))

    def _assert_ready(self) -> None:
        if not self.settings.xai_api_key:
            raise VideoGenerationError("VIDEO_BACKEND=xai ma XAI_API_KEY non e' disponibile.")
        if not self.settings.xai_download_to_storage:
            raise VideoGenerationError("XAI_DOWNLOAD_TO_STORAGE=false non e' supportato in questo step.")

    def _submit_generation(self, payload: dict[str, Any]) -> str:
        response = self.client.post(
            f"{self.settings.xai_api_base_url}/videos/generations",
            json=payload,
            headers=self._headers(),
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict) or not body.get("request_id"):
            raise VideoGenerationError("Risposta xAI non valida: request_id mancante.")
        return str(body["request_id"])

    def _poll_until_complete(self, request_id: str) -> dict[str, Any]:
        deadline = monotonic() + self.settings.xai_poll_timeout_seconds
        last_body: dict[str, Any] | None = None
        while monotonic() <= deadline:
            response = self.client.get(
                f"{self.settings.xai_api_base_url}/videos/{request_id}",
                headers=self._headers(),
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise VideoGenerationError("Risposta polling xAI non valida.")
            status = str(body.get("status") or "").strip().lower()
            last_body = body
            if status == "done":
                return body
            if status == "expired":
                raise VideoExpiredError(f"Richiesta video xAI scaduta: {request_id}.")
            if status and status not in PENDING_VIDEO_STATUSES:
                raise VideoGenerationError(f"Stato video xAI non supportato: {status}.")
            sleep(self.settings.xai_poll_interval_seconds)
        raise VideoTimeoutError(
            f"Timeout polling xAI dopo {int(self.settings.xai_poll_timeout_seconds)} secondi."
            if last_body is None
            else f"Timeout polling xAI con ultimo stato {last_body.get('status')}."
        )

    def _download_to_storage(
        self,
        *,
        project: Project,
        scene: Scene | None,
        prompt_data: BuiltVideoPrompt,
        request_id: str,
        status_body: dict[str, Any],
        video_url: str,
    ) -> OutputAsset:
        response = self.client.get(video_url)
        response.raise_for_status()
        content = response.content
        mime_type = detect_video_mime_type(content, response.headers.get("content-type"))
        extension = ALLOWED_VIDEO_MIME_TYPES[mime_type]
        target_id = scene.id if scene is not None else "project"
        relative_path = f"renders/{project.id}/videos/{target_id}-{uuid4().hex}{extension}"
        stored = self.storage.save_bytes(
            relative_path=relative_path,
            content=content,
            content_type=mime_type,
            metadata={"project-id": project.id, "provider": "xai", "request-id": request_id},
        )
        now = datetime.now(UTC)
        video_info = status_body.get("video") if isinstance(status_body.get("video"), dict) else {}
        return OutputAsset(
            id=str(uuid4()),
            file_name=stored.file_name,
            relative_path=stored.relative_path,
            url=f"/files/{stored.relative_path}",
            resolved_url=f"/files/{stored.relative_path}",
            mime_type=mime_type,
            summary=f"xAI video clip ({prompt_data.source_mode.replace('_', ' ')})",
            video_backend="xai",
            video_generation_mode="real",
            provider_request_id=request_id,
            provider_status=str(status_body.get("status") or "done"),
            provider_model_name=str(status_body.get("model") or self.settings.xai_video_model),
            source_mode=prompt_data.source_mode,
            duration_seconds=maybe_int(video_info.get("duration")) or prompt_data.duration_seconds,
            aspect_ratio=prompt_data.aspect_ratio,
            resolution=prompt_data.resolution,
            prompt_used=prompt_data.prompt_used,
            identity_mode=prompt_data.identity_mode,
            provider_asset_url=video_url,
            created_at=now,
            updated_at=now,
        )

    def _build_summary(
        self,
        *,
        prompt_data: BuiltVideoPrompt,
        request_id: str,
        status_body: dict[str, Any],
        video_url: str,
    ) -> VideoGenerationSummary:
        return VideoGenerationSummary(
            configured_backend=self.configured_backend,
            active_backend="xai",
            generation_mode="real",
            provider_status=str(status_body.get("status") or "done"),
            model_name=str(status_body.get("model") or self.settings.xai_video_model),
            source_mode=prompt_data.source_mode,
            duration_seconds=prompt_data.duration_seconds,
            aspect_ratio=prompt_data.aspect_ratio,
            resolution=prompt_data.resolution,
            prompt_used=prompt_data.prompt_used,
            identity_mode=prompt_data.identity_mode,
            provider_request_id=request_id,
            provider_asset_url=video_url,
            logs=["xAI request accepted", "xAI polling completed", "Video downloaded to configured storage"],
        )

    def _fallback(
        self,
        *,
        project: Project,
        scene: Scene | None,
        message: str,
    ) -> tuple[OutputAsset, VideoGenerationSummary]:
        if not self.settings.video_fallback_to_mock or self.fallback_generator is None:
            raise VideoGenerationError(message)
        if scene is None:
            asset, summary = self.fallback_generator.generate_project_video(
                project,
                status="fallback",
                message=message,
                configured_backend=self.configured_backend,
            )
        else:
            asset, summary = self.fallback_generator.generate_scene_video(
                project,
                scene,
                status="fallback",
                message=message,
                configured_backend=self.configured_backend,
            )
        return asset, summary

    def _build_request_payload(self, *, project: Project, prompt_data: BuiltVideoPrompt) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.settings.xai_video_model,
            "prompt": prompt_data.prompt_used,
            "duration": prompt_data.duration_seconds,
            "aspect_ratio": prompt_data.aspect_ratio,
            "resolution": prompt_data.resolution,
        }
        image = _serialize_primary_image(project, self.settings)
        if image is not None:
            payload["image"] = image
        return payload

    def _extract_video_url(self, body: dict[str, Any]) -> str:
        video = body.get("video")
        if not isinstance(video, dict) or not video.get("url"):
            raise VideoGenerationError("Risposta xAI non valida: video.url mancante.")
        return str(video["url"])

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.xai_api_key}",
            "Content-Type": "application/json",
        }


def _serialize_primary_image(project: Project, settings: Settings) -> dict[str, str] | None:
    identity_pack = project.identity_pack
    if identity_pack is None or identity_pack.primary_image is None:
        return None
    asset = identity_pack.primary_image
    local_path = settings.data_root / asset.relative_path
    if local_path.exists():
        encoded = b64encode(local_path.read_bytes()).decode("ascii")
        return {"url": f"data:{asset.mime_type};base64,{encoded}"}
    return {"url": get_storage_adapter(settings).resolve_url(relative_path=asset.relative_path)}


def maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def detect_video_mime_type(content: bytes, fallback: Any) -> str:
    if len(content) >= 12 and content[4:8] == b"ftyp":
        return "video/mp4"
    fallback_text = str(fallback).split(";")[0].strip().lower() if fallback else ""
    if fallback_text in ALLOWED_VIDEO_MIME_TYPES:
        return fallback_text
    raise VideoGenerationError("Il backend video ha restituito un MIME type non supportato.")


def normalize_video_backend(value: str | None) -> str:
    normalized = (value or "mock").strip().lower()
    alias_map = {
        "mock": "mock",
        "xai": "xai",
        "grok": "xai",
        "grok-imagine-video": "xai",
    }
    try:
        return alias_map[normalized]
    except KeyError as exc:
        raise ValueError(f"Video backend non supportato: {normalized}") from exc


def get_video_generator(settings: Settings | None = None) -> VideoGenerator:
    current_settings = settings or get_settings()
    backend = normalize_video_backend(current_settings.video_backend)
    if backend == "mock":
        return MockVideoGenerator(current_settings)
    if backend == "xai":
        return XaiVideoGenerator(
            current_settings,
            fallback_generator=MockVideoGenerator(current_settings),
        )
    raise ValueError(f"Video backend non supportato: {backend}")
