"""
SARA Control — ControlIngestBufferGuard, ControlSystemStrainBudget, and resource monitoring.
Extracted from sara_controlgen1.py.
"""
import os
import sys
import json
import subprocess
import threading
import importlib
from typing import Any, Dict, Optional

try:
    psutil = importlib.import_module("psutil")
except Exception:
    psutil = None


class ControlIngestBufferGuard:
    """
    Tracks ingest preview buffers so control keeps RAM usage bounded.
    Default policy keeps total in-process preview buffers under 3% of system RAM.
    """
    def __init__(self, max_percent: float = 3.0):
        self.max_percent = max(0.1, float(max_percent))
        total_ram = self._total_ram_bytes()
        self.max_bytes = int(total_ram * (self.max_percent / 100.0))
        self._in_use_bytes = 0
        self._lock = threading.Lock()

    def _total_ram_bytes(self) -> int:
        if psutil is not None:
            try:
                return int(psutil.virtual_memory().total)
            except Exception:
                pass
        return 8 * 1024 * 1024 * 1024

    def try_acquire(self, nbytes: int) -> bool:
        with self._lock:
            if self._in_use_bytes + nbytes > self.max_bytes:
                return False
            self._in_use_bytes += nbytes
            return True

    def release(self, nbytes: int) -> None:
        with self._lock:
            self._in_use_bytes = max(0, self._in_use_bytes - nbytes)

    def usage(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "guard_in_use_bytes": self._in_use_bytes,
                "guard_max_bytes": self.max_bytes,
                "guard_usage_percent": (self._in_use_bytes / self.max_bytes * 100.0) if self.max_bytes > 0 else 0.0,
            }


def _process_memory_percent_con() -> Optional[float]:
    if psutil is None:
        return None
    try:
        rss = psutil.Process(os.getpid()).memory_info().rss
        total = psutil.virtual_memory().total
        if total <= 0:
            return None
        return (rss / total) * 100.0
    except Exception:
        return None


def _process_cpu_percent_con() -> Optional[float]:
    if psutil is None:
        return None
    try:
        proc = psutil.Process(os.getpid())
        proc.cpu_percent(interval=None)
        cpu_count = max(1, int(psutil.cpu_count() or 1))
        return proc.cpu_percent(interval=0.02) / float(cpu_count)
    except Exception:
        return None


def _user_interactive_active_con(idle_threshold_sec: int = 90) -> Optional[bool]:
    """
    Return True when recent local user input is detected.
    Windows-only best effort; returns None when unavailable.
    """
    try:
        if os.name != "nt":
            return None
        import ctypes
        from ctypes import wintypes

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return None
        tick_now = ctypes.windll.kernel32.GetTickCount()
        idle_ms = max(0, int(tick_now - info.dwTime))
        return idle_ms < (max(5, int(idle_threshold_sec)) * 1000)
    except Exception:
        return None


