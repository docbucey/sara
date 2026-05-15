# sara_security/scanner.py
# Extracted from sara_securitygen1.py — document and image scanning.

import os
import importlib
import shutil
from typing import Optional, Dict, List, Any

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass


def scan_image_con(
    con_image_path: str,
    con_project: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Scan an image file for metadata, size, format anomalies.
    Check for embedded scripts or suspicious EXIF data.

    Args:
        con_image_path : path to image file to scan
        con_project    : optional, writes NBS audit wrapper

    Returns dict with 'success', 'threats' list, 'metadata'.
    Requires: Pillow
    """
    try:
        pil_image = importlib.import_module("PIL.Image")
    except Exception:
        return {"success": False, "error": "Pillow not installed (pip install Pillow)"}

    if not os.path.exists(con_image_path):
        return {"success": False, "error": f"File not found: {con_image_path}"}

    threats = []
    metadata = {}

    try:
        with open(con_image_path, "rb") as f:
            header = f.read(4)
            # Check magic bytes for spoofing
            if header.startswith(b"<?xml") or b"script" in f.read(1000).lower():
                threats.append("Possible embedded script in header")

        img = pil_image.open(con_image_path)
        format_str = str(img.format or "unknown").upper()
        metadata["format"] = format_str
        metadata["width"] = img.width
        metadata["height"] = img.height
        metadata["mode"] = img.mode
        metadata["file_size_kb"] = os.path.getsize(con_image_path) / 1024

        # Check for suspicious EXIF data
        try:
            exif_data = img._getexif()
            if exif_data:
                metadata["has_exif"] = True
                # Check for GPS data that might leak location
                for tag, value in exif_data.items():
                    if tag in (34853, 34854):  # GPS IFD tags
                        threats.append("GPS location data found in EXIF")
                        break
        except Exception:
            pass

        # Check for anomalies
        if metadata["width"] > 10000 or metadata["height"] > 10000:
            threats.append("Extremely large image dimensions (possible DoS vector)")

    except Exception as e:
        return {"success": False, "error": f"scan_image failed: {e}"}

    result: Dict[str, Any] = {
        "success": True,
        "path": con_image_path,
        "threats": threats,
        "metadata": metadata,
        "threat_level": "high" if threats else "low",
    }

    return result


def audit_image_con(
    con_image_path: str,
    con_quarantine_reason: Optional[str] = None,
    con_project: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Audit and optionally quarantine an image based on threats.
    Move to quarantine folder if con_quarantine_reason provided.

    Args:
        con_image_path        : path to image file to audit
        con_quarantine_reason : if provided, move file to quarantine with this reason
        con_project           : optional, writes NBS audit wrapper

    Returns dict with 'success', 'action', 'quarantine_path'.
    Requires: Pillow (for scan), shutil (built-in)
    """
    # First scan the image
    scan_result = scan_image_con(con_image_path, con_project=None)
    if not scan_result.get("success"):
        return scan_result  # Propagate scan error

    threat_level = scan_result.get("threat_level", "low")
    quarantine_path = None
    action = "audited"

    # If high threat or explicit quarantine reason, move to quarantine
    if con_quarantine_reason or threat_level == "high":
        try:
            quarantine_dir = os.path.join(
                os.path.dirname(con_image_path), "__quarantine__"
            )
            os.makedirs(quarantine_dir, exist_ok=True)
            reason_str = (con_quarantine_reason or threat_level).replace(" ", "_")[:50]
            base_name = os.path.basename(con_image_path)
            name, ext = os.path.splitext(base_name)
            quarantine_path = os.path.join(
                quarantine_dir,
                f"{name}__quarantined__{reason_str}{ext}",
            )
            shutil.move(con_image_path, quarantine_path)
            action = "quarantined"
        except Exception as e:
            return {"success": False, "error": f"Quarantine failed: {e}"}

    result: Dict[str, Any] = {
        "success": True,
        "path": con_image_path,
        "action": action,
        "threat_level": threat_level,
        "threats": scan_result.get("threats", []),
        "metadata": scan_result.get("metadata", {}),
    }

    if quarantine_path:
        result["quarantine_path"] = quarantine_path

    return result


def scan_docx_con(
    con_docx_path: str,
) -> Dict[str, Any]:
    """
    Scan a DOCX file for embedded threats: macros, code, OLE objects, external links.

    Args:
        con_docx_path : path to .docx file to scan

    Returns dict with 'success', 'threats' list, 'metadata'.
    Requires: python-docx, zipfile (built-in)
    """
    if not os.path.exists(con_docx_path):
        return {"success": False, "error": f"File not found: {con_docx_path}"}

    threats = []
    metadata = {}

    try:
        import zipfile

        metadata["file_size_kb"] = os.path.getsize(con_docx_path) / 1024
        metadata["format"] = "docx"

        # DOCX is a ZIP file; scan the internal structure
        with zipfile.ZipFile(con_docx_path, "r") as zf:
            file_list = zf.namelist()
            metadata["internal_files"] = len(file_list)

            # Check for VBA macros (usually in /word/vbaProject.bin or /xl/vbaProject.bin)
            if any("vbaProject" in f for f in file_list):
                threats.append("VBA macros detected (potential malware vector)")

            # Check for embedded objects
            if "word/embeddings/" in str(file_list):
                threats.append("Embedded objects found (potential execution vector)")

            # Check external relationships (links to external servers)
            for fname in file_list:
                if fname.endswith(".rels"):
                    try:
                        content = zf.read(fname).decode("utf-8", errors="ignore")
                        if "http://" in content or "ftp://" in content:
                            threats.append(
                                "External link in relationships (potential data exfiltration)"
                            )
                            break
                    except Exception:
                        pass

            # Check document.xml for suspicious fields
            try:
                if "word/document.xml" in file_list:
                    doc_xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
                    if "<w:fldCode>" in doc_xml or "EXTERNAL" in doc_xml:
                        threats.append("Dynamic field code detected (potential injection)")
                    if "field_update" in doc_xml.lower():
                        threats.append("Auto-update field detected")
            except Exception:
                pass

    except Exception as e:
        return {"success": False, "error": f"scan_docx failed: {e}"}

    result: Dict[str, Any] = {
        "success": True,
        "path": con_docx_path,
        "threats": threats,
        "metadata": metadata,
        "threat_level": "high" if threats else "low",
    }

    return result


def scan_xlsx_con(
    con_xlsx_path: str,
) -> Dict[str, Any]:
    """
    Scan an XLSX file for threats: formulas, external links, VBA, data validation tricks.

    Args:
        con_xlsx_path : path to .xlsx file to scan

    Returns dict with 'success', 'threats' list, 'metadata'.
    Requires: zipfile (built-in)
    """
    import zipfile

    if not os.path.exists(con_xlsx_path):
        return {"success": False, "error": f"File not found: {con_xlsx_path}"}

    threats = []
    metadata = {}

    try:
        metadata["file_size_kb"] = os.path.getsize(con_xlsx_path) / 1024
        metadata["format"] = "xlsx"

        with zipfile.ZipFile(con_xlsx_path, "r") as zf:
            file_list = zf.namelist()
            metadata["internal_files"] = len(file_list)

            # Check for VBA macros
            if any("vbaProject" in f for f in file_list):
                threats.append("VBA macros detected in XLSX")

            # Check workbook.xml for external connections
            try:
                if "xl/workbook.xml" in file_list:
                    wbk = zf.read("xl/workbook.xml").decode("utf-8", errors="ignore")
                    if "externalLink" in wbk:
                        threats.append("External link references found")
                    if "dataConnection" in wbk:
                        threats.append("Data connection found (potential data exfiltration)")
            except Exception:
                pass

            # Check worksheets for suspicious formulas
            for fname in file_list:
                if fname.startswith("xl/worksheets/sheet") and fname.endswith(".xml"):
                    try:
                        sheet_xml = zf.read(fname).decode("utf-8", errors="ignore")
                        # Check for formula injection patterns
                        if "=cmd|" in sheet_xml or "=powershell" in sheet_xml:
                            threats.append("Command injection formula detected")
                        if "=WEBSERVICE(" in sheet_xml:
                            threats.append("WEBSERVICE formula (data exfil potential)")
                        if "=HYPERLINK(" in sheet_xml and ("http" in sheet_xml or "ftp" in sheet_xml):
                            threats.append("Suspicious hyperlink formula")
                    except Exception:
                        pass

            # Check for data validation with malicious patterns
            try:
                if "xl/dataValidations.xml" in file_list:
                    dv = zf.read("xl/dataValidations.xml").decode("utf-8", errors="ignore")
                    if "prompt" in dv.lower() and ("password" in dv.lower() or "login" in dv.lower()):
                        threats.append("Credential prompt data validation (social engineering)")
            except Exception:
                pass

    except Exception as e:
        return {"success": False, "error": f"scan_xlsx failed: {e}"}

    result: Dict[str, Any] = {
        "success": True,
        "path": con_xlsx_path,
        "threats": threats,
        "metadata": metadata,
        "threat_level": "high" if threats else "low",
    }

    return result


def scan_pdf_con(
    con_pdf_path: str,
) -> Dict[str, Any]:
    """
    Scan a PDF file for threats: embedded scripts, form handlers, unusual objects.

    Args:
        con_pdf_path : path to .pdf file to scan

    Returns dict with 'success', 'threats' list, 'metadata'.
    """
    if not os.path.exists(con_pdf_path):
        return {"success": False, "error": f"File not found: {con_pdf_path}"}

    threats = []
    metadata = {}

    try:
        metadata["file_size_kb"] = os.path.getsize(con_pdf_path) / 1024
        metadata["format"] = "pdf"

        # Read raw PDF to look for suspicious patterns
        with open(con_pdf_path, "rb") as f:
            content = f.read()
            metadata["size_bytes"] = len(content)

            # Check for JavaScript in PDF
            if b"/JavaScript" in content or b"/JS" in content:
                threats.append("JavaScript embedded in PDF (potential exploit)")

            # Check for launch actions (external program execution)
            if b"/Launch" in content or b"/SubmitForm" in content:
                threats.append("Launch/form action detected (potential RCE)")

            # Check for embedded files
            if b"/EmbeddedFile" in content:
                threats.append("Embedded files in PDF (potential malware payload)")

            # Check for OpenAction (auto-execute on open)
            if b"/OpenAction" in content:
                threats.append("OpenAction detected (auto-execute on open)")

            # Check for external references
            if b"/XObject" in content or b"/ObjStm" in content:
                if b"http" in content or b"ftp" in content:
                    threats.append("External resource reference in PDF")

            # Check for form field submit to external URL
            if b"/SubmitForm" in content:
                if b"http" in content or b"ftp" in content:
                    threats.append("Form submission to external URL detected")

            # Check for unusually large compressed streams (potential polyglot/exploit)
            if b"stream" in content:
                stream_count = content.count(b"stream")
                metadata["stream_count"] = stream_count
                if stream_count > 50:
                    threats.append("High number of streams (potential polyglot/exploit)")

    except Exception as e:
        return {"success": False, "error": f"scan_pdf failed: {e}"}

    result: Dict[str, Any] = {
        "success": True,
        "path": con_pdf_path,
        "threats": threats,
        "metadata": metadata,
        "threat_level": "high" if threats else "low",
    }

    return result


def audit_files_con(
    con_file_paths: List[str],
    con_quarantine_on_threat: bool = True,
) -> Dict[str, Any]:
    """
    Batch audit multiple office files (DOCX, XLSX, PDF, images).
    Auto-quarantine if threats detected and con_quarantine_on_threat=True.

    Args:
        con_file_paths         : list of file paths to audit
        con_quarantine_on_threat: if True, quarantine threatened files

    Returns dict with 'success', 'results' list, 'quarantined_count'.
    """
    results = []
    quarantined_count = 0

    for fpath in (con_file_paths or []):
        if not os.path.exists(fpath):
            results.append({"path": fpath, "success": False, "error": "File not found"})
            continue

        ext = os.path.splitext(fpath)[1].lower()
        scan_result = None

        if ext == ".docx":
            scan_result = scan_docx_con(fpath)
        elif ext == ".xlsx":
            scan_result = scan_xlsx_con(fpath)
        elif ext == ".pdf":
            scan_result = scan_pdf_con(fpath)
        elif ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
            scan_result = scan_image_con(fpath)
        else:
            results.append({"path": fpath, "success": False, "error": f"Unsupported format: {ext}"})
            continue

        if not scan_result.get("success"):
            results.append(scan_result)
            continue

        threat_level = scan_result.get("threat_level", "low")
        threats = scan_result.get("threats", [])

        action = "passed"
        quarantine_path = None

        if (threat_level == "high" or threats) and con_quarantine_on_threat:
            try:
                quarantine_dir = os.path.join(os.path.dirname(fpath), "__quarantine__")
                os.makedirs(quarantine_dir, exist_ok=True)
                threat_str = (threats[0] if threats else "high_threat").replace(" ", "_")[:40]
                base_name = os.path.basename(fpath)
                name, ext_part = os.path.splitext(base_name)
                quarantine_path = os.path.join(
                    quarantine_dir, f"{name}__quarantined__{threat_str}{ext_part}"
                )
                shutil.move(fpath, quarantine_path)
                action = "quarantined"
                quarantined_count += 1
            except Exception as e:
                results.append(
                    {"path": fpath, "success": False, "error": f"Quarantine failed: {e}"}
                )
                continue

        result_entry = {
            "path": fpath,
            "success": True,
            "threat_level": threat_level,
            "threats": threats,
            "action": action,
        }
        if quarantine_path:
            result_entry["quarantine_path"] = quarantine_path

        results.append(result_entry)

    return {
        "success": True,
        "results": results,
        "quarantined_count": quarantined_count,
        "total_audited": len(con_file_paths or []),
    }
