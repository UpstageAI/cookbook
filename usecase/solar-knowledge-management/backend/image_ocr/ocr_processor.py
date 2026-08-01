"""
OCR 및 문서 구조 추출 API 호출 모듈
"""

import os
import requests
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class OCRProcessor:
    """Upstage Document Parse API를 사용하여 이미지에서 OCR 텍스트 및 구조를 추출"""

    def __init__(self):
        """
        OCRProcessor 초기화

        Raises:
            ValueError: UPSTAGE_API_KEY 환경 변수가 설정되지 않은 경우
        """
        self.api_key: Optional[str] = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다")

        self.ocr_endpoint: str = "https://api.upstage.ai/v1/document-digitization"

    def extract_text(self, image_path: Path) -> str:
        """
        Upstage Document Parse API를 사용하여 이미지에서 OCR 텍스트 및 구조를 추출합니다.

        Args:
            image_path: 추출할 이미지 파일 경로

        Returns:
            추출된 텍스트 (오류 시 ERROR 메시지)

        Raises:
            requests.exceptions.HTTPError: HTTP 요청 실패 시
            Exception: 기타 처리 오류 시
        """
        try:
            # 요청 헤더 구성
            headers: Dict[str, str] = {"Authorization": f"Bearer {self.api_key}"}
            mime_type = "image/" + image_path.suffix.lstrip(".")

            # 파일을 with 문으로 안전하게 열기
            with open(image_path, "rb") as image_file:
                files = {
                    "document": (
                        image_path.name,
                        image_file,
                        mime_type,
                    )
                }

                # 공식 데이터 파라미터
                data_payload: Dict = {
                    "model": "document-parse",
                    "ocr": "force",  # OCR 강제 실행
                    "output_formats": "['markdown', 'text']",  # 출력 형식 명시
                    "base64_encoding": "['table', 'figure']",  # 테이블과 이미지 포함
                }

                response = requests.post(
                    self.ocr_endpoint,
                    headers=headers,
                    files=files,
                    data=data_payload,
                    timeout=120,
                )

            response.raise_for_status()
            response_json: Dict = response.json()

            # Document Parse 결과에서 추출된 텍스트를 반환
            # 1. 최상위 content 객체에서 text 추출 (우선순위: text > markdown)
            content = response_json.get("content", {})
            extracted_text = content.get("text", "").strip() or content.get("markdown", "").strip()

            # 2. content가 없으면 elements 배열에서 추출
            if not extracted_text and "elements" in response_json:
                elements = response_json.get("elements", [])
                text_parts = []

                for element in elements:
                    element_content = element.get("content", {})
                    # 각 element의 텍스트 추출 (우선순위: text > markdown)
                    element_text = element_content.get("text", "").strip() or element_content.get("markdown", "").strip()

                    if element_text:
                        text_parts.append(element_text)

                extracted_text = "\n\n".join(text_parts)

            # 디버깅: 추출된 텍스트 길이 출력
            print(f"[INFO] OCR 결과: {len(extracted_text)}자 추출 (파일: {image_path.name})")
            if not extracted_text:
                print(f"[WARNING] OCR이 빈 텍스트를 반환했습니다.")
                print(f"[DEBUG] API 응답 구조: content={bool(content)}, elements={len(response_json.get('elements', []))}개")

            return extracted_text

        except requests.exceptions.HTTPError as e:
            error_msg = (
                f"ERROR: OCR/Parse API 요청 실패 (HTTP {e.response.status_code})"
            )
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] 응답 상세: {e.response.text}")
            return f"{error_msg}: {e.response.text[:100]}"
        except Exception as e:
            error_msg = f"ERROR: OCR Processing Failed - {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg


if __name__ == "__main__":
    # 테스트 코드
    processor = OCRProcessor()
    test_image_path = Path("test_image.png")

    if test_image_path.exists():
        result = processor.extract_text(test_image_path)
        print(f"[INFO] OCR 결과: {result[:200]}...")
    else:
        print(f"[WARNING] 테스트 이미지 파일을 찾을 수 없습니다: {test_image_path}")
