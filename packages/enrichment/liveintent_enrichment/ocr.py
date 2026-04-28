from pathlib import Path
import pytesseract
from PIL import Image
import structlog

log = structlog.get_logger(__name__)

def extract_text(image_path: Path | str) -> str | None:
    p = Path(image_path)
    if not p.exists():
        return None
    try:
        with Image.open(p) as img:
            text = pytesseract.image_to_string(img)
        return text.strip() or None
    except Exception as e:
        log.warning("ocr.failed", path=str(p), error=str(e))
        return None
