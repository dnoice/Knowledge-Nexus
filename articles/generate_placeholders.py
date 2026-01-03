#!/usr/bin/env python3
"""
Generates placeholder markdown files for Knowledge Nexus article directories.

Creates three placeholder files per topic directory:
- {topic}.md (main article)
- {topic}_my_notes.md (personal notes)
- {topic}_works_cited.md (citations)

Directory names use kebab-case, file names use snake_case.
"""

import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent

# Signature and checkmark
SIGNATURE = "︻デ═─── ✦ ✦ ✦ | Aim Twice, Shoot Once!"
CHECKMARK = "✒"

TODAY = datetime.now().strftime("%Y-%m-%d")
TODAY_LONG = datetime.now().strftime("%A, %B %d, %Y")


def kebab_to_snake(s: str) -> str:
    return s.replace("-", "_")


def kebab_to_title(s: str) -> str:
    return " ".join(word.capitalize() for word in s.split("-"))


def create_main_content(topic_title: str, topic_snake: str, relative_path: str) -> str:
    return f'''# {topic_title}

<!--
{CHECKMARK} Metadata
    - Title: {topic_title} (Knowledge Nexus 2026 Edition - v1.0)
    - File Name: {topic_snake}.md
    - Relative Path: {relative_path}\\{topic_snake}.md
    - Artifact Type: docs
    - Version: 1.0.0
    - Date: {TODAY}
    - Update: {TODAY_LONG}
    - Author: Dennis 'dnoice' Smaltz
    - A.I. Acknowledgement: Anthropic - Claude Opus 4.5
    - Signature: {SIGNATURE}

{CHECKMARK} Description:
    Placeholder for comprehensive exploration of {topic_title}.
    This document will serve as a foundational knowledge base for the topic.

{CHECKMARK} Key Features:
    - Feature 1: [To be developed]
    - Feature 2: [To be developed]
    - Feature 3: [To be developed]

{CHECKMARK} Other Important Information:
    - Dependencies: None (documentation only)
    - Compatible platforms: Universal (all markdown renderers)
    - Scope: Comprehensive overview for research and learning
    - Intended audience: Researchers, students, enthusiasts
---------
-->

> **Status**: Placeholder - Content to be developed

## Overview

[Content to be developed]

## Key Concepts

[Content to be developed]

## Current Research

[Content to be developed]

## Applications

[Content to be developed]

## Future Directions

[Content to be developed]

---

> **{SIGNATURE}**
'''


def create_notes_content(topic_title: str, topic_snake: str, relative_path: str) -> str:
    return f'''# {topic_title} - My Notes

<!--
{CHECKMARK} Metadata
    - Title: {topic_title} Notes (Knowledge Nexus 2026 Edition - v1.0)
    - File Name: {topic_snake}_my_notes.md
    - Relative Path: {relative_path}\\{topic_snake}_my_notes.md
    - Artifact Type: docs
    - Version: 1.0.0
    - Date: {TODAY}
    - Update: {TODAY_LONG}
    - Author: Dennis 'dnoice' Smaltz
    - A.I. Acknowledgement: Anthropic - Claude Opus 4.5
    - Signature: {SIGNATURE}

{CHECKMARK} Description:
    Personal notes and observations on {topic_title}.

{CHECKMARK} Key Features:
    - Feature 1: Personal insights and observations
    - Feature 2: Questions for further research
    - Feature 3: Connections to other topics

{CHECKMARK} Other Important Information:
    - Dependencies: None
    - Compatible platforms: Universal
---------
-->

> **Status**: Placeholder - Notes to be added

## Initial Observations

[Notes to be added]

## Questions to Explore

- [ ] Question 1
- [ ] Question 2
- [ ] Question 3

## Connections to Other Topics

[Notes to be added]

## Personal Insights

[Notes to be added]

---

> **{SIGNATURE}**
'''


def create_cited_content(topic_title: str, topic_snake: str, relative_path: str) -> str:
    return f'''# {topic_title} - Works Cited

<!--
{CHECKMARK} Metadata
    - Title: {topic_title} Works Cited (Knowledge Nexus 2026 Edition - v1.0)
    - File Name: {topic_snake}_works_cited.md
    - Relative Path: {relative_path}\\{topic_snake}_works_cited.md
    - Artifact Type: docs
    - Version: 1.0.0
    - Date: {TODAY}
    - Update: {TODAY_LONG}
    - Author: Dennis 'dnoice' Smaltz
    - A.I. Acknowledgement: Anthropic - Claude Opus 4.5
    - Signature: {SIGNATURE}

{CHECKMARK} Description:
    Bibliography and reference materials for {topic_title}.

{CHECKMARK} Key Features:
    - Feature 1: Academic papers and journals
    - Feature 2: Books and monographs
    - Feature 3: Web resources and datasets

{CHECKMARK} Other Important Information:
    - Dependencies: None
    - Compatible platforms: Universal
---------
-->

> **Status**: Placeholder - References to be added

## Academic Papers

[References to be added]

## Books and Monographs

[References to be added]

## Web Resources

[References to be added]

## Datasets and Repositories

[References to be added]

---

> **{SIGNATURE}**
'''


def main():
    import re

    # Get all section directories (03-14, skip 01 and 02)
    sections = [
        d for d in BASE_DIR.iterdir()
        if d.is_dir() and re.match(r"^\d{2}-", d.name) and not re.match(r"^0[12]-", d.name)
    ]

    created_count = 0
    skipped_count = 0

    for section in sorted(sections):
        section_name = section.name
        topics = [d for d in section.iterdir() if d.is_dir()]

        for topic in sorted(topics):
            topic_kebab = topic.name
            topic_snake = kebab_to_snake(topic_kebab)
            topic_title = kebab_to_title(topic_kebab)
            relative_path = f"articles\\{section_name}\\{topic_kebab}"

            main_file = topic / f"{topic_snake}.md"
            notes_file = topic / f"{topic_snake}_my_notes.md"
            cited_file = topic / f"{topic_snake}_works_cited.md"

            # Skip if main file already exists
            if main_file.exists():
                print(f"Skipping {topic_kebab} - files already exist")
                skipped_count += 1
                continue

            print(f"Creating files for: {section_name}/{topic_kebab}")

            # Write files
            main_file.write_text(create_main_content(topic_title, topic_snake, relative_path), encoding="utf-8")
            notes_file.write_text(create_notes_content(topic_title, topic_snake, relative_path), encoding="utf-8")
            cited_file.write_text(create_cited_content(topic_title, topic_snake, relative_path), encoding="utf-8")

            created_count += 1

    print(f"\nPlaceholder generation complete!")
    print(f"Created: {created_count * 3} files ({created_count} topics)")
    print(f"Skipped: {skipped_count} existing topics")


if __name__ == "__main__":
    main()
