"""
가이드라인과 markdown 파일을 받아, 신규 태그를 생성
"""

import os
import json

from openai import OpenAI
from dotenv import load_dotenv

from .tag_guidelines import GuidelineGenerator

load_dotenv()


class TagGenerator:
    """LLM을 사용하여 마크다운 내용을 기반으로 태그 생성"""

    def __init__(
        self,
        model: str = "solar-pro2",
        temperature: float = 0.3,
        max_tokens: int = 1000,
        reasoning_effort: str = "high",
        timeout: int = 300,
    ):
        """
        TagGenerator 초기화

        Args:
            model: 사용할 LLM 모델 (기본값: "solar-pro2")
            temperature: 생성 다양성 (0.0-1.0, 기본값: 0.3)
            max_tokens: 최대 토큰 수 (기본값: 1000)
            reasoning_effort: reasoning 강도 (기본값: "high")
            timeout: API 타임아웃 (초 단위, 기본값: 300 = 5분)
        """
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.upstage.ai/v1",
            timeout=timeout,
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort

    def _parse_llm_response(self, response: str) -> list[str]:
        """
        LLM 응답을 파싱하여 태그 리스트 추출

        Args:
            response: LLM의 원본 응답

        Returns:
            파싱된 태그 리스트

        Raises:
            ValueError: JSON 파싱 실패 시
        """
        if not response:
            raise ValueError("LLM 응답이 비어있습니다")

        # 다양한 형식의 코드 블록 제거
        cleaned_response = response.strip()

        if cleaned_response.startswith("```"):
            # 첫 번째 줄 제거 (```json, ```JSON, ``` 등)
            lines = cleaned_response.split("\n", 1)
            if len(lines) > 1:
                cleaned_response = lines[1]
            else:
                cleaned_response = cleaned_response[3:]

        # 마지막 ``` 제거
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        cleaned_response = cleaned_response.strip()

        # JSON 파싱
        try:
            parsed = json.loads(cleaned_response)
            tags = parsed.get("tags", [])
            if not isinstance(tags, list):
                raise ValueError("tags가 리스트 형식이 아닙니다")
            return tags
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM 응답을 JSON으로 파싱할 수 없습니다: {cleaned_response[:200]}"
            ) from e

    def generate_tags(
        self,
        guideline_generator: GuidelineGenerator,
        md_content: str,
        filename: str,
        max_retries: int = 5,
    ) -> list[str]:
        """
        가이드라인과 마크다운 내용을 기반으로 태그 생성

        Args:
            guideline_generator: 태그 생성 가이드라인 생성기
            md_content: 마크다운 파일 내용
            filename: 파일명 (LLM 컨텍스트 제공용)
            max_retries: 최대 재시도 횟수 (기본값: 5)

        Returns:
            생성된 태그 리스트

        Raises:
            ValueError: LLM 응답이 올바른 JSON 형식이 아닌 경우
            Exception: LLM API 호출 실패 시
        """
        # 가이드라인 생성
        system_prompt = guideline_generator.generate_guideline()

        # 사용자 메시지 구성
        user_message = f"markdown 파일: {filename}\n\n{md_content}"

        last_error = None

        for attempt in range(max_retries):
            try:
                # LLM API 호출
                print(f"[DEBUG] 태그 생성 시작 (시도 {attempt + 1}/{max_retries})")
                print(f"[DEBUG] 모델: {self.model}, reasoning_effort: {self.reasoning_effort}")
                print(f"[DEBUG] API 호출 중... (최대 {self.client.timeout}초 대기)")

                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_message,
                        },
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    reasoning_effort=self.reasoning_effort,
                    stream=False,
                )

                print(f"[DEBUG] API 응답 수신 완료")

                # 응답 추출
                if not stream.choices:
                    raise ValueError("LLM 응답에 choices가 없습니다")

                response = stream.choices[0].message.content
                print(f"[DEBUG] 응답 파싱 시작")

                # 응답 파싱
                tags = self._parse_llm_response(response)
                print(f"[DEBUG] 태그 생성 완료: {len(tags)}개")
                return tags

            except ValueError as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(
                        f"[WARNING] 태그 생성 실패 (시도 {attempt + 1}/{max_retries}): {e}"
                    )
                    # temperature를 약간 조정하여 재시도
                    self.temperature = min(self.temperature + 0.1, 1.0)
                continue
            except Exception as e:
                raise Exception(f"태그 생성 중 오류 발생: {str(e)}") from e

        # 모든 재시도 실패
        raise Exception(
            f"태그 생성 실패 ({max_retries}회 시도): {str(last_error)}"
        ) from last_error


if __name__ == "__main__":
    import pathlib
    from backend.tag_suggest import ChecklistType, GuidelineGenerator

    # 테스트용 체크리스트
    checklist: ChecklistType = {
        "language": "en",
        "case_style": "lowercase",
        "separator": "hyphen",
        "tag_count_range": {"min": 3, "max": 5},
    }

    # 가이드라인 생성기 초기화
    guideline_gen = GuidelineGenerator(checklist)
    tag_gen = TagGenerator()

    # 테스트용 마크다운 파일
    FILENAME = "YOUR_FILE_HERE"
    DATA_PATH = pathlib.Path(__file__).parent.parent.parent / "data" / FILENAME

    if not DATA_PATH.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {DATA_PATH}")
        exit(1)

    print(f"[INFO] 파일 경로: {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()

    try:
        print(f"[INFO] 태그 생성 시작")
        tags = tag_gen.generate_tags(guideline_gen, md_content, FILENAME)
        print(f"\n[SUCCESS] 생성된 태그: {tags}")
        print(f"[INFO] 태그 개수: {len(tags)}")
    except Exception as e:
        print(f"\n[ERROR] 에러 발생: {e}")
        import traceback

        traceback.print_exc()
