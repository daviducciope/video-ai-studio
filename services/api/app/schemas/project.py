from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    prompt: str = Field(min_length=10, max_length=1200)
    style: str = Field(min_length=3, max_length=120)
    duration_target: int = Field(ge=15, le=300)
    aspect_ratio: str = Field(pattern=r"^(9:16|16:9)$")
    avatar_notes: str | None = Field(default=None, max_length=400)
    character_notes: str | None = Field(default=None, max_length=2000)
    lock_identity: bool = False


class PreviewRequest(BaseModel):
    variants_per_scene: int = Field(default=1, ge=1, le=3)


class SceneSelectionRequest(BaseModel):
    preview_id: str | None = None


class VideoGenerationRequest(BaseModel):
    fallback_to_mock: bool | None = None


class PreviewAsset(BaseModel):
    id: str
    scene_id: str
    file_name: str
    relative_path: str
    url: str
    resolved_url: str | None = None
    mime_type: str
    prompt: str
    source_prompt: str | None = None
    positive_prompt: str | None = None
    negative_prompt: str | None = None
    consistency_notes: str | None = None
    identity_constraints: str | None = None
    camera_notes: str | None = None
    lens_notes: str | None = None
    lighting_notes: str | None = None
    wardrobe_notes: str | None = None
    mood_notes: str | None = None
    background_notes: str | None = None
    style_notes: str | None = None
    configured_backend: str = "mock"
    generation_backend: str = "mock"
    generation_mode: str = "mock"
    variant_index: int = 1
    seed: int | None = None
    model_name: str | None = None
    retry_count: int = 0
    fallback_reason: str | None = None
    prompt_signature: str | None = None
    generation_duration_ms: int | None = None
    identity_strength_score: int | None = None
    identity_strength_label: str | None = None
    identity_strength_reason: str | None = None
    status: str
    created_at: datetime


class IdentityImageAsset(BaseModel):
    id: str
    file_name: str
    relative_path: str
    url: str
    resolved_url: str | None = None
    mime_type: str
    size_bytes: int
    role: str
    created_at: datetime


class IdentityPack(BaseModel):
    primary_image: IdentityImageAsset | None = None
    reference_images: list[IdentityImageAsset] = Field(default_factory=list)
    character_notes: str | None = None
    lock_identity: bool = False
    created_at: datetime
    updated_at: datetime


class Scene(BaseModel):
    id: str
    title: str
    beat: str
    visual_prompt: str
    negative_prompt: str
    voiceover: str
    duration_seconds: int
    selected: bool = False
    selected_preview_id: str | None = None
    preview_revision: int = 0
    preview_history_note: str | None = None
    last_previews_generated_at: datetime | None = None
    previews: list[PreviewAsset] = Field(default_factory=list)
    generated_video: OutputAsset | None = None


class Storyboard(BaseModel):
    refined_title: str
    script: str
    overview: str
    scenes: list[Scene]
    generated_at: datetime


class RenderJob(BaseModel):
    id: str
    status: str
    logs: list[str] = Field(default_factory=list)
    output_asset_ids: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class OutputAsset(BaseModel):
    id: str
    file_name: str
    relative_path: str
    url: str
    resolved_url: str | None = None
    mime_type: str
    summary: str
    video_backend: str = "mock"
    video_generation_mode: str = "mock"
    provider_request_id: str | None = None
    provider_status: str | None = None
    provider_model_name: str | None = None
    source_mode: str | None = None
    duration_seconds: int | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    prompt_used: str | None = None
    identity_mode: str | None = None
    fallback_message: str | None = None
    provider_asset_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class VideoJob(BaseModel):
    id: str
    status: str
    target_type: str
    target_id: str
    backend: str
    active_backend: str
    generation_mode: str
    provider_request_id: str | None = None
    provider_status: str | None = None
    logs: list[str] = Field(default_factory=list)
    output_asset_id: str | None = None
    fallback_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class Project(BaseModel):
    id: str
    title: str
    prompt: str
    style: str
    duration_target: int
    aspect_ratio: str
    avatar_notes: str | None = None
    identity_pack: IdentityPack | None = None
    preview_backend: str = "mock"
    preview_backend_effective: str = "mock"
    preview_generation_mode: str = "mock"
    preview_backend_message: str | None = None
    preview_model_name: str | None = None
    preview_last_generated_at: datetime | None = None
    video_backend: str = "mock"
    video_backend_effective: str = "mock"
    video_generation_mode: str = "mock"
    video_backend_message: str | None = None
    video_model_name: str | None = None
    video_last_generated_at: datetime | None = None
    status: str
    storyboard: Storyboard | None = None
    render_job: RenderJob | None = None
    video_job: VideoJob | None = None
    project_video: OutputAsset | None = None
    outputs: list[OutputAsset] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
