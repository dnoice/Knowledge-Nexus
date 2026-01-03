"""
Helper Utilities
================
Common utility functions for the backend.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

import re
from typing import Optional

from slugify import slugify


def slugify_safe(text: str, max_length: int = 100) -> str:
    """
    Create a URL-safe slug from text.

    Args:
        text: Input text to slugify
        max_length: Maximum length of output

    Returns:
        URL-safe slug
    """
    slug = slugify(text, lowercase=True, max_length=max_length)
    return slug or "untitled"


def truncate_text(
    text: str,
    max_length: int = 200,
    suffix: str = "..."
) -> str:
    """
    Truncate text to a maximum length at word boundaries.

    Args:
        text: Input text
        max_length: Maximum output length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    # Find last space before max_length
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')

    if last_space > max_length // 2:
        truncated = truncated[:last_space]

    return truncated.rstrip() + suffix


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting from text.

    Args:
        text: Markdown text

    Returns:
        Plain text with markdown removed
    """
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)

    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)

    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove emphasis
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove list markers
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def calculate_reading_time(
    word_count: int,
    words_per_minute: int = 200
) -> int:
    """
    Calculate estimated reading time.

    Args:
        word_count: Number of words
        words_per_minute: Reading speed (default 200)

    Returns:
        Reading time in minutes (minimum 1)
    """
    minutes = word_count / words_per_minute
    return max(1, round(minutes))


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            if unit == 'B':
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.1f} TB"


def extract_first_paragraph(markdown: str) -> str:
    """
    Extract the first paragraph from markdown text.

    Args:
        markdown: Markdown content

    Returns:
        First paragraph text
    """
    # Split on blank lines
    paragraphs = re.split(r'\n\s*\n', markdown)

    for para in paragraphs:
        # Skip headings
        if para.strip().startswith('#'):
            continue
        # Skip code blocks
        if para.strip().startswith('```'):
            continue
        # Skip horizontal rules
        if re.match(r'^[-*_]{3,}\s*$', para.strip()):
            continue

        # Found a content paragraph
        text = strip_markdown(para)
        if text and len(text) > 20:
            return text

    return ""


def normalize_path(path: str) -> str:
    """
    Normalize a path for consistent comparison.

    Args:
        path: File or URL path

    Returns:
        Normalized path
    """
    # Convert backslashes to forward slashes
    path = path.replace('\\', '/')

    # Remove trailing slash
    path = path.rstrip('/')

    # Remove double slashes
    path = re.sub(r'/+', '/', path)

    return path


def generate_excerpt(
    content: str,
    query: Optional[str] = None,
    max_length: int = 300
) -> str:
    """
    Generate an excerpt from content, optionally centered on a query match.

    Args:
        content: Full content text
        query: Optional search query to center excerpt on
        max_length: Maximum excerpt length

    Returns:
        Excerpt text
    """
    content = strip_markdown(content)

    if query and query.lower() in content.lower():
        # Find query position
        pos = content.lower().find(query.lower())

        # Center excerpt around match
        start = max(0, pos - max_length // 2)
        end = min(len(content), pos + len(query) + max_length // 2)

        excerpt = content[start:end]

        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt

    # No query or no match - return beginning
    return truncate_text(content, max_length)
