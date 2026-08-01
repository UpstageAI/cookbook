"""
마크다운 파일 처리 유틸리티

YAML frontmatter 추가 등 마크다운 파일 관련 기능 제공
"""

from datetime import datetime
from typing import List


def add_yaml_frontmatter(md_content: str, tags: List[str]) -> str:
    """
    마크다운 파일 최상단에 YAML frontmatter를 추가

    Args:
        md_content: 원본 마크다운 내용
        tags: 추가할 태그 리스트

    Returns:
        YAML frontmatter가 추가된 마크다운 내용

    Examples:
        >>> content = "# Hello World"
        >>> result = add_yaml_frontmatter(content, ["python", "tutorial"])
        >>> "tags:" in result
        True
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # 태그 리스트를 YAML 형식으로 변환
    tags_yaml = "\n".join([f"  - {tag}" for tag in tags])

    # YAML frontmatter 생성
    frontmatter = f"""---
created: {today}
modified: {today}
tags:
{tags_yaml}
---

"""

    return frontmatter + md_content
