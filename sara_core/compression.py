"""CORE Compression: bytes compression, decompression, checksums, archive extraction."""
import hashlib
import zlib
from typing import Any, Dict


def core_compress_bytes(data: bytes, level: int = 3) -> bytes:
    """
    CORE-level compression helper.
    CONTROL will choose backend (zstd, zip, etc.).
    CORE provides a stable API surface only.
    """
    raise NotImplementedError("core_compress_bytes backend not wired yet.")


def core_decompress_bytes(blob: bytes) -> bytes:
    """
    CORE-level decompression helper.
    CONTROL will implement backend logic.
    """
    raise NotImplementedError("core_decompress_bytes backend not wired yet.")


def core_detect_compression_format(path: str) -> str:
    """
    Inspect a file and return a best-effort compression format label.
    CONTROL will implement actual detection logic.
    """
    return "unknown"


def core_checksum_bytes(blob: bytes, algorithm: str = "sha256") -> str:
    """
    Return a checksum string for the given bytes.
    CONTROL will implement actual hashing.
    """
    raise NotImplementedError("core_checksum_bytes backend not wired yet.")


def core_extract_full(archive_path: str, output_dir: str) -> Dict[str, Any]:
    """
    CORE-level full extraction helper.
    CONTROL will choose the archive backend and execution path.
    CORE provides a stable API surface only.
    """
    raise NotImplementedError("core_extract_full backend not wired yet.")


def core_extract_target(archive_path: str, target_name: str, output_dir: str = "") -> Dict[str, Any]:
    """
    CORE-level targeted extraction helper.
    CONTROL will implement selective extraction logic.
    """
    raise NotImplementedError("core_extract_target backend not wired yet.")
