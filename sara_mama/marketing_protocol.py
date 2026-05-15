"""
MarketingProtocol: PowerPoint/Google Slides and graphics protocol for Mama
Implements slideshow and graphics validation/automation using python-pptx and Pillow.
"""

from typing import Optional, List, Dict, Any

try:
    import pptx  # python-pptx
    from PIL import Image
    _PPTX_OK = True
except Exception:
    _PPTX_OK = False

class MarketingProtocol:
    """
    Protocol for validating and automating slideshow (PowerPoint/Google Slides) and graphics assets.
    """
    def __init__(self):
        if not _PPTX_OK:
            raise ImportError("python-pptx and Pillow are required for MarketingProtocol")

    def validate_slideshow(self, pptx_path: str, required_titles: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate that the slideshow contains all required slide titles.
        """
        if not _PPTX_OK:
            return {"status": "ERROR", "error": "python-pptx not available"}
        try:
            prs = pptx.Presentation(pptx_path)
            titles = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        text = shape.text_frame.text.strip()
                        if text:
                            titles.append(text)
            missing = [t for t in (required_titles or []) if t not in titles]
            return {
                "status": "PASS" if not missing else "FAIL",
                "slide_titles": titles,
                "missing_titles": missing,
                "required_titles": required_titles or [],
                "pptx_path": pptx_path,
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e), "pptx_path": pptx_path}

    def automate_graphics(self, image_path: str, output_path: Optional[str] = None, resize: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Example automation: resize image using Pillow.
        """
        if not _PPTX_OK:
            return {"status": "ERROR", "error": "Pillow not available"}
        try:
            img = Image.open(image_path)
            if resize:
                img = img.resize(resize)
            out_path = output_path or image_path
            img.save(out_path)
            return {"status": "PASS", "output_path": out_path, "resized": bool(resize)}
        except Exception as e:
            return {"status": "ERROR", "error": str(e), "image_path": image_path}
