"""Web scraping service for extracting content from URLs."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebScraperService:
    """Service for scraping web content."""
    
    def __init__(self, timeout: int = 10, user_agent: Optional[str] = None):
        """
        Initialize web scraper.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing:
                - title: Page title
                - text: Extracted text content
                - html: Raw HTML content
                - links: List of links found
                - success: Boolean indicating success
                - error: Error message if failed
        """
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    "success": False,
                    "error": "Invalid URL format",
                    "url": url,
                }
            
            # Fetch content
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = None
            if soup.title:
                title = soup.title.string.strip()
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text(separator='\n')
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            # Extract links
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                link_text = a.get_text(strip=True)
                if href.startswith('http') or href.startswith('//'):
                    links.append({
                        'url': href,
                        'text': link_text,
                    })
            
            logger.info(f"Successfully scraped {url}: {len(text)} chars, {len(links)} links")
            
            return {
                "success": True,
                "url": url,
                "title": title or "Untitled",
                "text": text,
                "html": str(soup),
                "links": links,
                "content_type": response.headers.get('content-type', ''),
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while scraping {url}")
            return {
                "success": False,
                "error": "Request timeout",
                "url": url,
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while scraping {url}: {str(e)}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "url": url,
            }
        except Exception as e:
            logger.error(f"Unexpected error while scraping {url}: {str(e)}")
            return {
                "success": False,
                "error": f"Scraping failed: {str(e)}",
                "url": url,
            }


def scrape_url(url: str) -> Dict[str, Any]:
    """
    Convenience function to scrape a URL.
    
    Args:
        url: URL to scrape
        
    Returns:
        Scraped content dictionary
    """
    scraper = WebScraperService()
    return scraper.scrape_url(url)

