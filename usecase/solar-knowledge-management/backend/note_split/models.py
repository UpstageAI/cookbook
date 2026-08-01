"""Data models for the atomic notes application."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Topic:
    """Represents a topic extracted from a raw note.

    Attributes:
        topic: The name/title of the topic
        coverage: Brief summary/overview of the topic
        line_numbers: List of line numbers in the raw note related to this topic
        keywords: List of key terms related to this topic
        user_direction: Optional user instructions for generating the atomic note
        use_llm: Whether to use LLM for generating atomic note content
        selected: Whether this topic is selected for batch operations
    """
    topic: str
    coverage: str
    line_numbers: List[int] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    user_direction: Optional[str] = None
    use_llm: bool = False
    selected: bool = False

    def to_dict(self) -> dict:
        """Convert Topic to dictionary."""
        return {
            'topic': self.topic,
            'coverage': self.coverage,
            'line_numbers': self.line_numbers,
            'keywords': self.keywords,
            'user_direction': self.user_direction,
            'use_llm': self.use_llm,
            'selected': self.selected
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Topic':
        """Create Topic from dictionary."""
        return cls(
            topic=data.get('topic', ''),
            coverage=data.get('coverage', ''),
            line_numbers=data.get('line_numbers', []),
            keywords=data.get('keywords', []),
            user_direction=data.get('user_direction'),
            use_llm=data.get('use_llm', False),
            selected=data.get('selected', False)
        )

    def get_properties_markdown(self) -> str:
        """Generate markdown properties section for the atomic note."""
        props = [
            "---",
            f"topic: {self.topic}",
            f"coverage: {self.coverage}",
            f"line_numbers: {self.line_numbers}",
            f"keywords: {', '.join(self.keywords)}",
        ]
        if self.user_direction:
            props.append(f"user_direction: {self.user_direction}")
        props.append("---")
        return '\n'.join(props)


@dataclass
class PromptTemplate:
    """Represents a prompt template for LLM interaction.

    Attributes:
        name: Template identifier
        description: Brief description of the template's purpose
        system_prompt: System-level instructions for the LLM
        user_prompt_template: Template for user prompt with placeholders
    """
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str

    def format_user_prompt(self, **kwargs) -> str:
        """Format the user prompt with given variables."""
        return self.user_prompt_template.format(**kwargs)

