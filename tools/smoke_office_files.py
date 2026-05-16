"""
Write sample .docx and .xlsx on disk. Open them in Microsoft Word / Excel or LibreOffice.
This does NOT install SARA inside Word; it only creates normal Office files.

Run from SARA repo root: python tools/smoke_office_files.py
"""
from __future__ import annotations

import os
import sys
import traceback


def main() -> int:
    try:
        from docx import Document
    except ImportError:
        print("MISSING: pip install python-docx")
        return 2
    try:
        import openpyxl
    except ImportError:
        print("MISSING: pip install openpyxl")
        return 2

    docs = os.path.join(os.path.expanduser("~"), "Documents", "SARA_smoke_out")
    os.makedirs(docs, exist_ok=True)
    docx_path = os.path.join(docs, "sara_smoke.docx")
    xlsx_path = os.path.join(docs, "sara_smoke.xlsx")
    try:
        doc = Document()
        doc.add_heading("SARA smoke test", 0)
        doc.add_paragraph(
            "If Word shows a yellow bar, click Enable Editing. "
            "SARA is not a Word add-in; CONTROL wrote this file to disk for you to open."
        )
        doc.add_paragraph("Hello from python-docx.")
        doc.save(docx_path)

        wb = openpyxl.Workbook()
        ws = wb.active
        assert ws is not None
        ws.title = "Smoke"
        ws["A1"] = "Hello"
        ws["B1"] = "Open in Excel or Calc"
        wb.save(xlsx_path)

        print("OK wrote (ASCII paths):")
        print(" ", docx_path)
        print(" ", xlsx_path)
        print("Opening folder in Explorer...")
        if sys.platform == "win32":
            os.startfile(docs)  # noqa: S606 - opens Explorer on the output folder
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
