from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "shared"))

from app.core.config import get_settings
from app.services.rendering import RemoteRenderExecutorStub, get_render_executor
from app.services.storage import LocalStorageAdapter, S3StorageAdapter, StorageError, get_storage_adapter


class FakeS3Client:
    def __init__(self) -> None:
        self.put_calls: list[dict[str, object]] = []
        self.presign_calls: list[dict[str, object]] = []

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)
        return {"ETag": '"mock"'}

    def generate_presigned_url(self, operation_name: str, *, Params: dict[str, str], ExpiresIn: int) -> str:
        self.presign_calls.append(
            {
                "operation_name": operation_name,
                "params": Params,
                "expires_in": ExpiresIn,
            }
        )
        return f"https://example-presigned.local/{Params['Key']}?ttl={ExpiresIn}"


def test_local_storage_adapter_rejects_path_traversal(tmp_path: Path) -> None:
    storage = LocalStorageAdapter(tmp_path)
    with pytest.raises(StorageError):
        storage.save_bytes(relative_path="../escape.txt", content=b"nope")


def test_s3_storage_adapter_uploads_with_private_defaults() -> None:
    client = FakeS3Client()
    storage = S3StorageAdapter(
        bucket_name="video-ai-studio-test",
        region_name="eu-west-1",
        prefix="mvp",
        presigned_url_ttl_seconds=321,
        client=client,
    )

    stored = storage.save_bytes(
        relative_path="assets/project-1/asset.png",
        content=b"png-bytes",
        content_type="image/png",
        metadata={"project-id": "project-1"},
    )
    resolved_url = storage.resolve_url(relative_path=stored.relative_path)

    assert stored.relative_path == "assets/project-1/asset.png"
    assert stored.storage_key == "mvp/assets/project-1/asset.png"
    assert client.put_calls[0]["ServerSideEncryption"] == "AES256"
    assert client.put_calls[0]["ContentType"] == "image/png"
    assert client.put_calls[0]["Metadata"] == {"project-id": "project-1"}
    assert client.presign_calls[0]["operation_name"] == "get_object"
    assert client.presign_calls[0]["params"] == {
        "Bucket": "video-ai-studio-test",
        "Key": "mvp/assets/project-1/asset.png",
    }
    assert resolved_url.endswith("ttl=321")


def test_storage_factory_defaults_to_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)

    settings = get_settings()
    storage = get_storage_adapter(settings)

    assert isinstance(storage, LocalStorageAdapter)


def test_render_executor_remote_stub_is_honest(monkeypatch) -> None:
    monkeypatch.setenv("RENDER_BACKEND", "remote_stub")

    executor = get_render_executor(get_settings())

    assert isinstance(executor, RemoteRenderExecutorStub)
    with pytest.raises(NotImplementedError):
        executor.assert_ready()
