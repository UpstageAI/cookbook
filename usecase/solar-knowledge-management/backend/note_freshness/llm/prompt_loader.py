"""Prompt template loading functionality for note freshness."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from backend.note_split.models import PromptTemplate
from ..config import Config


class PromptLoader:
    """Loader for prompt templates from YAML files."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt loader.

        Args:
            prompts_dir: Directory containing prompt template files
        """
        self.prompts_dir = prompts_dir or Config.PROMPTS_DIR

    def load_template(self, template_name: str) -> Optional[PromptTemplate]:
        """Load a specific prompt template by name.

        Args:
            template_name: Name of the template file (without .yml extension)

        Returns:
            PromptTemplate object or None if not found
        """
        template_path = self.prompts_dir / f"{template_name}.yml"

        if not template_path.exists():
            return None

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                print(f"Warning: Template file '{template_name}.yml' is empty.")
                return None

            if not isinstance(data, dict):
                print(f"Error: Template {template_name} must be a dictionary.")
                return None

            return PromptTemplate(
                name=data.get("name", template_name),
                description=data.get("description", ""),
                system_prompt=data.get("system_prompt", ""),
                user_prompt_template=data.get("user_prompt_template", ""),
            )
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in template {template_name}: {e}")
            return None
        except Exception as e:
            print(f"Error loading template {template_name}: {e}")
            return None

    def load_schema(self, schema_name: str) -> Optional[str]:
        """Load a JSON schema from a YAML file.

        Args:
            schema_name: Name of the schema file (without .yml extension)

        Returns:
            Schema string or None if not found
        """
        schema_path = self.prompts_dir / f"{schema_name}.yml"

        if not schema_path.exists():
            return None

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None or "schema" not in data:
                return None

            return data["schema"].strip()
        except Exception as e:
            print(f"Error loading schema {schema_name}: {e}")
            return None

    def list_templates(self) -> List[str]:
        """List all available template names."""
        if not self.prompts_dir.exists():
            return []

        return [p.stem for p in self.prompts_dir.glob("*.yml")]
