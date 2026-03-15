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


class PreviewAsset(BaseModel):
    id: str
    scene_id: str
    file_name: str
    relative_path: str
    url: str
    resolved_url: str | None = None
    mime_type: str
    prompt: str
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
    previews: list[PreviewAsset] = Field(default_factory=list)


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
    created_at: datetime


class Project(BaseModel):
    id: str
    title: str
    prompt: str
    style: str
    duration_target: int
    aspect_ratio: str
    avatar_notes: str | None = None
    identity_pack: IdentityPack | None = None
    status: str
    storyboard: Storyboard | None = None
    render_job: RenderJob | None = None
    outputs: list[OutputAsset] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
