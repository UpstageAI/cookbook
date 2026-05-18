"""File handling operations for note freshness."""

import re
import yaml
from pathlib import Path
from typing import Optional, Tuple, Union
from datetime import datetime
from ..models import FreshnessMetadata
from .path_utils import resolve_path


class FileHandler:
    """Handler for file operations related to note freshness."""

    @staticmethod
    def _resolve_path(path: Union[str, Path]) -> Path:
        return resolve_path(path)

    @staticmethod
    def read_note(
        note_path: Union[str, Path],
    ) -> Tuple[Optional[str], Optional[FreshnessMetadata]]:
        """Read a markdown note file and extract metadata.

        Args:
            note_path: Path to the note file

        Returns:
            Tuple of (full content as string, FreshnessMetadata) or (None, None) on error
        """
        try:
            resolved_path = FileHandler._resolve_path(note_path)
            with open(resolved_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract YAML front matter
            metadata = FileHandler._extract_yaml_metadata(content)
            return content, metadata
        except FileNotFoundError:
            print(f"File not found: {note_path}")
            return None, None
        except Exception as e:
            print(f"Error reading file {note_path}: {e}")
            return None, None

    @staticmethod
    def _extract_yaml_metadata(content: str) -> FreshnessMetadata:
        """Extract freshness-related metadata from YAML front matter."""
        metadata = FreshnessMetadata()

        # Match YAML front matter
        yaml_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if yaml_match:
            try:
                yaml_content = yaml.safe_load(yaml_match.group(1))
                if yaml_content:
                    # Extract info_keyword
                    info_keyword = yaml_content.get("info_keyword", [])
                    if isinstance(info_keyword, str):
                        info_keyword = [info_keyword]
                    metadata.info_keyword = info_keyword

                    # Extract info_query
                    info_query = yaml_content.get("info_query", [])
                    if isinstance(info_query, str):
                        info_query = [info_query]
                    metadata.info_query = info_query

                    # Extract search timestamps
                    metadata.wiki_searched_at = yaml_content.get("wiki_searched_at")
                    metadata.tavily_searched_at = yaml_content.get("tavily_searched_at")
            except yaml.YAMLError as e:
                print(f"Error parsing YAML metadata: {e}")

        return metadata

    @staticmethod
    def update_note_metadata(
        note_path: Union[str, Path],
        info_keyword: list = None,
        info_query: list = None,
        wiki_searched_at: str = None,
        tavily_searched_at: str = None,
    ) -> bool:
        """Update the YAML front matter of a note with freshness metadata.

        Args:
            note_path: Path to the note file
            info_keyword: List of keywords for Wikipedia search
            info_query: List of queries for Tavily search
            wiki_searched_at: Timestamp of Wikipedia search
            tavily_searched_at: Timestamp of Tavily search

        Returns:
            True if successful, False otherwise
        """
        try:
            resolved_path = FileHandler._resolve_path(note_path)
            with open(resolved_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if YAML front matter exists
            yaml_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)

            if yaml_match:
                # Parse existing YAML
                try:
                    yaml_content = yaml.safe_load(yaml_match.group(1)) or {}
                except yaml.YAMLError:
                    yaml_content = {}

                # Update metadata
                if info_keyword is not None:
                    yaml_content["info_keyword"] = info_keyword
                if info_query is not None:
                    yaml_content["info_query"] = info_query
                if wiki_searched_at is not None:
                    yaml_content["wiki_searched_at"] = wiki_searched_at
                if tavily_searched_at is not None:
                    yaml_content["tavily_searched_at"] = tavily_searched_at

                # Reconstruct content with updated YAML
                new_yaml = yaml.dump(
                    yaml_content,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
                new_content = f"---\n{new_yaml}---{content[yaml_match.end():]}"
            else:
                # Create new YAML front matter
                yaml_content = {}
                if info_keyword is not None:
                    yaml_content["info_keyword"] = info_keyword
                if info_query is not None:
                    yaml_content["info_query"] = info_query
                if wiki_searched_at is not None:
                    yaml_content["wiki_searched_at"] = wiki_searched_at
                if tavily_searched_at is not None:
                    yaml_content["tavily_searched_at"] = tavily_searched_at

                new_yaml = yaml.dump(
                    yaml_content,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
                new_content = f"---\n{new_yaml}---\n\n{content}"

            # Write back to file
            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"Error updating note metadata: {e}")
            return False

    @staticmethod
    def save_search_result(
        save_folder: Union[str, Path], filename: str, content: str
    ) -> bool:
        """Save search result to a markdown file.

        Args:
            save_folder: Folder to save the result
            filename: Name of the file (without extension)
            content: Markdown content to save

        Returns:
            True if successful, False otherwise
        """
        try:
            resolved_folder = FileHandler._resolve_path(save_folder)
            resolved_folder.mkdir(parents=True, exist_ok=True)

            file_path = resolved_folder / f"{filename}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving search result: {e}")
            return False

    @staticmethod
    def insert_freshness_guide(
        note_path: Union[str, Path], guide_summary: str, full_guide_path: str
    ) -> bool:
        """Insert freshness guide summary at the top of the note (after YAML).

        Args:
            note_path: Path to the note file
            guide_summary: Summary of the freshness guide
            full_guide_path: Relative path to the full guide

        Returns:
            True if successful, False otherwise
        """
        try:
            resolved_path = FileHandler._resolve_path(note_path)
            with open(resolved_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find end of YAML front matter
            yaml_match = re.match(r"^---\s*\n.*?\n---\s*\n?", content, re.DOTALL)

            # Create the guide block
            guide_block = f"""
> [!info] 최신성 검토 가이드
> {guide_summary}
>
> [[{full_guide_path}|전체 가이드 보기]]

"""

            if yaml_match:
                # Insert after YAML
                insert_pos = yaml_match.end()
                new_content = content[:insert_pos] + guide_block + content[insert_pos:]
            else:
                # Insert at the beginning
                new_content = guide_block + content

            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"Error inserting freshness guide: {e}")
            return False

    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
