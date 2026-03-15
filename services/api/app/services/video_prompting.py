from __future__ import annotations

from dataclasses import dataclass

from app.schemas.project import Project, Scene


@dataclass(slots=True)
class BuiltVideoPrompt:
    source_prompt: str
    prompt_used: str
    negative_prompt: str
    source_mode: str
    identity_mode: str
    duration_seconds: int
    aspect_ratio: str
    resolution: str
    reference_count: int
    has_primary_image: bool


class VideoPromptBuilder:
    def __init__(self, *, default_duration: int, default_resolution: str, default_aspect_ratio: str) -> None:
        self.default_duration = default_duration
        self.default_resolution = default_resolution
        self.default_aspect_ratio = default_aspect_ratio

    def build_project_video_prompt(self, project: Project) -> BuiltVideoPrompt:
        if project.storyboard is None:
            raise ValueError("Storyboard missing")
        overview = project.storyboard.overview
        scene_titles = ", ".join(scene.title for scene in project.storyboard.scenes[:4])
        return self._build_prompt(
            project=project,
            scene=None,
            narrative=f"Project overview: {overview}. Scene anchors: {scene_titles}.",
            duration_seconds=min(project.duration_target, self.default_duration),
        )

    def build_scene_video_prompt(self, project: Project, scene: Scene) -> BuiltVideoPrompt:
        return self._build_prompt(
            project=project,
            scene=scene,
            narrative=f"Scene beat: {scene.beat}. Visual direction: {scene.visual_prompt}. Voiceover: {scene.voiceover}.",
            duration_seconds=max(3, min(scene.duration_seconds, self.default_duration)),
        )

    def _build_prompt(
        self,
        *,
        project: Project,
        scene: Scene | None,
        narrative: str,
        duration_seconds: int,
    ) -> BuiltVideoPrompt:
        identity_pack = project.identity_pack
        character_notes = (identity_pack.character_notes if identity_pack else project.avatar_notes) or ""
        lock_identity = bool(identity_pack and identity_pack.lock_identity)
        has_primary_image = bool(identity_pack and identity_pack.primary_image is not None)
        reference_count = len(identity_pack.reference_images) if identity_pack else 0
        source_mode = "image_to_video" if has_primary_image else "text_to_video"
        identity_mode = "locked_primary_image" if has_primary_image and lock_identity else "primary_image_guided" if has_primary_image else "text_only_identity" if character_notes else "generic"
        aspect_ratio = project.aspect_ratio or self.default_aspect_ratio
        negative_prompt = (
            "avoid identity drift, face swaps, duplicate limbs, abrupt costume changes, "
            "low-detail skin, distorted hands, flicker, strobing, muddy motion, cheap CGI look"
        )

        scene_title = scene.title if scene is not None else project.storyboard.refined_title if project.storyboard else project.title
        sections = [
            f"Create a premium cinematic video clip for '{project.title}'.",
            f"Clip focus: {scene_title}.",
            f"Project brief: {project.prompt}.",
            narrative,
            f"Style direction: {project.style}.",
            f"Target aspect ratio: {aspect_ratio}.",
            f"Target duration: {duration_seconds} seconds.",
            f"Target resolution: {self.default_resolution}.",
        ]
        if character_notes:
            sections.append(f"Character notes: {character_notes}.")
        if lock_identity:
            sections.append("Identity lock is enabled: preserve face, hair silhouette, wardrobe logic and age consistency.")
        if has_primary_image:
            sections.append("Use the primary character image as the visual anchor for identity consistency.")
        if reference_count:
            sections.append(f"Reference image count: {reference_count}; match the same character language and styling cues.")
        sections.append("Visual quality: premium, elegant, physically plausible motion, refined lighting, filmic color separation.")

        prompt_used = "\n".join(sections)
        return BuiltVideoPrompt(
            source_prompt=project.prompt,
            prompt_used=prompt_used,
            negative_prompt=negative_prompt,
            source_mode=source_mode,
            identity_mode=identity_mode,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            resolution=self.default_resolution,
            reference_count=reference_count,
            has_primary_image=has_primary_image,
        )
