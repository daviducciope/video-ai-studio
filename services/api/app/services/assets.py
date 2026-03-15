from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.schemas.project import IdentityImageAsset, Project
from app.services.storage import StorageAdapter

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_REFERENCE_IMAGES = 8


def _safe_extension(content_type: str) -> str:
    try:
        return ALLOWED_IMAGE_TYPES[content_type]
    except KeyError as exc:
        raise ValueError("Sono supportate solo immagini JPG, PNG, WEBP o GIF.") from exc


def _detect_mime_type(content: bytes, fallback: str | None) -> str:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return "image/gif"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    if fallback in ALLOWED_IMAGE_TYPES:
        return fallback
    raise ValueError("Il file caricato non sembra un'immagine valida.")


async def attach_identity_images(
    *,
    project: Project,
    files: list[UploadFile],
    role: str,
    storage: StorageAdapter,
) -> Project:
    if role not in {"primary", "reference"}:
        raise ValueError("Tipo asset non supportato.")
    if not files:
        raise ValueError("Nessun file caricato.")

    identity_pack = project.identity_pack
    if identity_pack is None:
        raise ValueError("Identity pack non inizializzato.")
    if role == "primary" and len(files) != 1:
        raise ValueError("L'immagine principale deve essere una sola.")
    if role == "reference" and len(identity_pack.reference_images) + len(files) > MAX_REFERENCE_IMAGES:
        raise ValueError("Puoi caricare al massimo 8 immagini reference.")

    stored_assets: list[IdentityImageAsset] = []
    for file in files:
        content = await file.read()
        if not content:
            raise ValueError("Uno dei file caricati e' vuoto.")

        mime_type = _detect_mime_type(content, file.content_type)
        extension = _safe_extension(mime_type)
        asset_id = str(uuid4())
        stored = storage.save_bytes(
            relative_path=Path("assets", project.id, f"{asset_id}{extension}").as_posix(),
            content=content,
            content_type=mime_type,
            metadata={
                "project-id": project.id,
                "asset-role": role,
                "asset-id": asset_id,
            },
        )
        created_at = datetime.now(UTC)
        stored_assets.append(
            IdentityImageAsset(
                id=asset_id,
                file_name=stored.file_name,
                relative_path=stored.relative_path,
                url=f"/files/{stored.relative_path}",
                resolved_url=storage.resolve_url(relative_path=stored.relative_path),
                mime_type=mime_type,
                size_bytes=stored.size_bytes,
                role=role,
                created_at=created_at,
            )
        )

    identity_pack.updated_at = datetime.now(UTC)
    if role == "primary":
        identity_pack.primary_image = stored_assets[0]
    else:
        identity_pack.reference_images.extend(stored_assets)
    project.avatar_notes = identity_pack.character_notes
    return project
