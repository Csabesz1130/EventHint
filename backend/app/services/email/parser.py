"""Email content parsing and normalization."""

from bs4 import BeautifulSoup
from typing import Optional
import re


def html_to_text(html: str) -> str:
    """
    Convert HTML email body to plain text.
    
    Args:
        html: HTML content
    
    Returns:
        Plain text with preserved structure
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text


def clean_email_text(text: str) -> str:
    """
    Clean email text by removing signatures, quoted replies, etc.
    
    Args:
        text: Email body text
    
    Returns:
        Cleaned text focusing on main content
    """
    # Remove email signatures (common patterns)
    signature_patterns = [
        r'--\s*\n.*',  # -- signature
        r'_{5,}.*',  # _____ signature
        r'Sent from my \w+.*',
        r'Get Outlook for \w+.*',
    ]
    
    for pattern in signature_patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove quoted replies (lines starting with >)
    lines = text.split('\n')
    cleaned_lines = []
    in_quote = False
    
    for line in lines:
        if line.strip().startswith('>'):
            in_quote = True
            continue
        if in_quote and line.strip() == '':
            in_quote = False
            continue
        if not in_quote:
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def extract_email_metadata(from_header: str) -> dict:
    """
    Parse From header into name and email.
    
    Args:
        from_header: From header value (e.g., "John Doe <john@example.com>")
    
    Returns:
        Dict with 'name' and 'email'
    """
    # Pattern: "Name <email>"
    match = re.match(r'^(.+?)\s*<(.+?)>$', from_header)
    
    if match:
        return {
            'name': match.group(1).strip().strip('"'),
            'email': match.group(2).strip(),
        }
    else:
        # Just an email address
        return {
            'name': '',
            'email': from_header.strip(),
        }

