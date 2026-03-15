from __future__ import annotations

from pathlib import Path
import os

from fastapi.testclient import TestClient


def test_full_project_flow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))

    from app.main import app

    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "title": "Launch Campaign",
            "prompt": "Create a bold launch video for a wearable AI assistant",
            "style": "cinematic",
            "duration_target": 45,
            "aspect_ratio": "16:9",
            "avatar_notes": "Confident founder",
        },
    )
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    storyboard_response = client.post(f"/projects/{project_id}/storyboard")
    assert storyboard_response.status_code == 200
    assert len(storyboard_response.json()["storyboard"]["scenes"]) == 4

    preview_response = client.post(f"/projects/{project_id}/previews", json={"variants_per_scene": 1})
    assert preview_response.status_code == 200
    scene = preview_response.json()["storyboard"]["scenes"][0]
    assert len(scene["previews"]) == 1

    select_response = client.post(
        f"/projects/{project_id}/scenes/{scene['id']}/select",
        json={"preview_id": scene["previews"][0]["id"]},
    )
    assert select_response.status_code == 200
    assert select_response.json()["storyboard"]["scenes"][0]["selected"] is True

    render_response = client.post(f"/projects/{project_id}/render")
    assert render_response.status_code == 200
    assert render_response.json()["render_job"]["status"] == "completed"

    outputs_response = client.get(f"/projects/{project_id}/outputs")
    assert outputs_response.status_code == 200
    assert len(outputs_response.json()["outputs"]) == 2
