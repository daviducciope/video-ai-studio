from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from time import monotonic
from typing import Any, Protocol
from uuid import uuid4

import httpx

from app.core.config import Settings, get_settings
from app.schemas.project import IdentityImageAsset, PreviewAsset, Project, Scene
from app.services.preview_prompting import BuiltPreviewPrompt, PromptBuilder
from app.services.storage import LocalStorageAdapter, StorageError, get_storage_adapter

ALLOWED_PREVIEW_MIME_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}
RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


class PreviewGenerationError(RuntimeError):
    """Readable preview generation failure."""


class PreviewBackendError(PreviewGenerationError):
    def __init__(self, message: str, *, retry_count: int = 0) -> None:
        super().__init__(message)
        self.retry_count = retry_count


@dataclass(slots=True)
class PreviewGenerationSummary:
    configured_backend: str
    active_backend: str
    generation_mode: str
    message: str | None = None
    model_name: str | None = None


class PreviewGenerator(Protocol):
    configured_backend: str

    def generate_preview(self, project: Project, scene: Scene, variant_index: int) -> tuple[PreviewAsset, PreviewGenerationSummary]:
        """Generate a single preview asset."""


class MockPreviewGenerator:
    configured_backend = "mock"

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.storage = LocalStorageAdapter(self.settings.data_root)

    def generate_preview(
        self,
        project: Project,
        scene: Scene,
        variant_index: int,
        *,
        prompt_data: BuiltPreviewPrompt | None = None,
        status: str = "generated",
        message: str | None = None,
        retry_count: int = 0,
    ) -> tuple[PreviewAsset, PreviewGenerationSummary]:
        started = monotonic()
        prompt_data = prompt_data or self.prompt_builder.build_scene_preview_prompt(project, scene, variant_index)
        prompt_signature = build_prompt_signature(project, scene, prompt_data, variant_index)
        identity_strength = self.prompt_builder.estimate_identity_strength(
            project,
            active_backend="mock",
            generation_mode="mock_fallback" if status == "fallback_to_mock" else "mock",
        )
        file_stem = uuid4().hex
        relative_path = f"previews/{project.id}/{scene.id}/{file_stem}.svg"
        content = self._build_svg_bytes(
            title=project.storyboard.refined_title if project.storyboard else project.title,
            scene_title=scene.title,
            style=project.style,
            prompt=prompt_data.positive_prompt,
            generation_label="Mock Preview",
        )
        stored = self.storage.save_bytes(
            relative_path=relative_path,
            content=content,
            content_type="image/svg+xml",
            metadata={"project-id": project.id, "scene-id": scene.id, "variant-index": str(variant_index)},
        )
        duration_ms = int((monotonic() - started) * 1000)
        preview = PreviewAsset(
            id=str(uuid4()),
            scene_id=scene.id,
            file_name=stored.file_name,
            relative_path=stored.relative_path,
            url=f"/files/{stored.relative_path}",
            resolved_url=f"/files/{stored.relative_path}",
            mime_type="image/svg+xml",
            prompt=prompt_data.positive_prompt,
            source_prompt=prompt_data.source_prompt,
            positive_prompt=prompt_data.positive_prompt,
            negative_prompt=prompt_data.negative_prompt,
            consistency_notes=prompt_data.consistency_notes,
            identity_constraints=prompt_data.identity_constraints,
            camera_notes=prompt_data.camera_notes,
            lens_notes=prompt_data.lens_notes,
            lighting_notes=prompt_data.lighting_notes,
            wardrobe_notes=prompt_data.wardrobe_notes,
            mood_notes=prompt_data.mood_notes,
            background_notes=prompt_data.background_notes,
            style_notes=prompt_data.style_notes,
            configured_backend=self.configured_backend,
            generation_backend="mock",
            generation_mode="mock_fallback" if status == "fallback_to_mock" else "mock",
            variant_index=variant_index,
            retry_count=retry_count,
            fallback_reason=message if status == "fallback_to_mock" else None,
            prompt_signature=prompt_signature,
            generation_duration_ms=duration_ms,
            identity_strength_score=identity_strength.score,
            identity_strength_label=identity_strength.label,
            identity_strength_reason=identity_strength.reason,
            status=status,
            created_at=datetime.now(UTC),
        )
        return preview, PreviewGenerationSummary(
            configured_backend=self.configured_backend,
            active_backend="mock",
            generation_mode=preview.generation_mode,
            message=message,
            model_name="mock-svg",
        )

    def _build_svg_bytes(
        self,
        *,
        title: str,
        scene_title: str,
        style: str,
        prompt: str,
        generation_label: str,
    ) -> bytes:
        safe_prompt = prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines = safe_prompt.splitlines()
        text_lines = []
        for index, line in enumerate(lines[:10]):
            text_lines.append(
                f'<text x="48" y="{188 + index * 22}" fill="#dde7f5" font-family="Verdana, sans-serif" '
                f'font-size="14">{line[:96]}</text>'
            )
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f2135" />
      <stop offset="100%" stop-color="#365e7c" />
    </linearGradient>
  </defs>
  <rect width="960" height="540" fill="url(#bg)" rx="32"/>
  <rect x="28" y="28" width="904" height="484" rx="24" fill="none" stroke="#f3efe6" stroke-opacity="0.2"/>
  <text x="48" y="78" fill="#f3efe6" font-family="Verdana, sans-serif" font-size="28">{title}</text>
  <text x="48" y="118" fill="#f8d49d" font-family="Verdana, sans-serif" font-size="22">{scene_title}</text>
  <text x="48" y="154" fill="#f3efe6" font-family="Verdana, sans-serif" font-size="18">{style}</text>
  {''.join(text_lines)}
  <rect x="624" y="108" width="252" height="176" rx="28" fill="#f3efe6" fill-opacity="0.08"/>
  <circle cx="750" cy="180" r="64" fill="#f8d49d" fill-opacity="0.12" stroke="#f8d49d" stroke-opacity="0.4"/>
  <text x="666" y="330" fill="#f3efe6" font-family="Verdana, sans-serif" font-size="24">{generation_label}</text>
