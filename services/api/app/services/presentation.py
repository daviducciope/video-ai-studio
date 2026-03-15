from __future__ import annotations

from app.schemas.project import IdentityPack, Project
from app.services.storage import StorageAdapter


def resolve_identity_pack_urls(identity_pack: IdentityPack | None, storage: StorageAdapter) -> IdentityPack | None:
    if identity_pack is None:
        return None
    if identity_pack.primary_image is not None:
        identity_pack.primary_image.resolved_url = storage.resolve_url(
            relative_path=identity_pack.primary_image.relative_path
        )
    for asset in identity_pack.reference_images:
        asset.resolved_url = storage.resolve_url(relative_path=asset.relative_path)
    return identity_pack


def resolve_project_urls(
    project: Project,
    *,
    asset_storage: StorageAdapter,
    artifact_storage: StorageAdapter,
) -> Project:
    resolve_identity_pack_urls(project.identity_pack, asset_storage)
    if project.storyboard is not None:
        for scene in project.storyboard.scenes:
            for preview in scene.previews:
                preview.resolved_url = artifact_storage.resolve_url(relative_path=preview.relative_path)
    for output in project.outputs:
        output.resolved_url = artifact_storage.resolve_url(relative_path=output.relative_path)
    return project
