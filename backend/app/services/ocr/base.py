"""Base OCR provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class TextBlock:
    """Represents a detected text block with position."""
    text: str
    confidence: float
    bbox: Optional[tuple] = None  # (x, y, width, height)
    page: int = 0


@dataclass
class OCRResult:
    """OCR extraction result."""
    text: str
    confidence: float
    blocks: List[TextBlock]
    language: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class OCRProvider(ABC):
    """
    Abstract base class for OCR providers.
    
    Implementations:
    - TesseractOCR: Free, local OCR
    - GoogleVisionOCR: Premium cloud OCR with table detection
    """
    
    @abstractmethod
    def extract(self, image_bytes: bytes) -> OCRResult:
        """
        Extract text from an image.
        
        Args:
            image_bytes: Image data as bytes
        
        Returns:
            OCRResult with text, confidence, and metadata
        """
        pass
    
    @abstractmethod
    def extract_from_pdf(self, pdf_bytes: bytes) -> List[OCRResult]:
        """
        Extract text from a PDF (page by page).
        
        Args:
            pdf_bytes: PDF data as bytes
        
        Returns:
            List of OCRResult, one per page
        """
        pass
    
    def supports_tables(self) -> bool:
        """Whether this provider supports table detection."""
        return False
    
    def supports_layout(self) -> bool:
        """Whether this provider supports layout analysis."""
        return False

