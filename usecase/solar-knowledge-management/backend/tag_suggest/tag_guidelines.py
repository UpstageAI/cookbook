"""
태그 작성을 위한 가이드라인 생성

사용자의 체크리스트를 받아서 LLM에게 태그 작성 가이드라인을 전달

---
✅ 체크리스트
주로 사용하는 언어
영어 사용 시 대소문자 규칙
단어의 구분자
태그 개수
"""

from typing import Dict, Any, TypedDict


class ChecklistType(TypedDict, total=False):
    """태그 작성 패턴 체크리스트 타입"""

    language: str  # ko, en
    case_style: str  # lowercase, uppercase (영어 사용 시)
    separator: str  # hyphen, underscore
    tag_count_range: Dict[str, int]  # min, max


class GuidelineGenerator:
    """태그 작성 가이드라인 생성 클래스"""

    def __init__(self, checklist: ChecklistType) -> None:
        self.checklist = checklist
        self._validate_checklist()

    def _validate_checklist(self) -> None:
        """체크리스트 유효성 검사"""
        required_fields = [
            "language",
            "separator",
            "tag_count_range",
        ]

        for field in required_fields:
            if field not in self.checklist:
                raise ValueError(f"필수 항목이 누락되었습니다: {field}")

        # 영어 사용 시 case_style 필수
        if self.checklist["language"] in ["en"]:
            if "case_style" not in self.checklist:
                raise ValueError("영어 사용 시 대소문자 설정은 필수입니다")

            if self.checklist["case_style"] not in ["lowercase", "uppercase"]:
                raise ValueError("영어 사용 시 대소문자 설정은 필수입니다")

        # tag_count_range 검증
        tag_range = self.checklist.get("tag_count_range", {})

        min_val = tag_range["min"]
        max_val = tag_range["max"]

        if "min" not in tag_range or "max" not in tag_range:
            raise ValueError("태그의 최소, 최대 개수 설정이 필요합니다")

        if min_val > max_val:
            raise ValueError(f"'{min_val}'은 '{max_val}'보다 작거나 같아야 합니다")

        if min_val < 2 or max_val > 10:
            raise ValueError("태그 개수는 최소 2개, 최대 10개로 제한됩니다")

    def generate_guideline(self) -> str:
        """
        체크리스트를 바탕으로 태그 작성 가이드라인 생성

        Returns:
            LLM 프롬프트에 사용할 가이드라인 문자열
        """
        guideline_parts = [
            "# 태그 작성 가이드라인\n",
            "다음 규칙을 **반드시** 준수하여 태그를 생성해 주세요.\n",
        ]

        # 주로 사용하는 언어
        guideline_parts.append(self._generate_language_rule())

        # 영어 사용 시 대소문자 규칙
        if self.checklist["language"] in ["en"]:
            guideline_parts.append(self._generate_case_rule())

        # 단어의 구분이 필요할 경우
        guideline_parts.append(self._generate_separator_rule())

        # 선호하는 태그 개수
        guideline_parts.append(self._generate_count_rule())

        # Output 형식
        guideline_parts.append(self._generate_output_format())

        return "\n".join(guideline_parts)

    def _generate_language_rule(self) -> str:
        """언어 규칙 생성"""
        language = self.checklist["language"]

        language_map = {
            "ko": "**한국어**만 사용하세요.",
            "en": "**영어**만 사용하세요.",
        }

        rule = language_map[language]
        return f"## 주로 사용하는 언어\n{rule}\n"

    def _generate_case_rule(self) -> str:
        """대소문자 규칙 생성 (영어 사용 시)"""
        case_style = self.checklist.get("case_style", "lowercase")

        case_map = {
            "lowercase": f"**소문자**만 사용하세요.",
            "uppercase": f"**대문자**만 사용하세요.",
        }

        rule = case_map[case_style]
        return f"## 대소문자 규칙\n{rule}\n"

    def _generate_separator_rule(self) -> str:
        """단어 구분자 규칙 생성"""
        separator = self.checklist["separator"]

        separator_map = {
            "hyphen": "단어의 사이를 **하이픈(-)**으로 구분하세요.",
            "underscore": "단어의 사이를 **언더스코어(_)**로 구분하세요.",
        }

        rule = separator_map[separator]
        return f"## 단어에서 구분자가 필요한 경우\n{rule}\n"

    def _generate_count_rule(self) -> str:
        """태그 개수 규칙 생성"""
        tag_range = self.checklist["tag_count_range"]
        min_count = tag_range["min"]
        max_count = tag_range["max"]

        return (
            f"## 태그 개수 (CRITICAL)\n"
            f"**반드시 {min_count}개 이상 {max_count}개 이하의 태그만 생성하세요.**\n"
            f"- {min_count}개보다 적으면 안 됩니다.\n"
            f"- {max_count}개보다 많으면 안 됩니다.\n"
            f"- 이 규칙을 위반하면 응답이 거부됩니다.\n"
        )

    def _generate_output_format(self) -> str:
        """Output 형식 규칙 생성"""
        return (
            "# Output Format\n"
            "Return ONLY the JSON object:\n"
            "```json\n"
            '{"tags": ["...", "...", "...", ..., "..."]}\n'
            "```"
        )

    def get_summary(self) -> Dict[str, Any]:
        """
        체크리스트 요약 정보 반환

        Returns:
            체크리스트의 주요 설정을 요약한 딕셔너리
        """
        summary = {
            "언어": self.checklist["language"],
            "대소문자": self.checklist.get("case_style", "N/A"),
            "구분자": self.checklist["separator"],
            "태그 개수": f"{self.checklist['tag_count_range']['min']}-{self.checklist['tag_count_range']['max']}개",
        }

        return summary


if __name__ == "__main__":
    test_checklist: ChecklistType = {
        "language": "en",
        "case_style": "lowercase",
        "separator": "hyphen",
        "tag_count_range": {"min": 3, "max": 5},
    }

    guidelines_generator = GuidelineGenerator(test_checklist)
    summary = guidelines_generator.get_summary()
    print("\n체크리스트 요약:")
    for key, value in summary.items():
        print(f"  - {key}: {value}")

    print("\n생성된 가이드라인:")
    print(guidelines_generator.generate_guideline())
