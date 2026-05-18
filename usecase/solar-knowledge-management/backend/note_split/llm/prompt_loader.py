"""Prompt template loading functionality."""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from ..models import PromptTemplate
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
            with open(template_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 빈 파일이나 None인 경우 명시적으로 처리
            if data is None:
                print(f"Warning: Template file '{template_name}.yml' is empty or contains no valid YAML content.")
                return None
            
            # data가 딕셔너리가 아닌 경우 처리
            if not isinstance(data, dict):
                print(f"Error loading template {template_name}: YAML content must be a dictionary, got {type(data).__name__}")
                return None

            return PromptTemplate(
                name=data.get('name', template_name),
                description=data.get('description', ''),
                system_prompt=data.get('system_prompt', ''),
                user_prompt_template=data.get('user_prompt_template', '')
            )
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in template {template_name}: {e}")
            return None
        except Exception as e:
            print(f"Error loading template {template_name}: {e}")
            return None

    def list_templates(self) -> List[str]:
        """List all available template names.

        Returns:
            List of template names (without .yml extension)
        """
        if not self.prompts_dir.exists():
            return []

        return [
            p.stem for p in self.prompts_dir.glob('*.yml')
        ]

    def get_templates_info(self) -> Dict[str, str]:
        """Get information about all available templates.

        Returns:
            Dictionary mapping template names to their descriptions
        """
        templates_info = {}
        for template_name in self.list_templates():
            template = self.load_template(template_name)
            if template:
                templates_info[template_name] = template.description
        return templates_info

