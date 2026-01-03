"""
Markdown Parser Service
=======================
Parses markdown files and extracts metadata from docstring headers.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional
import logging

import markdown
from slugify import slugify

from ..config import get_settings
from ..models.article import (
    ArticleMetadata,
    TableOfContentsEntry,
    ArticleContent,
)

logger = logging.getLogger(__name__)


class DocstringParser:
    """
    Parses the custom docstring metadata format used in Knowledge Nexus articles.

    Expected format:
    <!--
    ✒ Metadata
        - Title: ...
        - File Name: ...
        ...
    ✒ Description:
        ...
    ✒ Key Features:
        - Feature 1: ...
        - Feature 2: ...
    ...
    ---------
    -->
    """

    # Pattern to match the entire docstring block
    DOCSTRING_PATTERN = re.compile(
        r'<!--\s*\n(.*?)\n\s*-{3,}\s*\n\s*-->',
        re.DOTALL
    )

    # Pattern to match section headers (e.g., "✒ Metadata")
    SECTION_PATTERN = re.compile(
        r'✒\s*([^:\n]+?)(?::\s*(.*))?$',
        re.MULTILINE
    )

    # Pattern to match key-value fields (e.g., "- Title: Something")
    FIELD_PATTERN = re.compile(
        r'^\s*-\s*([^:]+?):\s*(.+)$',
        re.MULTILINE
    )

    # Pattern to match feature list items (e.g., "- Feature 1: Description")
    FEATURE_PATTERN = re.compile(
        r'^\s*-\s*Feature\s*\d+:\s*(.+)$',
        re.MULTILINE
    )

    # Pattern for date parsing
    DATE_PATTERNS = [
        r'(\d{4})-(\d{2})-(\d{2})',  # 2025-01-03
        r'(\w+),?\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # Friday, January 3, 2025
    ]

    def __init__(self):
        self.settings = get_settings()

    def parse(self, content: str) -> tuple[dict[str, Any], str]:
        """
        Parse content and extract docstring metadata.

        Returns:
            Tuple of (metadata_dict, clean_content)
        """
        match = self.DOCSTRING_PATTERN.search(content)

        if not match:
            logger.debug("No docstring found in content")
            return {}, content

        docstring = match.group(1)
        metadata = self._parse_docstring(docstring)

        # Remove docstring from content
        clean_content = self.DOCSTRING_PATTERN.sub('', content).strip()

        return metadata, clean_content

    def _parse_docstring(self, docstring: str) -> dict[str, Any]:
        """Parse the docstring content into a metadata dictionary."""
        metadata: dict[str, Any] = {}
        current_section: Optional[str] = None
        section_content: list[str] = []

        lines = docstring.split('\n')

        for line in lines:
            stripped = line.strip()

            # Check for section header
            section_match = self.SECTION_PATTERN.match(stripped)
            if section_match:
                # Save previous section
                if current_section:
                    self._save_section(metadata, current_section, section_content)
                    section_content = []

                current_section = self._normalize_key(section_match.group(1))

                # Check for inline value
                inline_value = section_match.group(2)
                if inline_value and inline_value.strip():
                    section_content.append(inline_value.strip())

                continue

            # Process line within current section
            if current_section:
                # Check for key-value field
                field_match = self.FIELD_PATTERN.match(line)
                if field_match:
                    key = self._normalize_key(field_match.group(1))
                    value = field_match.group(2).strip()
                    metadata[key] = value
                    continue

                # Check for feature item
                feature_match = self.FEATURE_PATTERN.match(line)
                if feature_match:
                    if 'key_features' not in metadata:
                        metadata['key_features'] = []
                    metadata['key_features'].append(feature_match.group(1).strip())
                    continue

                # Accumulate section content
                if stripped:
                    section_content.append(stripped)

        # Save last section
        if current_section:
            self._save_section(metadata, current_section, section_content)

        # Post-process metadata
        return self._post_process(metadata)

    def _normalize_key(self, key: str) -> str:
        """Normalize a key name to snake_case."""
        key = key.strip().lower()
        # Replace special characters and spaces
        key = re.sub(r'[.\s-]+', '_', key)
        key = re.sub(r'[^a-z0-9_]', '', key)
        # Handle specific mappings
        key_mappings = {
            'ai_acknowledgement': 'ai_acknowledgement',
            'a_i_acknowledgement': 'ai_acknowledgement',
            'other_important_information': 'other_info',
            'usage_instructions': 'usage_instructions',
        }
        return key_mappings.get(key, key)

    def _save_section(
        self,
        metadata: dict[str, Any],
        section: str,
        content: list[str]
    ) -> None:
        """Save accumulated section content."""
        if not content:
            return

        # Join content lines
        text = ' '.join(content).strip()

        # Skip if section already has fields (like metadata with - key: value)
        if section == 'metadata':
            return

        metadata[section] = text

    def _post_process(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Post-process metadata values."""
        # Parse date field
        if 'date' in metadata:
            metadata['date'] = self._parse_date(metadata['date'])

        # Ensure key_features is a list
        if 'key_features' not in metadata:
            metadata['key_features'] = []
        elif isinstance(metadata['key_features'], str):
            metadata['key_features'] = [metadata['key_features']]

        # Set defaults
        defaults = {
            'title': 'Untitled',
            'file_name': '',
            'relative_path': '',
            'artifact_type': 'docs',
            'version': '1.0.0',
            'author': 'Dennis \'dnoice\' Smaltz',
            'ai_acknowledgement': 'Anthropic - Claude Opus 4.5',
            'signature': 'Aim Twice, Shoot Once!',
            'description': '',
            'usage_instructions': '',
            'other_info': '',
        }

        for key, default in defaults.items():
            if key not in metadata:
                metadata[key] = default

        return metadata

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse a date string into a date object."""
        if not date_str:
            return None

        # Try YYYY-MM-DD format
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if match:
            try:
                return date(
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3))
                )
            except ValueError:
                pass

        # Try parsing with datetime
        formats = [
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def to_article_metadata(self, metadata: dict[str, Any]) -> ArticleMetadata:
        """Convert parsed metadata dict to ArticleMetadata model."""
        return ArticleMetadata(
            title=metadata.get('title', 'Untitled'),
            file_name=metadata.get('file_name', ''),
            relative_path=metadata.get('relative_path', ''),
            artifact_type=metadata.get('artifact_type', 'docs'),
            version=metadata.get('version', '1.0.0'),
            date=metadata.get('date'),
            update=metadata.get('update'),
            author=metadata.get('author', 'Dennis \'dnoice\' Smaltz'),
            ai_acknowledgement=metadata.get('ai_acknowledgement', ''),
            signature=metadata.get('signature', ''),
            description=metadata.get('description', ''),
            key_features=metadata.get('key_features', []),
            usage_instructions=metadata.get('usage_instructions', ''),
            other_info=metadata.get('other_info', ''),
        )


class MarkdownParser:
    """
    Full markdown parser with rendering and TOC extraction.
    """

    # Heading pattern for TOC extraction
    HEADING_PATTERN = re.compile(
        r'^(#{1,6})\s+(.+?)(?:\s+\{#([^}]+)\})?$',
        re.MULTILINE
    )

    def __init__(self):
        self.settings = get_settings()
        self.docstring_parser = DocstringParser()

        # Configure markdown processor
        md_config = self.settings.markdown
        extension_configs = {
            'codehilite': {
                'css_class': md_config.extension_configs.codehilite.css_class,
                'guess_lang': md_config.extension_configs.codehilite.guess_lang,
                'linenums': md_config.extension_configs.codehilite.linenums,
            },
            'toc': {
                'permalink': md_config.extension_configs.toc.permalink,
                'toc_depth': md_config.extension_configs.toc.toc_depth,
            },
        }

        self.md = markdown.Markdown(
            extensions=md_config.extensions,
            extension_configs=extension_configs,
        )

    def parse_file(self, file_path: Path) -> dict[str, Any]:
        """
        Parse a markdown file completely.

        Returns dict with:
            - metadata: ArticleMetadata
            - content: raw markdown (without docstring)
            - content_html: rendered HTML
            - toc: table of contents
            - word_count: word count
            - reading_time_minutes: estimated reading time
        """
        content = file_path.read_text(encoding='utf-8')
        return self.parse_content(content, file_path.name)

    def parse_content(
        self,
        content: str,
        filename: str = ""
    ) -> dict[str, Any]:
        """Parse markdown content string."""
        # Extract docstring metadata
        metadata_dict, clean_content = self.docstring_parser.parse(content)

        # Update filename in metadata
        if filename and not metadata_dict.get('file_name'):
            metadata_dict['file_name'] = filename

        # Convert to model
        metadata = self.docstring_parser.to_article_metadata(metadata_dict)

        # Render markdown to HTML
        self.md.reset()
        content_html = self.md.convert(clean_content)

        # Extract TOC
        toc = self._extract_toc(clean_content)

        # Calculate word count and reading time
        word_count = self._count_words(clean_content)
        reading_time = self._calculate_reading_time(word_count)

        return {
            'metadata': metadata,
            'content': clean_content,
            'content_html': content_html,
            'toc': toc,
            'word_count': word_count,
            'reading_time_minutes': reading_time,
        }

    def render_html(self, content: str) -> str:
        """Render markdown content to HTML."""
        self.md.reset()
        return self.md.convert(content)

    def _extract_toc(self, content: str) -> list[TableOfContentsEntry]:
        """Extract table of contents from markdown headings."""
        toc: list[TableOfContentsEntry] = []
        stack: list[tuple[int, TableOfContentsEntry]] = []

        for match in self.HEADING_PATTERN.finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()
            explicit_id = match.group(3)

            # Generate slug
            slug = explicit_id if explicit_id else slugify(title)

            entry = TableOfContentsEntry(
                level=level,
                title=title,
                slug=slug,
                children=[],
            )

            # Find parent
            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                # Add as child of parent
                stack[-1][1].children.append(entry)
            else:
                # Top-level entry
                toc.append(entry)

            stack.append((level, entry))

        return toc

    def _count_words(self, content: str) -> int:
        """Count words in markdown content."""
        # Remove markdown syntax
        text = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # Code blocks
        text = re.sub(r'`[^`]+`', '', text)  # Inline code
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
        text = re.sub(r'[#*_~>\-|]', '', text)  # Markdown chars
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

        words = text.split()
        return len(words)

    def _calculate_reading_time(self, word_count: int) -> int:
        """Calculate estimated reading time in minutes."""
        wpm = self.settings.reading.words_per_minute
        min_time = self.settings.reading.min_reading_time

        minutes = max(min_time, round(word_count / wpm))
        return minutes

    def extract_tags(self, content: str, metadata: ArticleMetadata) -> list[str]:
        """
        Extract tags from content and metadata.
        Combines explicit tags with inferred topics.
        """
        tags: set[str] = set()

        # Extract from key features
        for feature in metadata.key_features:
            # Extract key terms from features
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', feature)
            for word in words[:2]:  # Limit to 2 terms per feature
                tags.add(word.lower())

        # Extract from title
        title_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', metadata.title)
        for word in title_words:
            tags.add(word.lower())

        # Extract capitalized terms from content (potential proper nouns/concepts)
        content_terms = re.findall(
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b',
            content[:5000]  # First 5000 chars
        )
        # Count frequency
        term_counts: dict[str, int] = {}
        for term in content_terms:
            term_lower = term.lower()
            term_counts[term_lower] = term_counts.get(term_lower, 0) + 1

        # Add frequent terms
        for term, count in sorted(term_counts.items(), key=lambda x: -x[1])[:10]:
            if count >= 2 and len(term) > 3:
                tags.add(term)

        return sorted(list(tags))[:20]  # Limit to 20 tags


def create_article_content(parsed: dict[str, Any]) -> ArticleContent:
    """Create ArticleContent from parsed data."""
    return ArticleContent(
        raw=parsed['content'],
        html=parsed['content_html'],
        toc=parsed['toc'],
        word_count=parsed['word_count'],
        reading_time_minutes=parsed['reading_time_minutes'],
    )
