"""Tesseract OCR implementation - free, local OCR."""

import pytesseract
from PIL import Image
import io
from typing import List
import logging

from app.services.ocr.base import OCRProvider, OCRResult, TextBlock
from app.config import settings

logger = logging.getLogger(__name__)


class TesseractOCR(OCRProvider):
    """
    Tesseract OCR implementation (free, local).
    
    Supports multiple languages (eng, hun) and provides decent accuracy
    for printed text. Not as good with handwriting or complex layouts.
    """
    
    def __init__(self):
        # Set Tesseract path if configured
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    
    def extract(self, image_bytes: bytes) -> OCRResult:
        """
        Extract text from an image using Tesseract.
        
        Args:
            image_bytes: Image data as bytes
        
        Returns:
            OCRResult with extracted text and confidence
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # OCR with detailed data (includes confidence per word)
            data = pytesseract.image_to_data(
                image,
                lang='eng+hun',  # English + Hungarian
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text = pytesseract.image_to_string(image, lang='eng+hun')
            
            # Calculate average confidence
            confidences = [
                float(conf) for conf in data['conf'] 
                if conf != '-1' and str(conf).replace('.', '').isdigit()
            ]
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.5
            
            # Extract blocks with positions
            blocks = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0:
                    block = TextBlock(
                        text=data['text'][i],
                        confidence=float(data['conf'][i]) / 100.0,
                        bbox=(
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i],
                        ),
                    )
                    blocks.append(block)
            
            # Detect language
            try:
                lang_data = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
                detected_lang = lang_data.get('script', 'Latin')
            except Exception:
                detected_lang = None
            
            logger.info(
                f"Tesseract extracted {len(text)} chars with confidence {avg_confidence:.2f}"
            )
            
            return OCRResult(
                text=text,
                confidence=avg_confidence,
                blocks=blocks,
                language=detected_lang,
                metadata={
                    "provider": "tesseract",
                    "num_blocks": len(blocks),
                },
            )
            
        except Exception as e:
            logger.error(f"Tesseract OCR error: {str(e)}")
            raise
    
    def extract_from_pdf(self, pdf_bytes: bytes) -> List[OCRResult]:
        """
        Extract text from PDF by converting pages to images.
        
        Args:
            pdf_bytes: PDF data as bytes
        
        Returns:
            List of OCRResult, one per page
        """
        try:
            from pdf2image import convert_from_bytes
            
            # Convert PDF pages to images
            images = convert_from_bytes(pdf_bytes)
            
            results = []
            for page_num, image in enumerate(images, start=1):
                # Convert PIL Image to bytes
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # OCR the page
                result = self.extract(img_bytes.getvalue())
                
                # Update blocks with page number
                for block in result.blocks:
                    block.page = page_num
                
                result.metadata["page"] = page_num
                results.append(result)
            
            logger.info(f"Tesseract extracted {len(results)} pages from PDF")
            return results
            
        except Exception as e:
            logger.error(f"Tesseract PDF extraction error: {str(e)}")
            raise
    
    def supports_tables(self) -> bool:
        """Tesseract has basic table detection with layoutparser."""
        return False  # For now; can enhance with layoutparser
    
    def supports_layout(self) -> bool:
        """Tesseract supports basic layout analysis."""
        return True