</svg>
"""
        return svg.encode("utf-8")


class HTTPPreviewGeneratorBase:
    configured_backend = "external_generic"
    provider_name = "external_generic"

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        prompt_builder: PromptBuilder | None = None,
        fallback_generator: MockPreviewGenerator | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.fallback_generator = fallback_generator
        timeout = httpx.Timeout(self.settings.preview_external_timeout_seconds)
        self.client = client or httpx.Client(timeout=timeout)
        self.storage = LocalStorageAdapter(self.settings.data_root)

    def generate_preview(self, project: Project, scene: Scene, variant_index: int) -> tuple[PreviewAsset, PreviewGenerationSummary]:
        prompt_data = self.prompt_builder.build_scene_preview_prompt(project, scene, variant_index)
        prompt_signature = build_prompt_signature(project, scene, prompt_data, variant_index)
        if not self.settings.preview_external_url:
            return self._fallback(
                project,
                scene,
                variant_index,
                prompt_data,
                "Preview backend configurato ma PREVIEW_EXTERNAL_URL non e' valorizzato.",
                retry_count=0,
            )

        started = monotonic()
        payload = self._build_payload(project, scene, variant_index, prompt_data, prompt_signature)
        headers = self._build_headers()
        try:
            body, retry_count = self._request_json(
                self.settings.preview_external_url,
                payload=payload,
                headers=headers,
            )
            content, mime_type = self._load_external_content(body)
            extension = extension_from_mime(mime_type)
        except (PreviewBackendError, StorageError) as exc:
            return self._fallback(project, scene, variant_index, prompt_data, str(exc), retry_count=getattr(exc, "retry_count", 0))
        except PreviewGenerationError as exc:
            return self._fallback(project, scene, variant_index, prompt_data, str(exc), retry_count=0)
        except Exception as exc:  # pragma: no cover - defensive boundary
            return self._fallback(project, scene, variant_index, prompt_data, f"Preview backend non disponibile: {exc}", retry_count=0)

        relative_path = f"previews/{project.id}/{scene.id}/{uuid4().hex}{extension}"
        stored = self.storage.save_bytes(
            relative_path=relative_path,
            content=content,
            content_type=mime_type,
            metadata={"project-id": project.id, "scene-id": scene.id, "variant-index": str(variant_index)},
        )
        duration_ms = int((monotonic() - started) * 1000)
        generation_mode = "real"
        identity_strength = self.prompt_builder.estimate_identity_strength(
            project,
            active_backend=self.provider_name,
            generation_mode=generation_mode,
        )
        preview = PreviewAsset(
            id=str(uuid4()),
            scene_id=scene.id,
            file_name=stored.file_name,
            relative_path=stored.relative_path,
            url=f"/files/{stored.relative_path}",
            resolved_url=f"/files/{stored.relative_path}",
            mime_type=mime_type,
            prompt=prompt_data.positive_prompt,
            source_prompt=prompt_data.source_prompt,
            positive_prompt=prompt_data.positive_prompt,
            negative_prompt=prompt_data.negative_prompt,
            consistency_notes=prompt_data.consistency_notes,
            identity_constraints=prompt_data.identity_constraints,
            camera_notes=prompt_data.camera_notes,
            lens_notes=prompt_data.lens_notes,
            lighting_notes=prompt_data.lighting_notes,
            wardrobe_notes=prompt_data.wardrobe_notes,
            mood_notes=prompt_data.mood_notes,
            background_notes=prompt_data.background_notes,
            style_notes=prompt_data.style_notes,
            configured_backend=self.configured_backend,
            generation_backend=self.provider_name,
            generation_mode=generation_mode,
            variant_index=variant_index,
            seed=maybe_int(body.get("seed")),
            model_name=(body.get("model_name") or self.settings.preview_external_model_name or self.provider_name),
            retry_count=retry_count,
            fallback_reason=None,
            prompt_signature=prompt_signature,
            generation_duration_ms=duration_ms,
            identity_strength_score=identity_strength.score,
            identity_strength_label=identity_strength.label,
            identity_strength_reason=identity_strength.reason,
            status="generated",
            created_at=datetime.now(UTC),
        )
        return preview, PreviewGenerationSummary(
            configured_backend=self.configured_backend,
            active_backend=self.provider_name,
            generation_mode=generation_mode,
            message=None,
            model_name=preview.model_name,
        )

    def _build_headers(self) -> dict[str, str]:
        headers = {"X-Preview-Backend": self.provider_name}
        if self.settings.preview_external_api_key:
            headers["Authorization"] = f"Bearer {self.settings.preview_external_api_key}"
        return headers

    def _request_json(
        self,
        url: str,
        *,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> tuple[dict[str, Any], int]:
        max_retries = self.settings.preview_external_max_retries
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.post(url, json=payload, headers=headers)
                status_code = getattr(response, "status_code", 200)
                if status_code in RETRYABLE_STATUS_CODES:
                    raise PreviewBackendError(f"HTTP {status_code} dal backend preview", retry_count=attempt)
                if status_code >= 400:
                    detail = _safe_error_text(response)
                    raise PreviewBackendError(
                        f"Backend preview ha risposto con HTTP {status_code}: {detail}",
                        retry_count=attempt,
                    )
                body = response.json()
                if not isinstance(body, dict):
                    raise PreviewGenerationError("Risposta preview non valida: body JSON non oggetto.")
                return body, attempt
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError, PreviewBackendError) as exc:
                last_error = exc
                if attempt >= max_retries or not _is_retryable_error(exc):
                    break
            except (ValueError, TypeError) as exc:
                last_error = PreviewGenerationError(f"Risposta preview non valida: {exc}")
                break
        raise PreviewBackendError(str(last_error or "Preview backend non raggiungibile."), retry_count=max_retries)

    def _load_external_content(self, body: dict[str, Any]) -> tuple[bytes, str]:
        if body.get("image_base64"):
            try:
                content = b64decode(str(body["image_base64"]))
            except (ValueError, TypeError) as exc:
                raise PreviewGenerationError(f"image_base64 non valido: {exc}") from exc
            mime_type = detect_preview_mime_type(content, body.get("mime_type"))
            return content, mime_type
        if body.get("image_url"):
            return self._download_external_content(str(body["image_url"]), body.get("mime_type"))
        raise PreviewGenerationError("Risposta preview priva di image_base64 o image_url.")

    def _download_external_content(self, url: str, declared_mime_type: Any) -> tuple[bytes, str]:
        max_retries = self.settings.preview_external_max_retries
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.get(url)
                status_code = getattr(response, "status_code", 200)
                if status_code in RETRYABLE_STATUS_CODES:
                    raise PreviewBackendError(
                        f"HTTP {status_code} durante il download immagine preview",
                        retry_count=attempt,
                    )
                if status_code >= 400:
                    raise PreviewBackendError(
                        f"Download immagine preview fallito con HTTP {status_code}",
                        retry_count=attempt,
                    )
                content = getattr(response, "content", b"")
                mime_type = detect_preview_mime_type(content, declared_mime_type or _header_value(response, "content-type"))
                return content, mime_type
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError, PreviewBackendError) as exc:
                last_error = exc
                if attempt >= max_retries or not _is_retryable_error(exc):
                    break
        raise PreviewBackendError(str(last_error or "Download immagine preview non riuscito."), retry_count=max_retries)

    def _fallback(
        self,
        project: Project,
        scene: Scene,
        variant_index: int,
        prompt_data: BuiltPreviewPrompt,
        message: str,
        *,
        retry_count: int,
    ) -> tuple[PreviewAsset, PreviewGenerationSummary]:
        if not self.settings.preview_fallback_to_mock or self.fallback_generator is None:
            raise PreviewGenerationError(message)
        preview, _summary = self.fallback_generator.generate_preview(
            project,
            scene,
            variant_index,
            prompt_data=prompt_data,
            status="fallback_to_mock",
            message=message,
            retry_count=retry_count,
        )
        preview.configured_backend = self.configured_backend
        return preview, PreviewGenerationSummary(
            configured_backend=self.configured_backend,
            active_backend="mock",
            generation_mode="mock_fallback",
            message=message,
            model_name="mock-svg",
        )

    def _build_payload(
        self,
        project: Project,
        scene: Scene,
        variant_index: int,
        prompt_data: BuiltPreviewPrompt,
        prompt_signature: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class ExternalGenericPreviewGenerator(HTTPPreviewGeneratorBase):
    configured_backend = "external_generic"
    provider_name = "external_generic"

    def _build_payload(
        self,
        project: Project,
        scene: Scene,
        variant_index: int,
        prompt_data: BuiltPreviewPrompt,
        prompt_signature: str,
    ) -> dict[str, Any]:
        return {
            "project_id": project.id,
            "scene_id": scene.id,
            "variant_index": variant_index,
            "model_name": self.settings.preview_external_model_name,
            "prompt_signature": prompt_signature,
            "project": {
                "title": project.title,
                "prompt": project.prompt,
                "style": project.style,
                "aspect_ratio": project.aspect_ratio,
            },
            "scene": {
                "title": scene.title,
                "beat": scene.beat,
                "duration_seconds": scene.duration_seconds,
                "voiceover": scene.voiceover,
            },
            "prompt": {
                "positive": prompt_data.positive_prompt,
                "negative": prompt_data.negative_prompt,
                "consistency_notes": prompt_data.consistency_notes,
                "identity_constraints": prompt_data.identity_constraints,
                "camera_notes": prompt_data.camera_notes,
                "lighting_notes": prompt_data.lighting_notes,
            },
        }


class RealProviderPreviewGenerator(HTTPPreviewGeneratorBase):
    configured_backend = "real_provider"
    provider_name = "real_provider"

    def _build_payload(
        self,
        project: Project,
        scene: Scene,
        variant_index: int,
        prompt_data: BuiltPreviewPrompt,
        prompt_signature: str,
    ) -> dict[str, Any]:
        identity_assets = build_identity_payload(project, self.settings)
        return {
            "request_type": "preview_image",
            "project_id": project.id,
            "scene_id": scene.id,
            "variant_index": variant_index,
            "model_name": self.settings.preview_external_model_name,
            "prompt_signature": prompt_signature,
            "output": {
                "kind": "image",
                "aspect_ratio": project.aspect_ratio,
                "quality": "preview_pro",
            },
            "creative_direction": {
                "project_title": project.title,
                "project_brief": project.prompt,
                "style": project.style,
                "scene_title": scene.title,
                "scene_beat": scene.beat,
                "scene_visual_prompt": scene.visual_prompt,
                "voiceover": scene.voiceover,
            },
            "prompt": {
                "positive_prompt": prompt_data.positive_prompt,
                "negative_prompt": prompt_data.negative_prompt,
                "consistency_instructions": prompt_data.consistency_notes,
                "identity_constraints": prompt_data.identity_constraints,
                "camera_direction": prompt_data.camera_notes,
                "lens_direction": prompt_data.lens_notes,
                "lighting_direction": prompt_data.lighting_notes,
                "wardrobe_direction": prompt_data.wardrobe_notes,
                "mood_direction": prompt_data.mood_notes,
                "background_direction": prompt_data.background_notes,
                "style_finish": prompt_data.style_notes,
            },
            "identity": {
                "lock_identity": bool(project.identity_pack and project.identity_pack.lock_identity),
                "character_notes": project.identity_pack.character_notes if project.identity_pack else project.avatar_notes,
                "primary_image": identity_assets["primary_image"],
                "reference_images": identity_assets["reference_images"],
            },
        }


def build_identity_payload(project: Project, settings: Settings) -> dict[str, Any]:
    if project.identity_pack is None:
        return {"primary_image": None, "reference_images": []}
    storage = get_storage_adapter(settings)
    return {
        "primary_image": _serialize_identity_asset(project.identity_pack.primary_image, settings, storage),
        "reference_images": [
            serialized
            for serialized in (
                _serialize_identity_asset(asset, settings, storage) for asset in project.identity_pack.reference_images
            )
            if serialized is not None
        ],
    }


def _serialize_identity_asset(
    asset: IdentityImageAsset | None,
    settings: Settings,
    storage: Any,
) -> dict[str, Any] | None:
    if asset is None:
        return None
    local_path = settings.data_root / asset.relative_path
    if local_path.exists():
        return {
            "id": asset.id,
            "role": asset.role,
            "mime_type": asset.mime_type,
            "image_base64": b64encode(local_path.read_bytes()).decode("ascii"),
        }
    return {
        "id": asset.id,
        "role": asset.role,
        "mime_type": asset.mime_type,
        "image_url": storage.resolve_url(relative_path=asset.relative_path),
    }


def build_prompt_signature(project: Project, scene: Scene, prompt_data: BuiltPreviewPrompt, variant_index: int) -> str:
    payload = "|".join(
        [
            project.id,
            scene.id,
            str(variant_index),
            prompt_data.positive_prompt,
            prompt_data.negative_prompt,
            prompt_data.consistency_notes,
            prompt_data.camera_notes,
            prompt_data.lighting_notes,
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def detect_preview_mime_type(content: bytes, fallback: Any) -> str:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    if content.lstrip().startswith(b"<svg"):
        return "image/svg+xml"
    fallback_text = str(fallback).split(";")[0].strip().lower() if fallback else ""
    if fallback_text in ALLOWED_PREVIEW_MIME_TYPES:
        return fallback_text
    raise PreviewGenerationError("Il backend preview ha restituito un MIME type non supportato.")


def extension_from_mime(mime_type: str) -> str:
    try:
        return ALLOWED_PREVIEW_MIME_TYPES[mime_type.lower()]
    except KeyError as exc:
        raise PreviewGenerationError(f"MIME type preview non supportato: {mime_type}") from exc


def maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_preview_backend(value: str | None) -> str:
    normalized = (value or "mock").strip().lower()
    alias_map = {
        "mock": "mock",
        "external": "external_generic",
        "external_generic": "external_generic",
        "generic": "external_generic",
        "real": "real_provider",
        "real_provider": "real_provider",
        "provider": "real_provider",
    }
    try:
        return alias_map[normalized]
    except KeyError as exc:
        raise ValueError(f"Preview backend non supportato: {normalized}") from exc


def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, PreviewBackendError):
        message = str(exc)
        return message.startswith("HTTP 408") or message.startswith("HTTP 425") or message.startswith("HTTP 429") or message.startswith("HTTP 500") or message.startswith("HTTP 502") or message.startswith("HTTP 503") or message.startswith("HTTP 504")
    return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError))


def _safe_error_text(response: Any) -> str:
    body_text = getattr(response, "text", "")
    return body_text.strip()[:180] if isinstance(body_text, str) and body_text.strip() else "errore non dettagliato"


def _header_value(response: Any, key: str) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    if hasattr(headers, "get"):
        return headers.get(key)
    return None


def get_preview_generator(settings: Settings | None = None) -> PreviewGenerator:
    current_settings = settings or get_settings()
    backend = normalize_preview_backend(current_settings.preview_backend)
    if backend == "mock":
        return MockPreviewGenerator(current_settings)
    if backend == "external_generic":
        return ExternalGenericPreviewGenerator(
            current_settings,
            fallback_generator=MockPreviewGenerator(current_settings),
        )
    if backend == "real_provider":
        return RealProviderPreviewGenerator(
            current_settings,
            fallback_generator=MockPreviewGenerator(current_settings),
        )
    raise ValueError(f"Preview backend non supportato: {backend}")
