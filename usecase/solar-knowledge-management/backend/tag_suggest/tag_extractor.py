"""
사용자의 Vault 폴더 경로를 입력 받아서, 정규표현식으로 태그를 추출하게 됨

태그 형식은 2가지임
1. 해시태그
    #upstage #solar-pro2
2. YAML (노트 최상단 frontmatter)
    ---
    tags:
      - upstage
      - solar-pro2
    ---
"""

import re
import yaml
from pathlib import Path
from typing import List, Set, Dict
from collections import Counter


class TagExtractor:
    """Vault 내 노트들에서 태그를 추출하는 클래스"""

    def __init__(self) -> None:
        # 해시태그 패턴
        self.HASHTAG_PATTERN = r"(?:^|\s)#([a-zA-Z0-9가-힣_-]+)"
        # YAML 패턴
        self.YAML_PATTERN = r"\A---\s*\n(.*?)\n---"
        # YAML tag key
        self.YAML_TAG_KEY = "tags"

    def find_hash_tags(self, content: str) -> List[str]:
        """
        해시태그 패턴의 태그 찾기 (e.g. #upstage)

        Args:
            content: 노트 내용

        Returns:
            추출된 태그 리스트
        """
        hash_tags = re.findall(self.HASHTAG_PATTERN, content)
        return hash_tags

    def find_yaml_tags(self, content: str) -> List[str]:
        """
        YAML 패턴에서 태그 찾기

        Args:
            content: 노트 내용

        Returns:
            추출된 태그 리스트
        """
        yaml_tags = []
        match = re.search(self.YAML_PATTERN, content, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                if isinstance(frontmatter, dict):
                    for key, value in frontmatter.items():
                        if key.lower() in self.YAML_TAG_KEY:
                            if isinstance(value, list):
                                # if tag가 None이거나 빈 문자열("")이 아니면 리스트에 포함
                                yaml_tags.extend([str(tag) for tag in value if tag])
                            elif value:
                                yaml_tags.append(str(value))
            except yaml.YAMLError:
                # 빈 리스트 반환
                pass

        return yaml_tags

    def extract_tags_from_note(self, content: str) -> Set[str]:
        """
        노트에서 모든 태그를 추출

        Args:
            content: 노트 내용

        Returns:
            추출된 태그의 집합
        """
        tags = set()
        tags.update(self.find_hash_tags(content))
        tags.update(self.find_yaml_tags(content))

        return tags

    def extract_tags_from_vault(self, vault_path: str) -> Dict[str, List[str]]:
        """
        Vault 내 모든 노트에서 태그를 추출

        Args:
            vault_path: Vault 디렉토리 경로

        Returns:
            파일 경로는 key, 태그 리스트를 value로 하는 딕셔너리
        """
        vault_dir = Path(vault_path)

        if not vault_dir.exists() or not vault_dir.is_dir():
            raise ValueError(f"유효하지 않은 Vault 경로: {vault_path}")

        tags_by_file = {}

        # 모든 노트 순회
        for md_file in vault_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                tags = self.extract_tags_from_note(content)

                if tags:
                    tags_by_file[str(md_file)] = sorted(list(tags))
            except Exception as e:
                print(f"파일 읽기 실패 {md_file}: {e}")
                continue

        return tags_by_file

    def get_unique_tags(self, vault_path: str) -> Set[str]:
        """
        유니크한 태그만 있도록

        Args:
            vault_path: Vault 디렉토리 경로

        Returns:
            유니크한 태그의 집합
        """
        tags_by_file = self.extract_tags_from_vault(vault_path)
        unique_tags = set()
        for tags in tags_by_file.values():
            unique_tags.update(tags)

        return unique_tags

    def count_tags(self, vault_path: str) -> Dict[str, int]:
        """Vault 내 태그 빈도 계산"""
        tags_by_file = self.extract_tags_from_vault(vault_path)
        tag_counts = Counter()
        for tags in tags_by_file.values():
            tag_counts.update(tags)

        return dict(tag_counts.most_common())


if __name__ == "__main__":
    tag_extractor = TagExtractor()

    MY_VAULT_PATH = "YOUR_PATH_HERE"  # 절대 경로로 입력

    print(f"'{MY_VAULT_PATH}' 경로에서 태그 추출 시작")
    print("-" * 40)

    try:
        # 태그 빈도수 계산
        print("\n태그 빈도수 (가장 많이 사용된 상위 20개)")
        tag_counts = tag_extractor.count_tags(MY_VAULT_PATH)

        if not tag_counts:
            print(" -> 태그를 찾을 수 없습니다.")
        else:
            # 상위 20개만 출력 (너무 많을 경우 대비)
            for tag, count in list(tag_counts.items())[:20]:
                print(f"  - {tag}: {count}회")
            if len(tag_counts) > 20:
                print(f"  ... (외 {len(tag_counts) - 20}개 태그)")

        # 전체 고유 태그 목록
        print("\n전체 고유 태그 목록 (알파벳 순)")
        unique_tags = tag_extractor.get_unique_tags(MY_VAULT_PATH)

        if not unique_tags:
            print(" -> 태그를 찾을 수 없습니다.")
        else:
            print(f" -> 총 {len(unique_tags)}개의 고유 태그 발견")
            print(sorted(list(unique_tags)))

    except ValueError as e:
        print(f"❌ 경로 오류가 발생했습니다: {e}")
        print("MY_VAULT_PATH 변수에 올바른 Vault 폴더 경로를 입력했는지 확인하세요.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")
