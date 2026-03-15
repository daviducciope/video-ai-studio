from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Protocol
from urllib.parse import quote

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings, get_settings


@dataclass(slots=True)
class StoredFile:
    file_name: str
    relative_path: str
    absolute_path: Path | None
    size_bytes: int
    storage_key: str | None = None


class StorageError(RuntimeError):
    """Readable storage failure."""


def _normalize_relative_path(relative_path: str) -> str:
    cleaned = Path(relative_path.strip("/"))
    if cleaned.is_absolute():
        raise StorageError("Il path storage non puo' essere assoluto.")
    parts = [part for part in cleaned.parts if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        raise StorageError("Il path storage contiene segmenti non validi.")
    return Path(*parts).as_posix()


def _join_s3_key(prefix: str, relative_path: str) -> str:
    normalized = _normalize_relative_path(relative_path)
    if not prefix:
        return normalized
    return f"{prefix}/{normalized}"


class StorageAdapter(Protocol):
    def save_bytes(
        self,
        *,
        relative_path: str,
        content: bytes,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StoredFile:
        """Persist bytes and return normalized metadata."""

    def resolve_url(self, *, relative_path: str) -> str:
        """Return a client-consumable URL for reading the file."""


class LocalStorageAdapter:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def save_bytes(
        self,
        *,
        relative_path: str,
        content: bytes,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StoredFile:
        del content_type, metadata
        normalized = Path(_normalize_relative_path(relative_path))
        destination = self.root_dir / normalized
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return StoredFile(
            file_name=destination.name,
            relative_path=normalized.as_posix(),
            absolute_path=destination,
            size_bytes=len(content),
        )

    def resolve_url(self, *, relative_path: str) -> str:
        normalized = _normalize_relative_path(relative_path)
        return f"/files/{quote(normalized)}"


class S3StorageAdapter:
    def __init__(
        self,
        *,
        bucket_name: str,
        region_name: str | None,
        prefix: str = "",
        presigned_url_ttl_seconds: int = 900,
        client: Any | None = None,
    ) -> None:
        if not bucket_name:
            raise StorageError("S3 bucket non configurato.")
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self.presigned_url_ttl_seconds = presigned_url_ttl_seconds
        self.client = client or boto3.session.Session(region_name=region_name).client("s3")

    def save_bytes(
        self,
        *,
        relative_path: str,
        content: bytes,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StoredFile:
        key = _join_s3_key(self.prefix, relative_path)
        extra_args: dict[str, Any] = {
            "Bucket": self.bucket_name,
            "Key": key,
            "Body": content,
            "ServerSideEncryption": "AES256",
        }
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = metadata
        try:
            self.client.put_object(**extra_args)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Upload S3 fallito per '{relative_path}': {exc}") from exc
        return StoredFile(
            file_name=Path(relative_path).name,
            relative_path=_normalize_relative_path(relative_path),
            absolute_path=None,
            size_bytes=len(content),
            storage_key=key,
        )

    def resolve_url(self, *, relative_path: str) -> str:
        key = _join_s3_key(self.prefix, relative_path)
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=self.presigned_url_ttl_seconds,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Presigned URL S3 non disponibile per '{relative_path}': {exc}") from exc


def get_storage_adapter(settings: Settings | None = None) -> StorageAdapter:
    current_settings = settings or get_settings()
    if current_settings.storage_backend == "local":
        return LocalStorageAdapter(current_settings.data_root)
    if current_settings.storage_backend == "s3":
        return S3StorageAdapter(
            bucket_name=current_settings.s3_bucket_name or "",
            region_name=current_settings.aws_region,
            prefix=current_settings.s3_prefix,
            presigned_url_ttl_seconds=current_settings.presigned_url_ttl_seconds,
        )
    raise StorageError(f"Storage backend non supportato: {current_settings.storage_backend}")
