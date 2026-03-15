from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.project import Project, Scene, Storyboard


def generate_storyboard(project: Project) -> Storyboard:
    refined_title = f"{project.title} | {project.style.title()} Cut"
    total_duration = project.duration_target
    beats = [
        ("Hook", "Apertura immediata e memorabile"),
        ("Setup", "Introduzione del contesto e del valore"),
        ("Proof", "Dimostrazione concreta o trasformazione"),
        ("Close", "Call to action e payoff finale"),
    ]
    scene_duration = max(5, total_duration // len(beats))
    scenes = []
    for index, (scene_title, beat) in enumerate(beats, start=1):
        scene_id = f"scene-{index}"
        scenes.append(
            Scene(
                id=scene_id,
                title=scene_title,
                beat=beat,
                duration_seconds=scene_duration,
                visual_prompt=(
                    f"{project.prompt}. Scene focus: {beat}. "
                    f"Visual style {project.style}, aspect ratio {project.aspect_ratio}."
                ),
                negative_prompt="blurry, distorted face, inconsistent lighting, unreadable text",
                voiceover=(
                    f"{scene_title}: porta avanti il messaggio principale del progetto "
                    f"con tono {project.style.lower()}."
                ),
            )
        )

    script = " ".join(scene.voiceover for scene in scenes)
    overview = (
        f"Storyboard in 4 scene per un video {project.aspect_ratio} di circa "
        f"{project.duration_target} secondi."
    )
    return Storyboard(
        refined_title=refined_title,
        script=script,
        overview=overview,
        scenes=scenes,
        generated_at=datetime.now(UTC),
    )