class ControlSystemStrainBudget:
    """Adaptive ingest budget that favors stable desktop behavior over burst speed."""

    def __init__(self, max_percent: float = 3.0):
        self.max_percent = max(0.1, float(max_percent))

    def snapshot(
        self,
        buffer_guard: Optional[ControlIngestBufferGuard] = None,
        interactive_user_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        process_mem_pct = _process_memory_percent_con()
        process_cpu_pct = _process_cpu_percent_con()
        guard_usage = buffer_guard.usage() if buffer_guard is not None else {}
        mode = self._mode_for(
            process_mem_pct=process_mem_pct,
            process_cpu_pct=process_cpu_pct,
            guard_usage_percent=guard_usage.get("guard_usage_percent"),
            interactive_user_active=interactive_user_active,
        )
        return {
            "max_percent": self.max_percent,
            "process_memory_percent": process_mem_pct,
            "process_cpu_percent": process_cpu_pct,
            "interactive_user_active": interactive_user_active,
            "mode": mode,
            **guard_usage,
        }

    def _mode_for(
        self,
        process_mem_pct: Optional[float],
        process_cpu_pct: Optional[float],
        guard_usage_percent: Optional[float],
        interactive_user_active: Optional[bool],
    ) -> str:
        if (
            (process_mem_pct is not None and process_mem_pct >= self.max_percent)
            or (guard_usage_percent is not None and guard_usage_percent >= 90.0)
            or (process_cpu_pct is not None and process_cpu_pct >= 85.0)
        ):
            return "critical"
        if (
            (process_mem_pct is not None and process_mem_pct >= (self.max_percent * 0.75))
            or (guard_usage_percent is not None and guard_usage_percent >= 75.0)
            or (process_cpu_pct is not None and process_cpu_pct >= 65.0)
        ):
            return "constrained"
        if (
            (process_mem_pct is not None and process_mem_pct >= (self.max_percent * 0.5))
            or (guard_usage_percent is not None and guard_usage_percent >= 50.0)
            or (process_cpu_pct is not None and process_cpu_pct >= 40.0)
        ):
            return "pressure"
        if interactive_user_active is True:
            return "pressure"
        return "normal"

    def recommended_worker_count(
        self,
        base_worker_count: int,
        buffer_guard: Optional[ControlIngestBufferGuard] = None,
        interactive_user_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        base_worker_count = max(1, int(base_worker_count))
        snapshot = self.snapshot(buffer_guard, interactive_user_active=interactive_user_active)
        mode = snapshot["mode"]
        if mode == "critical":
            worker_count = 1
        elif mode == "constrained":
            worker_count = min(base_worker_count, 2)
        elif mode == "pressure":
            worker_count = max(1, min(base_worker_count, max(1, base_worker_count // 2)))
        else:
            worker_count = base_worker_count
        return {
            "worker_count": worker_count,
            "mode": mode,
            "snapshot": snapshot,
        }

    def preview_plan(
        self,
        preview_bytes: int,
        ext_l: str,
        buffer_guard: Optional[ControlIngestBufferGuard] = None,
        interactive_user_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        snapshot = self.snapshot(buffer_guard, interactive_user_active=interactive_user_active)
        mode = snapshot["mode"]
        preview_bytes = max(256, int(preview_bytes))
        heavy_preview_exts = {
            ".docx", ".pdf", ".xlsx",
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp",
            ".mp4", ".mov", ".avi", ".mkv", ".webm",
            ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
            ".stl", ".obj",
        }
        if interactive_user_active is True and ext_l in heavy_preview_exts:
            return {
                "mode": "interactive",
                "allow_preview": False,
                "preview_bytes": 0,
                "parser_status": "interactive_metadata_only",
                "offload": False,
                "snapshot": snapshot,
            }
        if mode == "critical":
            return {
                "mode": mode,
                "allow_preview": False,
                "preview_bytes": 0,
                "parser_status": "system_strain_critical",
                "offload": False,
                "snapshot": snapshot,
            }
        if mode == "constrained" and ext_l in heavy_preview_exts:
            return {
                "mode": mode,
                "allow_preview": False,
                "preview_bytes": 0,
                "parser_status": "strain_metadata_only",
                "offload": False,
                "snapshot": snapshot,
            }
        if mode == "constrained":
            preview_bytes = max(256, preview_bytes // 4)
        elif mode == "pressure":
            preview_bytes = max(256, preview_bytes // 2)
        return {
            "mode": mode,
            "allow_preview": True,
            "preview_bytes": preview_bytes,
            "parser_status": "metadata_only",
            "offload": ext_l in heavy_preview_exts,
            "snapshot": snapshot,
        }


def _preview_worker_creationflags_con() -> int:
    flags = 0
    flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
    flags |= getattr(subprocess, "IDLE_PRIORITY_CLASS", 0)
    return flags


def _run_preview_worker_con(local_path: str, ext_l: str, max_chars: int, timeout_sec: int = 20) -> Dict[str, Any]:
    worker_code = """
import json
import re
import sys
import zipfile
import importlib

path = sys.argv[1]
ext_l = sys.argv[2].lower()
max_chars = max(256, int(sys.argv[3]))
result = {"preview": None, "image_meta": {}, "parser_status": "metadata_only"}

try:
    if ext_l == ".docx":
        with zipfile.ZipFile(path, "r") as zf:
            raw = zf.read("word/document.xml")
        text = raw.decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", text)
        text = " ".join(text.split())
        result["preview"] = text[:max_chars] or None
        result["parser_status"] = "preview_docx_offloaded" if result["preview"] else "docx_no_preview"
    elif ext_l == ".pdf":
        pypdf2 = importlib.import_module("PyPDF2")
        with open(path, "rb") as f:
            reader = pypdf2.PdfReader(f)
            if reader.pages:
                text = reader.pages[0].extract_text() or ""
                result["preview"] = text[:max_chars] or None
        result["parser_status"] = "preview_pdf_offloaded" if result["preview"] else "pdf_no_preview"
    elif ext_l == ".xlsx":
        openpyxl = importlib.import_module("openpyxl")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheet = wb.worksheets[0] if wb.worksheets else None
        rows = []
        if sheet is not None:
            for ridx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                if ridx > 20:
                    break
                vals = [str(c) for c in row if c is not None]
                if vals:
                    rows.append(", ".join(vals))
        wb.close()
        text = "\\n".join(rows)
        result["preview"] = text[:max_chars] or None
        result["parser_status"] = "preview_xlsx_offloaded" if result["preview"] else "xlsx_no_preview"
    elif ext_l in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}:
        pil_image = importlib.import_module("PIL.Image")
        with pil_image.open(path) as im:
            result["image_meta"] = {
                "format": im.format,
                "mode": im.mode,
                "width": im.width,
                "height": im.height,
            }
        result["parser_status"] = "image_metadata_offloaded"
    elif ext_l in {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".stl", ".obj"}:
        import os
        result["media_meta"] = {
            "ext": ext_l,
            "size_bytes": os.path.getsize(path),
        }
        result["parser_status"] = "media_metadata_offloaded"
except Exception:
    result["parser_status"] = "preview_worker_failed"

print(json.dumps(result))
"""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", worker_code, local_path, ext_l, str(max_chars)],
            cwd=os.path.dirname(local_path) or None,
            capture_output=True,
            text=True,
            check=False,
            timeout=max(5, int(timeout_sec)),
            creationflags=_preview_worker_creationflags_con(),
        )
    except Exception:
        return {"preview": None, "image_meta": {}, "parser_status": "preview_worker_failed"}

    if proc.returncode != 0 or not proc.stdout.strip():
        return {"preview": None, "image_meta": {}, "parser_status": "preview_worker_failed"}

    try:
        result = json.loads(proc.stdout.strip())
    except Exception:
        return {"preview": None, "image_meta": {}, "parser_status": "preview_worker_failed"}

    if not isinstance(result, dict):
        return {"preview": None, "image_meta": {}, "parser_status": "preview_worker_failed"}
    return result
