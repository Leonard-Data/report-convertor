"""S3 storage configuration loaded from environment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class S3Config:
    """Configuration for S3 storage operations."""

    def __init__(
        self,
        bucket: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        folder: str,
        report_folder: str = "",
    ) -> None:
        self.bucket = bucket
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.folder = folder.rstrip("/") + "/"
        self.report_folder = report_folder.rstrip("/") + "/" if report_folder else ""

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> S3Config:
        """Load S3 configuration from .env file.

        Search order:
        1. Explicit path (if provided)
        2. Next to the executable (frozen mode)
        3. Current working directory
        4. Standard dotenv search (walks up from CWD)
        """
        import sys

        if env_path:
            load_dotenv(env_path, override=True)
        else:
            candidates = []
            if getattr(sys, "frozen", False):
                candidates.append(Path(sys.executable).parent / ".env")
            candidates.append(Path.cwd() / ".env")

            loaded = False
            for candidate in candidates:
                if candidate.exists():
                    load_dotenv(candidate, override=True)
                    loaded = True
                    break

            if not loaded:
                load_dotenv(override=True)  # walk up from CWD

        def _require(key: str) -> str:
            value = os_env(key)
            if not value:
                raise ValueError(f"Missing required environment variable: {key}")
            return value

        return cls(
            bucket=_require("S3_BUCKET"),
            region=os_env("S3_REGION") or "us-east-1",
            access_key_id=_require("S3_ACCESS_KEY_ID"),
            secret_access_key=_require("S3_SECRET_ACCESS_KEY"),
            folder=os_env("S3_FOLDER") or "",
            report_folder=os_env("S3_REPORT_FOLDER") or "",
        )

    def full_key(self, filename: str) -> str:
        """Generate full S3 key with folder prefix."""
        return f"{self.folder}{filename}"


def os_env(key: str) -> str:
    """Get environment variable, returns empty string if not set."""
    import os

    return os.environ.get(key, "") or ""
