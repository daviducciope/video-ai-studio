from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "worker"))
sys.path.insert(0, str(ROOT / "packages" / "shared"))

from app.worker import run_preview_job, run_render_job


def test_worker_generates_mock_artifacts(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "data"
    (data_root / "projects").mkdir(parents=True)
    monkeypatch.setenv("DATA_ROOT", str(data_root))
    project = {
        "id": "demo-project",
        "style": "cinematic",
        "storyboard": {
            "refined_title": "Demo Project",
            "script": "Script body",
            "scenes": [
                {
                    "id": "scene-1",
                    "title": "Hook",
                    "voiceover": "Intro",
                    "visual_prompt": "Hero shot",
                }
            ],
        },
    }
    (data_root / "projects" / "demo-project.json").write_text(json.dumps(project), encoding="utf-8")

    preview_result = run_preview_job("demo-project")
    render_result = run_render_job("demo-project")

    assert preview_result["artifacts"]
    assert render_result["artifacts"]
