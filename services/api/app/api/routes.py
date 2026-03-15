from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.project import IdentityPack, PreviewRequest, Project, ProjectCreate, SceneSelectionRequest, VideoGenerationRequest
from app.services.assets import attach_identity_images
from app.services.creative import generate_storyboard
from app.services.pipeline import generate_previews, generate_project_video, generate_scene_video, select_scene_preview
from app.services.presentation import resolve_identity_pack_urls, resolve_project_urls
from app.services.preview_generation import normalize_preview_backend
from app.services.video_generation import normalize_video_backend
from app.services.rendering import get_render_executor
from app.services.repository import ProjectRepository
from app.services.storage import LocalStorageAdapter, StorageError, get_storage_adapter

router = APIRouter()


def _repo() -> ProjectRepository:
    return ProjectRepository()


def _storage():
    return get_storage_adapter(get_settings())


def _artifact_storage() -> LocalStorageAdapter:
    return LocalStorageAdapter(get_settings().data_root)


def _present_project(project: Project) -> Project:
    project.preview_backend = normalize_preview_backend(get_settings().preview_backend)
    project.video_backend = normalize_video_backend(get_settings().video_backend)
    has_identity_assets = bool(
        project.identity_pack
        and (project.identity_pack.primary_image is not None or project.identity_pack.reference_images)
    )
    has_previews = bool(project.storyboard and any(scene.previews for scene in project.storyboard.scenes))
    has_outputs = bool(
        project.outputs
        or project.project_video is not None
        or (project.storyboard and any(scene.generated_video is not None for scene in project.storyboard.scenes))
    )
    if not (has_identity_assets or has_previews or has_outputs):
        return project
    try:
        return resolve_project_urls(project, asset_storage=_storage(), artifact_storage=_artifact_storage())
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/projects", response_model=Project)
def create_project(payload: ProjectCreate) -> Project:
    return _present_project(_repo().create_project(payload))


@router.get("/projects", response_model=list[Project])
def list_projects() -> list[Project]:
    return [_present_project(project) for project in _repo().list_projects()]


@router.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    try:
        return _present_project(_repo().get_project(project_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.get("/projects/{project_id}/assets", response_model=IdentityPack)
def get_project_assets(project_id: str) -> IdentityPack:
    try:
        project = _repo().get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    if project.identity_pack is None:
        raise HTTPException(status_code=404, detail="Identity pack not found")
    if project.identity_pack.primary_image is None and not project.identity_pack.reference_images:
        return project.identity_pack
    try:
        return resolve_identity_pack_urls(project.identity_pack, _storage())
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/projects/{project_id}/assets", response_model=Project)
async def upload_project_assets(
    project_id: str,
    role: str = Form(...),
    files: list[UploadFile] = File(...),
) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    try:
        project = await attach_identity_images(project=project, files=files, role=role, storage=_storage())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return _present_project(repo.save_project(project))


@router.post("/projects/{project_id}/storyboard", response_model=Project)
def create_storyboard(project_id: str) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    project.storyboard = generate_storyboard(project)
    project.status = "storyboard_ready"
    return _present_project(repo.save_project(project))


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
    return _present_project(repo.save_project(project))


@router.post("/projects/{project_id}/scenes/{scene_id}/previews", response_model=Project)
def regenerate_scene_previews(project_id: str, scene_id: str, payload: PreviewRequest) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    try:
        project = generate_previews(project, variants_per_scene=payload.variants_per_scene, scene_id=scene_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _present_project(repo.save_project(project))


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
    return _present_project(repo.save_project(project))


@router.post("/projects/{project_id}/render", response_model=Project)
def render_project(project_id: str) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    executor = get_render_executor(get_settings())
    try:
        executor.assert_ready()
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    project = repo.start_render_job(project)
    try:
        rendered_project, logs = executor.run(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _present_project(repo.update_outputs(rendered_project, rendered_project.outputs, logs))


@router.post("/projects/{project_id}/video", response_model=Project)
def create_project_video(project_id: str, payload: VideoGenerationRequest | None = None) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    try:
        project = generate_project_video(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    del payload
    return _present_project(repo.save_project(project))


@router.post("/projects/{project_id}/scenes/{scene_id}/video", response_model=Project)
def create_scene_video(project_id: str, scene_id: str, payload: VideoGenerationRequest | None = None) -> Project:
    repo = _repo()
    try:
        project = repo.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    try:
        project = generate_scene_video(project, scene_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    del payload
    return _present_project(repo.save_project(project))


@router.get("/projects/{project_id}/render-status")
def render_status(project_id: str) -> dict[str, object]:
    try:
        project = _present_project(_repo().get_project(project_id))
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
        project = _present_project(_repo().get_project(project_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    return {"project_id": project.id, "outputs": project.outputs}
