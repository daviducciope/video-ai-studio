from __future__ import annotations

from dataclasses import dataclass

from app.schemas.project import Project, Scene


@dataclass(slots=True)
class IdentityStrengthAssessment:
    score: int
    label: str
    reason: str


@dataclass(slots=True)
class BuiltPreviewPrompt:
    source_prompt: str
    positive_prompt: str
    negative_prompt: str
    consistency_notes: str
    identity_constraints: str
    camera_notes: str
    lens_notes: str
    lighting_notes: str
    wardrobe_notes: str
    mood_notes: str
    background_notes: str
    style_notes: str


class PromptBuilder:
    def build_scene_preview_prompt(
        self,
        project: Project,
        scene: Scene,
        variant_index: int,
    ) -> BuiltPreviewPrompt:
        identity_pack = project.identity_pack
        character_notes = (identity_pack.character_notes or project.avatar_notes or "").strip()
        reference_count = len(identity_pack.reference_images) if identity_pack else 0
        has_primary_image = bool(identity_pack and identity_pack.primary_image is not None)
        lock_identity = bool(identity_pack and identity_pack.lock_identity)

        identity_lines = []
        if lock_identity:
            identity_lines.append("locked hero identity; do not redesign the character between scene variants")
        else:
            identity_lines.append("preserve the same recognisable protagonist while allowing only minor pose variation")
        if has_primary_image:
            identity_lines.append("primary face reference available and must anchor facial geometry, hairstyle and silhouette")
        else:
            identity_lines.append("no primary image available; rely on written character bible with extra discipline")
        if reference_count:
            identity_lines.append(f"{reference_count} supporting reference image(s) available for wardrobe continuity and facial consistency")
        else:
            identity_lines.append("no supporting reference gallery available")
        if character_notes:
            identity_lines.append(f"character bible: {character_notes}")

        camera_notes = self._camera_notes(project.aspect_ratio, variant_index)
        lens_notes = self._lens_notes(variant_index)
        lighting_notes = self._lighting_notes(project.style, variant_index)
        wardrobe_notes = self._wardrobe_notes(character_notes, lock_identity)
        mood_notes = self._mood_notes(project.style, scene, variant_index)
        background_notes = self._background_notes(scene, variant_index)
        style_notes = self._style_notes(project.style)
        identity_constraints = (
            "Keep the same face shape, skin tone, hairstyle, age range, body type, wardrobe language and overall persona. "
            "Avoid identity drift, face swaps, inconsistent hair length, costume changes without reason and anatomy shifts."
        )
        consistency_notes = "; ".join(identity_lines)

        positive_sections = [
            f"Project brief: {project.prompt}",
            f"Scene intent: {scene.title}. {scene.beat}",
            f"Scene visual direction: {scene.visual_prompt}",
            f"Subject identity consistency: {consistency_notes}",
            f"Identity constraints: {identity_constraints}",
            f"Wardrobe continuity: {wardrobe_notes}",
            f"Camera framing: {camera_notes}",
            f"Lens feel: {lens_notes}",
            f"Lighting style: {lighting_notes}",
            f"Scene mood: {mood_notes}",
            f"Background discipline: {background_notes}",
            f"Premium finish: {style_notes}",
            f"Variant emphasis: {self._variant_direction(variant_index)}",
            "Output target: premium commercial still frame, cinematic polish, storyboard-ready, credible human subject, clean composition",
        ]
        positive_prompt = "\n".join(section for section in positive_sections if section)

        negative_sections = [
            scene.negative_prompt.strip(),
            "identity drift",
            "different person",
            "face asymmetry",
            "inconsistent hairstyle",
            "age inconsistency",
            "body shape inconsistency",
            "wardrobe mismatch",
            "duplicate subject",
            "extra limbs",
            "deformed hands",
            "bad anatomy",
            "plastic skin",
            "muddy details",
            "flat lighting",
            "overexposed highlights",
            "harsh skin retouching",
            "messy background",
            "busy frame clutter",
            "cheap stock photo look",
            "low-end CGI look",
            "text overlay",
            "caption",
            "watermark",
            "logo",
            "cropped head",
            "out of frame face",
        ]

        source_prompt = "\n\n".join(
            [
                "Positive Prompt",
                positive_prompt,
                "Negative Prompt",
                ", ".join(section for section in negative_sections if section),
            ]
        )

        return BuiltPreviewPrompt(
            source_prompt=source_prompt,
            positive_prompt=positive_prompt,
            negative_prompt=", ".join(section for section in negative_sections if section),
            consistency_notes=consistency_notes,
            identity_constraints=identity_constraints,
            camera_notes=camera_notes,
            lens_notes=lens_notes,
            lighting_notes=lighting_notes,
            wardrobe_notes=wardrobe_notes,
            mood_notes=mood_notes,
            background_notes=background_notes,
            style_notes=style_notes,
        )

    def estimate_identity_strength(
        self,
        project: Project,
        *,
        active_backend: str,
        generation_mode: str,
    ) -> IdentityStrengthAssessment:
        identity_pack = project.identity_pack
        reference_count = len(identity_pack.reference_images) if identity_pack else 0
        has_primary_image = bool(identity_pack and identity_pack.primary_image is not None)
        lock_identity = bool(identity_pack and identity_pack.lock_identity)
        character_notes = (identity_pack.character_notes or project.avatar_notes or "").strip()

        score = 18
        reasons = []

        if has_primary_image:
            score += 32
            reasons.append("primary image presente")
        else:
            reasons.append("manca primary image")

        if reference_count:
            score += min(reference_count, 4) * 9
            reasons.append(f"{reference_count} reference image")
        else:
            reasons.append("nessuna reference image")

        if lock_identity:
            score += 12
            reasons.append("identity lock attivo")

        if character_notes:
            score += 10 if len(character_notes) >= 60 else 5
            reasons.append("character notes utili")

        if active_backend == "mock":
            score -= 8
            reasons.append("preview effettiva mock")
        else:
            score += 8
            reasons.append("backend immagine reale")

        if generation_mode == "mock_fallback":
            score -= 15
            reasons.append("fallback attivo")

        score = max(0, min(100, score))
        if score >= 75:
            label = "alto"
        elif score >= 45:
            label = "medio"
        else:
            label = "basso"

        return IdentityStrengthAssessment(score=score, label=label, reason=", ".join(reasons[:4]))

    def build_negative_prompt(self, project: Project, scene: Scene) -> str:
        return self.build_scene_preview_prompt(project=project, scene=scene, variant_index=1).negative_prompt

    def _camera_notes(self, aspect_ratio: str, variant_index: int) -> str:
        camera_options = [
            "hero medium shot, stable eye-line, clean subject separation, deliberate negative space",
            "medium wide cinematic frame, strong depth layering, foreground guide elements, readable silhouette",
            "tight portrait framing, premium editorial balance, confident subject placement, face clearly unobstructed",
        ]
        ratio_guidance = (
            "vertical composition optimised for mobile-first delivery"
            if aspect_ratio == "9:16"
            else "horizontal composition optimised for cinematic delivery"
        )
        return f"{camera_options[(variant_index - 1) % len(camera_options)]}; {ratio_guidance}"

    def _lens_notes(self, variant_index: int) -> str:
        lens_options = [
            "natural 50mm feel with flattering proportions and restrained depth of field",
            "35mm cinematic feel with gentle environmental context and premium perspective control",
            "85mm portrait feel with elegant compression and crisp facial readability",
        ]
        return lens_options[(variant_index - 1) % len(lens_options)]

    def _lighting_notes(self, style: str, variant_index: int) -> str:
        lighting_options = [
            "soft key light, subtle rim separation, dimensional face modelling, controlled highlight roll-off",
            "directional cinematic light, shaped shadows, premium specular control, rich depth without crushed blacks",
            "clean commercial beauty lighting, natural skin tones, polished contrast, expensive but believable finish",
        ]
        return f"{lighting_options[(variant_index - 1) % len(lighting_options)]}; stay consistent with {style.lower()} style"

    def _wardrobe_notes(self, character_notes: str, lock_identity: bool) -> str:
        if character_notes:
            return f"carry forward the wardrobe language from the identity pack: {character_notes}"
        if lock_identity:
            return "keep wardrobe highly consistent across scenes and variants"
        return "keep wardrobe coherent with the project brief and avoid abrupt costume changes"

    def _mood_notes(self, style: str, scene: Scene, variant_index: int) -> str:
        mood_options = [
            "calm confidence with high-end brand energy",
            "purposeful momentum with cinematic clarity",
            "intimate premium focus with emotional precision",
        ]
        return f"{mood_options[(variant_index - 1) % len(mood_options)]}; emotional tone should support {style.lower()} and scene beat {scene.beat.lower()}"

    def _background_notes(self, scene: Scene, variant_index: int) -> str:
        if variant_index == 1:
            return f"background should support {scene.title.lower()} without stealing attention from the protagonist"
        if variant_index == 2:
            return "background should add depth cues and context but remain disciplined, uncluttered and brand-safe"
        return "background should stay elegant, minimal and coherent, with no distracting secondary subjects"

    def _style_notes(self, style: str) -> str:
        return (
            f"{style} premium commercial look, cinematic polish, refined color separation, believable skin texture, "
            "clean production design and premium post-production finish"
        )

    def _variant_direction(self, variant_index: int) -> str:
        variant_options = [
            "balanced hero frame optimised for clarity and approval speed",
            "more dynamic composition with stronger diagonals and controlled motion energy",
            "closer emotional read with identity-first storytelling and stronger facial presence",
        ]
        return variant_options[(variant_index - 1) % len(variant_options)]
