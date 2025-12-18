"""
LLM을 사용하여 OCR 텍스트로부터 대체 텍스트 생성
"""

import os
from openai import OpenAI
from openai import APIError as OpenAIAPIError
from dotenv import load_dotenv

load_dotenv()


class AltTextGenerator:
    """OCR 추출 텍스트를 solar-pro2 LLM에 입력하여 대체 텍스트를 생성"""

    def __init__(
        self,
        model: str = "solar-pro2",
        max_tokens: int = 150,
    ):
        """
        AltTextGenerator 초기화

        Args:
            model: 사용할 LLM 모델 (기본값: "solar-pro2")
            max_tokens: 최대 토큰 수 (기본값: 150)

        Raises:
            ValueError: UPSTAGE_API_KEY 환경 변수가 설정되지 않은 경우
        """
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.upstage.ai/v1",
        )
        self.model = model
        self.max_tokens = max_tokens

    def generate_alt_text(self, extracted_text: str) -> str:
        """
        추출된 텍스트를 solar-pro2 LLM에 입력하여 대체 텍스트를 생성합니다.

        Args:
            extracted_text: OCR로 추출된 텍스트

        Returns:
            생성된 대체 텍스트 (오류 시 ERROR 메시지)

        Raises:
            OpenAIAPIError: LLM API 호출 오류
            Exception: 기타 처리 오류
        """
        if not extracted_text:
            error_msg = "ERROR: OCR에서 추출된 텍스트가 비어있습니다. 이미지에 텍스트가 없거나 OCR이 실패했을 수 있습니다."
            print(f"[WARNING] {error_msg}")
            return error_msg

        if extracted_text.startswith("ERROR"):
            return extracted_text

        try:
            # LLM 프롬프트
            prompt_text: str = (
                f"다음은 이미지에서 추출된 텍스트와 문서 구조 분석 결과입니다.\n\n---\n{extracted_text}\n---\n\n"
                f"이 내용을 바탕으로 이미지의 내용을 상세히 설명하고, 이 설명을 시각 장애인을 위한 **대체 텍스트**로 "
                f"50단어 내외의 한국어로 생성해주세요. 오직 생성된 대체 텍스트만 출력하세요."
            )

            # solar-pro2 LLM 호출 (텍스트 전용)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt_text}],
                max_tokens=self.max_tokens,
            )

            return response.choices[0].message.content.strip()

        except OpenAIAPIError as e:
            error_msg = f"ERROR: LLM 추론 API 오류 (HTTP {e.response.status_code})"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] 응답 상세: {e.response.text}")
            return f"{error_msg}: {e.response.text[:100]}"
        except Exception as e:
            error_msg = f"ERROR: LLM Processing Failed - {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg


if __name__ == "__main__":
    # 테스트 코드
    generator = AltTextGenerator()

    # 테스트용 OCR 추출 텍스트
    test_extracted_text = """
    Machine Learning 개요
    - 지도 학습: 레이블이 있는 데이터로 학습
    - 비지도 학습: 레이블이 없는 데이터로 패턴 발견
    - 강화 학습: 보상을 통한 학습
    """

    result = generator.generate_alt_text(test_extracted_text)
    print(f"[INFO] 생성된 대체 텍스트: {result}")
