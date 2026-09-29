"""
Storage abstraction — local filesystem with S3-ready interface.
All paths are sanitized; no user-controlled paths escape the storage root.
"""
import os
import re
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from app.core.config import settings
from loguru import logger

_storage_root = Path(settings.LOCAL_STORAGE_PATH).resolve()


def _sanitize_filename(name: str) -> str:
    """Remove any dangerous path components."""
    name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", name)
    name = name.lstrip(".")
    return name or "file"


def _make_path(owner_id: str, project_id: str, filename: str) -> Path:
    safe_owner = _sanitize_filename(owner_id)
    safe_project = _sanitize_filename(project_id)
    safe_file = _sanitize_filename(filename)
    path = _storage_root / safe_owner / safe_project / safe_file
    # Ensure the resolved path is still within storage root (path traversal guard)
    path.resolve().relative_to(_storage_root)
    return path


async def save_file(
    data: bytes,
    owner_id: str,
    project_id: str,
    filename: str,
    subdir: str = "",
) -> tuple[str, str]:
    """Save bytes to local storage. Returns (file_path, public_url)."""
    ext = Path(filename).suffix or ".bin"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    if subdir:
        path = _storage_root / _sanitize_filename(owner_id) / _sanitize_filename(project_id) / _sanitize_filename(subdir) / unique_name
    else:
        path = _storage_root / _sanitize_filename(owner_id) / _sanitize_filename(project_id) / unique_name

    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)

    # Public URL relative to backend static mount
    rel = path.relative_to(_storage_root)
    url = f"/storage/{rel.as_posix()}"
    logger.debug(f"Saved file: {path} -> {url}")
    return str(path), url


def get_file_path(url: str) -> Optional[Path]:
    """Reverse a storage URL to an absolute path."""
    if not url.startswith("/storage/"):
        return None
    rel = url[len("/storage/"):]
    path = (_storage_root / rel).resolve()
    try:
        path.relative_to(_storage_root)
    except ValueError:
        return None
    return path if path.exists() else None


def ensure_storage_dirs():
    _storage_root.mkdir(parents=True, exist_ok=True)
    logger.info(f"Storage root: {_storage_root}")
