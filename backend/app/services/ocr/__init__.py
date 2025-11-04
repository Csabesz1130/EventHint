"""OCR services - dual strategy with Tesseract and Google Vision."""

from app.services.ocr.base import OCRProvider, OCRResult
from app.services.ocr.tesseract import TesseractOCR
from app.services.ocr.google_vision import GoogleVisionOCR
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def extract_text_smart(image_bytes: bytes, prefer_free: bool = True) -> OCRResult:
    """
    Smart OCR router: try Tesseract first, fallback to Vision on low confidence.
    
    Args:
        image_bytes: Image data as bytes
        prefer_free: If True, try free OCR (Tesseract) first
    
    Returns:
        OCRResult with text, confidence, and metadata
    """
    # Try Tesseract first (free)
    if prefer_free:
        try:
            tesseract = TesseractOCR()
            result = tesseract.extract(image_bytes)
            
            # If confidence is good enough, use free OCR
            if result.confidence >= settings.OCR_CONFIDENCE_THRESHOLD:
                logger.info(f"Tesseract OCR succeeded with confidence {result.confidence:.2f}")
                return result
            else:
                logger.info(
                    f"Tesseract confidence {result.confidence:.2f} below threshold "
                    f"{settings.OCR_CONFIDENCE_THRESHOLD}, trying Vision"
                )
        except Exception as e:
            logger.warning(f"Tesseract OCR failed: {str(e)}, trying Vision")
    
    # Use premium OCR (Google Vision) if enabled
    if settings.ENABLE_GOOGLE_VISION and settings.GOOGLE_CLOUD_VISION_API_KEY:
        try:
            vision = GoogleVisionOCR()
            result = vision.extract(image_bytes)
            logger.info(f"Google Vision OCR succeeded with confidence {result.confidence:.2f}")
            return result
        except Exception as e:
            logger.error(f"Google Vision OCR failed: {str(e)}")
            # Fall back to Tesseract result if we had one
            if prefer_free:
                tesseract = TesseractOCR()
                return tesseract.extract(image_bytes)
            raise
    
    # If Vision is not enabled, return Tesseract result regardless of confidence
    tesseract = TesseractOCR()
    return tesseract.extract(image_bytes)


__all__ = ["OCRProvider", "OCRResult", "TesseractOCR", "GoogleVisionOCR", "extract_text_smart"]

