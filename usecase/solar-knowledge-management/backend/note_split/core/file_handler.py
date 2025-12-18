"""File handling operations for raw notes and atomic notes."""
from pathlib import Path
from typing import List, Optional, Tuple, Union
from ..models import Topic
from ..config import Config
from .path_utils import resolve_path


class FileHandler:
    """Handler for file operations related to notes."""

    @staticmethod
    def _resolve_path(path: Union[str, Path]) -> Path:
        """Resolve and normalize a path for the current environment.
        
        Args:
            path: Path string or Path object
            
        Returns:
            Resolved and normalized Path object
        """
        return resolve_path(path)

    @staticmethod
    def read_note(note_path: Union[str, Path]) -> Tuple[Optional[str], Optional[List[str]]]:
        """Read a markdown note file.

        Args:
            note_path: Path to the note file (string or Path)

        Returns:
            Tuple of (full content as string, list of lines) or (None, None) on error
        """
        try:
            resolved_path = FileHandler._resolve_path(note_path)
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            return content, lines
        except FileNotFoundError:
            print(f"File not found: {note_path}")
            return None, None
        except Exception as e:
            print(f"Error reading file {note_path}: {e}")
            return None, None

    @staticmethod
    def get_lines_content(lines: List[str], line_numbers: List[int]) -> str:
        """Extract content from specific line numbers.

        Args:
            lines: List of all lines in the document
            line_numbers: List of line numbers to extract (1-indexed)

        Returns:
            Concatenated content of specified lines
        """
        content_lines = []
        for line_num in sorted(line_numbers):
            # Convert 1-indexed to 0-indexed
            idx = line_num - 1
            if 0 <= idx < len(lines):
                content_lines.append(lines[idx])

        return '\n'.join(content_lines)

    @staticmethod
    def insert_backlinks(
        lines: List[str],
        topics: List[Topic]
    ) -> List[str]:
        """Insert backlinks to atomic notes in the raw note.

        Backlinks are inserted at the last line of consecutive line ranges
        to improve readability.

        Args:
            lines: List of lines from the raw note
            topics: List of Topic objects with line numbers

        Returns:
            Modified list of lines with backlinks inserted
        """
        # Create a mapping of line numbers to topics
        line_to_backlinks = {}

        for topic in topics:
            if not topic.line_numbers:
                continue

            # Group consecutive line numbers
            sorted_lines = sorted(topic.line_numbers)
            ranges = []
            current_range = [sorted_lines[0]]

            for line_num in sorted_lines[1:]:
                if line_num == current_range[-1] + 1:
                    current_range.append(line_num)
                else:
                    ranges.append(current_range)
                    current_range = [line_num]
            ranges.append(current_range)

            # Add backlink to the last line of each range
            for line_range in ranges:
                last_line = line_range[-1]
                if last_line not in line_to_backlinks:
                    line_to_backlinks[last_line] = []
                line_to_backlinks[last_line].append(f"[[{topic.topic}|{topics.index(topic) + 1}]]")

        # Insert backlinks into lines
        modified_lines = []
        for i, line in enumerate(lines, 1):
            modified_lines.append(line)
            if i in line_to_backlinks:
                # Add backlinks at the end of the line
                backlinks_str = ' '.join(line_to_backlinks[i])
                modified_lines[-1] = f"{line} {backlinks_str}"

        return modified_lines

    @staticmethod
    def append_topic_list(
        lines: List[str],
        topics: List[Topic]
    ) -> List[str]:
        """Append list of generated atomic notes to the end of raw note.

        Args:
            lines: List of lines from the raw note
            topics: List of Topic objects

        Returns:
            Modified list of lines with topic list appended
        """
        # Add separator
        lines.append('')
        lines.append('---')
        lines.append('&&&')
        lines.append('')
        lines.append('## Generated Atomic Notes')
        lines.append('')

        # Add topic links
        for topic in topics:
            lines.append(f"{topics.index(topic) + 1}. [[{topic.topic}]]")

        return lines

    @staticmethod
    def create_atomic_note(
        topic: Topic,
        related_content: str,
        generated_content: Optional[str] = None
    ) -> str:
        """Create content for an atomic note.

        Args:
            topic: Topic object with metadata
            related_content: Content extracted from the raw note
            generated_content: Optional LLM-generated content for the note

        Returns:
            Complete markdown content for the atomic note
        """
        parts = []

        # Add properties
        parts.append(topic.get_properties_markdown())
        parts.append('')

        # Add title
        parts.append(f"# {topic.topic}")
        parts.append('')

        # Add overview
        parts.append("## Overview")
        parts.append(topic.coverage)
        parts.append('')

        # Add related content from raw note
        if related_content:
            parts.append("## Related Content from Raw Note")
            parts.append('')
            parts.append(related_content)
            parts.append('')

        # Add generated content if available
        if generated_content:
            parts.append("## Generated Content")
            parts.append('')
            parts.append(generated_content)
            parts.append('')

        # Add keywords section
        if topic.keywords:
            parts.append("## Keywords")
            parts.append('')
            parts.append(', '.join(f"`{kw}`" for kw in topic.keywords))
            parts.append('')

        return '\n'.join(parts)

    @staticmethod
    def save_atomic_note(
        save_folder: Union[str, Path],
        topic: Topic,
        content: str
    ) -> bool:
        """Save an atomic note to a file.

        Args:
            save_folder: Folder to save the atomic note (string or Path)
            topic: Topic object
            content: Markdown content for the note

        Returns:
            True if successful, False otherwise
        """
        try:
            resolved_folder = FileHandler._resolve_path(save_folder)
            # Ensure save folder exists
            resolved_folder.mkdir(parents=True, exist_ok=True)

            # Sanitize filename
            safe_filename = FileHandler._sanitize_filename(topic.topic)
            file_path = resolved_folder / f"{safe_filename}.md"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving atomic note: {e}")
            return False

    @staticmethod
    def save_raw_note(note_path: Union[str, Path], lines: List[str]) -> bool:
        """Save the modified raw note.

        Args:
            note_path: Path to the raw note file (string or Path)
            lines: List of lines to write

        Returns:
            True if successful, False otherwise
        """
        try:
            resolved_path = FileHandler._resolve_path(note_path)
            content = '\n'.join(lines)
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving raw note {note_path}: {e}")
            return False

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize a string to be used as a filename.

        Args:
            filename: String to sanitize

        Returns:
            Sanitized filename
        """
        # Replace invalid characters with underscore
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length
        max_length = 200
        if len(filename) > max_length:
            filename = filename[:max_length]

        return filename.strip()

