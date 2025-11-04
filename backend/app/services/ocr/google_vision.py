"""Google Cloud Vision API OCR implementation - premium cloud OCR."""

from google.cloud import vision
from typing import List
import logging

from app.services.ocr.base import OCRProvider, OCRResult, TextBlock
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleVisionOCR(OCRProvider):
    """
    Google Cloud Vision API OCR (premium, cloud-based).
    
    Features:
    - Excellent accuracy for printed and handwritten text
    - Table detection
    - Layout analysis
    - Multi-language support
    - Confidence scores per word
    """
    
    def __init__(self):
        if not settings.GOOGLE_CLOUD_VISION_API_KEY:
            raise ValueError("Google Cloud Vision API key not configured")
        
        # Initialize client
        import os
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_CLOUD_VISION_API_KEY
        self.client = vision.ImageAnnotatorClient()
    
    def extract(self, image_bytes: bytes) -> OCRResult:
        """
        Extract text from an image using Google Cloud Vision.
        
        Args:
            image_bytes: Image data as bytes
        
        Returns:
            OCRResult with extracted text and high confidence
        """
        try:
            # Create Vision API image object
            image = vision.Image(content=image_bytes)
            
            # Perform text detection
            response = self.client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Extract full text
            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            
            # Extract blocks with confidence
            blocks = []
            total_confidence = 0.0
            confidence_count = 0
            
            if response.full_text_annotation:
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        block_text = ""
                        block_confidence = 0.0
                        word_count = 0
                        
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                word_text = ''.join([symbol.text for symbol in word.symbols])
                                block_text += word_text + " "
                                block_confidence += word.confidence
                                word_count += 1
                        
                        if word_count > 0:
                            avg_confidence = block_confidence / word_count
                            total_confidence += avg_confidence
                            confidence_count += 1
                            
                            # Extract bounding box
                            vertices = block.bounding_box.vertices
                            bbox = (
                                vertices[0].x,
                                vertices[0].y,
                                vertices[2].x - vertices[0].x,
                                vertices[2].y - vertices[0].y,
                            )
                            
                            blocks.append(TextBlock(
                                text=block_text.strip(),
                                confidence=avg_confidence,
                                bbox=bbox,
                            ))
            
            # Calculate overall confidence
            overall_confidence = (
                total_confidence / confidence_count 
                if confidence_count > 0 
                else 0.8  # Default high confidence for Vision
            )
            
            # Detect language
            detected_languages = []
            if response.full_text_annotation:
                for page in response.full_text_annotation.pages:
                    for prop in page.property.detected_languages:
                        detected_languages.append(prop.language_code)
            
            language = detected_languages[0] if detected_languages else None
            
            logger.info(
                f"Google Vision extracted {len(full_text)} chars "
                f"with confidence {overall_confidence:.2f}"
            )
            
            return OCRResult(
                text=full_text,
                confidence=overall_confidence,
                blocks=blocks,
                language=language,
                metadata={
                    "provider": "google_vision",
                    "num_blocks": len(blocks),
                    "detected_languages": detected_languages,
                },
            )
            
        except Exception as e:
            logger.error(f"Google Vision OCR error: {str(e)}")
            raise
    
    def extract_from_pdf(self, pdf_bytes: bytes) -> List[OCRResult]:
        """
        Extract text from PDF using Vision API.
        
        Note: Vision API can process PDF directly, but for consistency
        we convert to images like Tesseract.
        
        Args:
            pdf_bytes: PDF data as bytes
        
        Returns:
            List of OCRResult, one per page
        """
        try:
            from pdf2image import convert_from_bytes
            import io
            
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
            
            logger.info(f"Google Vision extracted {len(results)} pages from PDF")
            return results
            
        except Exception as e:
            logger.error(f"Google Vision PDF extraction error: {str(e)}")
            raise
    
    def supports_tables(self) -> bool:
        """Vision API supports table detection."""
        return True
    
    def supports_layout(self) -> bool:
        """Vision API supports advanced layout analysis."""
        return True

