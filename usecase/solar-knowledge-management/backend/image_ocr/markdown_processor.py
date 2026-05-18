"""
마크다운 파일 내 이미지 처리 모듈
"""

import re
from pathlib import Path
from typing import List, Dict, Callable, Optional

from .ocr_processor import OCRProcessor
from .alt_text_generator import AltTextGenerator


class MarkdownImageProcessor:
    """마크다운 파일에서 이미지를 찾아 대체 텍스트를 생성하고 업데이트 (Obsidian 전용)"""

    # Obsidian 위키링크 형식: ![[image.png]]
    OBSIDIAN_IMAGE_PATTERN = re.compile(
        r"!\[\[(?P<filename>[^\]]+\.(png|jpg|jpeg))\]\]", re.IGNORECASE
    )

    def __init__(self):
        """MarkdownImageProcessor 초기화"""
        self.ocr_processor = OCRProcessor()
        self.alt_text_generator = AltTextGenerator()
        self._image_cache = {}  # 이미지 파일명 -> 경로 캐시

    def _build_image_cache(self, vault_root: Path) -> None:
        """
        Vault 전체에서 이미지 파일을 재귀적으로 검색하여 캐시 생성

        Args:
            vault_root: Vault 루트 경로
        """
        self._image_cache = {}

        # 지원하는 이미지 확장자
        image_extensions = {".png", ".jpg", ".jpeg"}

        # Vault 전체를 재귀적으로 검색
        for image_path in vault_root.rglob("*"):
            if image_path.is_file() and image_path.suffix.lower() in image_extensions:
                filename = image_path.name
                # 같은 파일명이 여러 개 있을 경우, 첫 번째 것을 사용
                if filename not in self._image_cache:
                    self._image_cache[filename] = image_path

        print(
            f"[INFO] Vault에서 {len(self._image_cache)}개의 이미지 파일을 찾았습니다."
        )

    def _find_image_in_vault(self, filename: str, vault_root: Path) -> Optional[Path]:
        """
        Vault 전체에서 파일명으로 이미지 찾기

        Args:
            filename: 이미지 파일명
            vault_root: Vault 루트 경로

        Returns:
            이미지 파일 경로 (없으면 None)
        """
        # 캐시가 비어있으면 캐시 생성
        if not self._image_cache:
            self._build_image_cache(vault_root)

        return self._image_cache.get(filename)

    def process_images(
        self,
        md_content: str,
        vault_root: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> tuple[str, List[Dict]]:
        """
        마크다운 내용에서 이미지를 찾아 대체 텍스트를 생성하고 업데이트

        Args:
            md_content: 원본 마크다운 내용
            vault_root: Vault 루트 경로 (이미지 파일을 찾을 기준 폴더)
            progress_callback: 진행 상황 콜백 함수 (현재 인덱스, 전체 개수, 이미지 경로)

        Returns:
            (업데이트된 마크다운 내용, 처리된 이미지 정보 리스트)
        """
        # 1. 대체 텍스트가 없는 이미지 수집
        images_to_process = self._collect_images_to_process(md_content, vault_root)

        if not images_to_process:
            return md_content, []

        # 2. 각 이미지에 대해 OCR + LLM 대체 텍스트 생성
        new_content = md_content
        offset = 0
        processed_images = []

        for i, img_data in enumerate(images_to_process):
            # 진행 상황 콜백 호출
            if progress_callback:
                progress_callback(i + 1, len(images_to_process), img_data["src"])

            # 1단계: OCR/Parse 텍스트 추출
            extracted_text = self.ocr_processor.extract_text(img_data["path"])

            # 2단계: LLM 추론으로 대체 텍스트 생성
            if "ERROR" in extracted_text:
                new_alt_text = extracted_text
            else:
                new_alt_text = self.alt_text_generator.generate_alt_text(extracted_text)

            # 텍스트 삽입 로직: 이미지 링크 아래에 대체 텍스트 추가
            match = img_data["match_object"]
            original_string = match.group(0)

            # Obsidian 위키링크 형식 유지 + 아래에 코드 블록으로 대체 텍스트 추가
            replacement_string = f"{original_string}\n```\n(대체 텍스트 by Upstage)\n{new_alt_text}\n```\n"

            start = match.start() + offset
            end = match.end() + offset

            new_content = new_content[:start] + replacement_string + new_content[end:]
            offset += len(replacement_string) - len(original_string)

            # 처리된 이미지 정보 저장
            processed_images.append(
                {
                    "src": img_data["src"],
                    "new_alt_text": new_alt_text,
                }
            )

        return new_content, processed_images

    def _collect_images_to_process(
        self, md_content: str, vault_root: Path
    ) -> List[Dict]:
        """
        마크다운 내용에서 Obsidian 위키링크 형식의 이미지를 수집

        Args:
            md_content: 마크다운 내용
            vault_root: Vault 루트 경로

        Returns:
            처리할 이미지 정보 리스트
        """
        images_to_process = []

        # Obsidian 위키링크 형식 매칭: ![[image.png]]
        for match in self.OBSIDIAN_IMAGE_PATTERN.finditer(md_content):
            filename = match.group("filename").strip()

            # 다음 줄에 코드 블록 "```\n(대체 텍스트 by Upstage)"가 있으면 이미 처리된 것으로 간주
            match_end = match.end()
            remaining_content = md_content[match_end:]

            if remaining_content.startswith("\n```\n(대체 텍스트 by Upstage)"):
                print(f"[INFO] '{filename}'은 이미 대체 텍스트가 있습니다. 건너뜁니다.")
                continue

            # Vault 전체에서 이미지 파일 찾기
            image_full_path = self._find_image_in_vault(filename, vault_root)

            if image_full_path:
                images_to_process.append(
                    {
                        "src": filename,
                        "path": image_full_path,
                        "match_object": match,
                    }
                )
            else:
                print(
                    f"[WARNING] Vault 경로에서 이미지 파일 '{filename}'을 찾을 수 없습니다."
                )

        return images_to_process


if __name__ == "__main__":
    # 테스트 코드
    from dotenv import load_dotenv

    load_dotenv()

    processor = MarkdownImageProcessor()

    # 테스트용 마크다운 내용 (Obsidian 위키링크 형식)
    test_md_content = """
# 테스트 노트

이것은 테스트 이미지입니다.

![[test.png]]
사용자가 작성한 노트 내용...

다른 이미지:

![[diagram.jpg]]
이미 작성된 내용이 있어도 대체 텍스트는 코드 블록으로 구분됩니다.
"""

    test_vault_path = Path("/path/to/vault")

    def test_progress_callback(current: int, total: int, img_src: str):
        print(f"[PROGRESS] {current}/{total} - {img_src}")

    # 처리 실행
    if test_vault_path.exists():
        updated_content, processed = processor.process_images(
            test_md_content, test_vault_path, test_progress_callback
        )
        print(f"\n[INFO] 업데이트된 내용:\n{updated_content}")
        print(f"\n[INFO] 처리된 이미지: {len(processed)}개")
    else:
        print(f"[WARNING] 테스트 Vault 경로를 찾을 수 없습니다: {test_vault_path}")
