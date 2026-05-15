# sara_security/platform.py
# Extracted from sara_securitygen1.py — platform-specific file scanning (Windows Defender, quarantine).

import os
import glob
import hashlib
import shutil
import subprocess
from datetime import datetime

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_windows_defender_cli():
    candidates = []
    env_pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates.append(os.path.join(env_pf, "Windows Defender", "MpCmdRun.exe"))
    candidates.extend(glob.glob(r"C:\ProgramData\Microsoft\Windows Defender\Platform\*\MpCmdRun.exe"))
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _scan_with_windows_defender(file_path, timeout_sec=45):
    mpcmd = _find_windows_defender_cli()
    if not mpcmd:
        return {"available": False, "status": "not_available", "detail": "MpCmdRun.exe not found"}
    try:
        proc = subprocess.run(
            [mpcmd, "-Scan", "-ScanType", "3", "-File", file_path],
            capture_output=True,
            text=True,
            timeout=max(5, int(timeout_sec)),
            check=False,
        )
        # Defender return codes vary by version, so we inspect output text too.
        out = f"{proc.stdout}\n{proc.stderr}".lower()
        if "found" in out and "threat" in out:
            return {
                "available": True,
                "status": "threat_found",
                "exit_code": proc.returncode,
                "detail": out[-4000:],
            }
        if proc.returncode == 0:
            return {
                "available": True,
                "status": "clean",
                "exit_code": proc.returncode,
                "detail": out[-2000:],
            }
        return {
            "available": True,
            "status": "scan_error",
            "exit_code": proc.returncode,
            "detail": out[-4000:],
        }
    except Exception as e:
        return {"available": True, "status": "scan_exception", "detail": str(e)}


def _quarantine_file(file_path, reason):
    q_dir = os.path.join(os.path.dirname(__file__), "quarantine")
    os.makedirs(q_dir, exist_ok=True)
    base = os.path.basename(file_path)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    q_path = os.path.join(q_dir, f"q_{stamp}_{base}")
    try:
        shutil.move(file_path, q_path)
        return {"moved": True, "quarantine_path": q_path, "reason": reason}
    except Exception as e:
        return {"moved": False, "quarantine_path": None, "reason": f"{reason};quarantine-move-failed:{e}"}


def _scan_file_policy(file_path, file_ext="", is_envoy=False, max_file_bytes=100 * 1024 * 1024):
    if not file_path or not os.path.exists(file_path):
        return {"allowed": False, "reason": "SEC:DENY:file-missing"}

    try:
        size = os.path.getsize(file_path)
    except Exception:
        return {"allowed": False, "reason": "SEC:DENY:size-read-failed"}

    if size <= 0:
        return {"allowed": False, "reason": "SEC:DENY:file-empty", "size": size}
    if size > int(max_file_bytes):
        return {"allowed": False, "reason": "SEC:DENY:file-too-large", "size": size}

    ext = (file_ext or os.path.splitext(file_path)[1] or "").lower()
    denied_exec_exts = {".exe", ".dll", ".bat", ".cmd", ".ps1", ".js", ".vbs", ".scr", ".com", ".msi"}
    if ext in denied_exec_exts:
        return {"allowed": False, "reason": f"SEC:DENY:blocked-ext:{ext}", "size": size}

    if is_envoy:
        # Envoy is an incoming I/O protocol: keep format strict and explicit.
        envoy_allowed = {
            ".json", ".nbs", ".txt", ".md", ".csv", ".pdf", ".docx", ".xlsx", ".xls",
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".zip",
            ".mp4", ".mov", ".avi", ".mkv", ".webm",
            ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
            ".stl", ".obj",
        }
        if ext and ext not in envoy_allowed:
            return {"allowed": False, "reason": f"SEC:DENY:envoy-ext-not-allowed:{ext}", "size": size}

    try:
        with open(file_path, "rb") as f:
            head = f.read(8192)
    except Exception:
        return {"allowed": False, "reason": "SEC:DENY:read-head-failed", "size": size}

    low_head = head.lower()
    bad_markers = [
        b"powershell -", b"cmd.exe", b"<script", b"wscript", b"cscript", b"mshta",
        b"mimikatz", b"invoke-expression", b"downloadstring",
    ]
    for marker in bad_markers:
        if marker in low_head:
            return {"allowed": False, "reason": f"SEC:DENY:signature:{marker.decode('utf-8', errors='ignore')}", "size": size}

    digest = None
    try:
        digest = _sha256_file(file_path)
    except Exception:
        digest = None

    return {
        "allowed": True,
        "reason": "SEC:ALLOW:policy-clean",
        "size": size,
        "sha256": digest,
        "ext": ext,
    }
