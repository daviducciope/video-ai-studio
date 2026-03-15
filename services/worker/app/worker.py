from __future__ import annotations

from pathlib import Path
import json
import os

from video_ai_shared.mock_media import build_preview_svg, build_render_manifest


def _project_path(project_id: str) -> Path:
    data_root = Path(os.getenv("DATA_ROOT", "./data")).resolve()
    return data_root / "projects" / f"{project_id}.json"


def _load_project(project_id: str) -> dict:
    path = _project_path(project_id)
    if not path.exists():
        raise FileNotFoundError(project_id)
    return json.loads(path.read_text(encoding="utf-8"))


def run_preview_job(project_id: str) -> dict[str, object]:
    project = _load_project(project_id)
    storyboard = project.get("storyboard")
    if not storyboard:
        raise ValueError("Storyboard missing")
    data_root = Path(os.getenv("DATA_ROOT", "./data")).resolve()
    previews = []
    for scene in storyboard.get("scenes", []):
        artifact = build_preview_svg(
            output_dir=data_root / "previews",
            project_id=project_id,
            scene_id=scene["id"],
            title=storyboard["refined_title"],
            prompt=scene["visual_prompt"],
            style=project["style"],
        )
        previews.append(artifact.relative_path)
    return {"project_id": project_id, "job": "preview", "artifacts": previews}


def run_render_job(project_id: str) -> dict[str, object]:
    project = _load_project(project_id)
    storyboard = project.get("storyboard")
    if not storyboard:
        raise ValueError("Storyboard missing")
    data_root = Path(os.getenv("DATA_ROOT", "./data")).resolve()
    selected_scenes = [
        {
            "title": scene["title"],
            "voiceover": scene["voiceover"],
            "visual_prompt": scene["visual_prompt"],
        }
        for scene in storyboard.get("scenes", [])
    ]
    artifacts = build_render_manifest(
        output_dir=data_root / "renders",
        project_id=project_id,
        title=storyboard["refined_title"],
        script=storyboard["script"],
        selected_scenes=selected_scenes,
    )
    return {"project_id": project_id, "job": "render", "artifacts": [item.relative_path for item in artifacts]}
