from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.project import PreviewRequest, Project, ProjectCreate, SceneSelectionRequest
from app.services.creative import generate_storyboard
from app.services.pipeline import generate_previews, run_render, select_scene_preview
from app.services.repository import ProjectRepository

router = APIRouter()


def _repo() -> ProjectRepository:
    return ProjectRepository()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/projects", response_model=Project)
def create_project(payload: ProjectCreate) -> Project:
    return _repo().create_project(payload)


@router.get("/projects", response_model=list[Project])
def list_projects() -> list[Project]:
    return _repo().list_projects()


@router.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    try:
        return _repo().get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.post("/projects/{project_id}/storyboard", response_model=Project)
def create_storyboard(project_id: str) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    project.storyboard = generate_storyboard(project)
    project.status = "storyboard_ready"
    return repo.save_project(project)


@router.post("/projects/{project_id}/previews", response_model=Project)
def create_previews(project_id: str, payload: PreviewRequest) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    try:
        project = generate_previews(project, variants_per_scene=payload.variants_per_scene)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return repo.save_project(project)


@router.post("/projects/{project_id}/scenes/{scene_id}/select", response_model=Project)
def select_preview(project_id: str, scene_id: str, payload: SceneSelectionRequest) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    try:
        project = select_scene_preview(project, scene_id=scene_id, preview_id=payload.preview_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return repo.save_project(project)


@router.post("/projects/{project_id}/render", response_model=Project)
def render_project(project_id: str) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    project = repo.start_render_job(project)
    try:
        rendered_project, logs = run_render(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return repo.update_outputs(rendered_project, rendered_project.outputs, logs)


@router.get("/projects/{project_id}/render-status")
def render_status(project_id: str) -> dict[str, object]:
    try:
        project = _repo().get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    return {
        "project_id": project.id,
        "status": project.render_job.status if project.render_job else "idle",
        "logs": project.render_job.logs if project.render_job else [],
        "outputs": project.outputs,
    }


@router.get("/projects/{project_id}/outputs")
def outputs(project_id: str) -> dict[str, object]:
    try:
        project = _repo().get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    return {"project_id": project.id, "outputs": project.outputs}
