"""
신규 생성된 태그와 기존 태그를 비교하여 매칭 및 추천

Qwen Embedding 모델을 사용하여 의미적 유사도 계산
"""

import numpy as np
from typing import List, Optional
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer

from .tag_extractor import TagExtractor


@dataclass
class TagMatch:
    """태그 매칭 결과"""

    new_tag: str  # 신규 생성된 태그
    matched_tag: Optional[str]  # 매칭된 기존 태그 (없으면 None)
    similarity: float  # 유사도 점수 (0.0 ~ 1.0)
    is_new: bool  # 완전히 새로운 태그인지 여부


class TagComparator:
    """신규 태그와 기존 태그를 비교하여 매칭 및 추천"""

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
    ):
        """
        TagComparator 초기화

        Args:
            similarity_threshold: 유사도 임계값 (이상이면 같은 태그로 간주)
            model_name: 사용할 임베딩 모델명
        """
        print(f"[INFO] Embedding 모델 로딩 중: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        self.tag_extractor = TagExtractor()

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 리스트를 embedding 벡터로 변환

        Args:
            texts: 변환할 텍스트 리스트

        Returns:
            embedding 벡터 배열 (shape: [len(texts), embedding_dim])

        Raises:
            ValueError: 빈 텍스트가 포함된 경우
        """
        if not texts:
            return np.array([])

        # 빈 문자열 필터링 및 검증
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if len(valid_texts) != len(texts):
            print(
                f"[WARNING] {len(texts) - len(valid_texts)}개의 빈 태그가 제거되었습니다"
            )

        if not valid_texts:
            raise ValueError("유효한 텍스트가 없습니다")

        # SentenceTransformer로 embedding 생성 (기존 태그/신규 태그 모두 document로 처리)
        embeddings = self.model.encode(valid_texts)

        return embeddings

    def compare_tags(
        self, new_tags: List[str], existing_tags: List[str]
    ) -> List[TagMatch]:
        """
        신규 태그와 기존 태그를 비교하여 매칭

        Args:
            new_tags: 신규 생성된 태그 리스트
            existing_tags: 기존 태그 리스트

        Returns:
            각 신규 태그에 대한 매칭 결과 리스트

        Raises:
            ValueError: 유효하지 않은 태그가 포함된 경우
            Exception: Embedding 생성 실패 시
        """
        if not new_tags:
            return []

        # 빈 문자열 필터링
        valid_new_tags = [tag.strip() for tag in new_tags if tag and tag.strip()]
        if len(valid_new_tags) != len(new_tags):
            print(
                f"[WARNING] {len(new_tags) - len(valid_new_tags)}개의 빈 신규 태그가 제거되었습니다"
            )

        if not valid_new_tags:
            raise ValueError("유효한 신규 태그가 없습니다")

        if not existing_tags:
            # 기존 태그가 없으면 모두 새로운 태그
            return [
                TagMatch(new_tag=tag, matched_tag=None, similarity=0.0, is_new=True)
                for tag in valid_new_tags
            ]

        valid_existing_tags = [
            tag.strip() for tag in existing_tags if tag and tag.strip()
        ]
        if not valid_existing_tags:
            print("[WARNING] 유효한 기존 태그가 없어 모든 태그를 신규로 처리합니다")
            return [
                TagMatch(new_tag=tag, matched_tag=None, similarity=0.0, is_new=True)
                for tag in valid_new_tags
            ]

        try:
            # Embedding 생성 (신규 태그와 기존 태그 모두 같은 공간에서 처리)
            new_tag_embeddings = self._get_embeddings(valid_new_tags)
            existing_tag_embeddings = self._get_embeddings(valid_existing_tags)

            # 모든 신규 태그와 기존 태그 간의 유사도를 한번에 계산
            all_similarities = self.model.similarity(
                new_tag_embeddings, existing_tag_embeddings
            )

            results = []

            # 각 신규 태그에 대해 가장 유사한 기존 태그 찾기
            for i, new_tag in enumerate(valid_new_tags):
                # i번째 신규 태그의 모든 유사도
                similarities = all_similarities[i]

                # 가장 유사한 태그 찾기
                max_similarity_idx = np.argmax(similarities)
                max_similarity = float(similarities[max_similarity_idx])

                # 임계값 이상이면 매칭, 아니면 새로운 태그
                if max_similarity >= self.similarity_threshold:
                    matched_tag = valid_existing_tags[max_similarity_idx]
                    is_new = False
                else:
                    matched_tag = None
                    is_new = True

                results.append(
                    TagMatch(
                        new_tag=new_tag,
                        matched_tag=matched_tag,
                        similarity=max_similarity,
                        is_new=is_new,
                    )
                )

            return results

        except Exception as e:
            raise Exception(f"태그 비교 중 오류 발생: {str(e)}") from e

    def get_recommended_tags(
        self, new_tags: List[str], vault_path: str
    ) -> List[TagMatch]:
        """
        Vault에서 기존 태그를 추출하고 신규 태그와 비교

        Args:
            new_tags: 신규 생성된 태그 리스트
            vault_path: Vault 디렉토리 경로

        Returns:
            각 신규 태그에 대한 매칭 결과 리스트
        """
        # Vault에서 기존 태그 추출
        existing_tags = list(self.tag_extractor.get_unique_tags(vault_path))

        # 비교 및 매칭
        return self.compare_tags(new_tags, existing_tags)

    @staticmethod
    def get_final_tags(matches: List[TagMatch]) -> List[str]:
        """
        매칭 결과를 기반으로 최종 추천 태그 리스트 생성

        Args:
            matches: 태그 매칭 결과 리스트

        Returns:
            최종 추천 태그 리스트 (기존 태그로 대체되거나 새로운 태그, 중복 제거됨)
        """
        final_tags = []
        seen_tags = set()

        for match in matches:
            if match.is_new:
                # 새로운 태그
                tag = match.new_tag
            else:
                # 기존 태그로 대체
                tag = match.matched_tag

            # 중복 체크 후 추가
            if tag not in seen_tags:
                final_tags.append(tag)
                seen_tags.add(tag)

        return final_tags


if __name__ == "__main__":
    import pathlib
    import traceback
    from .tag_guidelines import GuidelineGenerator, ChecklistType
    from .tag_generator import TagGenerator

    # 설정
    VAULT_PATH = "YOUR_PATH_HERE"
    TEST_FILE = "YOUR_FILE_HERE"

    print("=" * 60)
    print("전체 태그 추천 파이프라인 테스트")
    print("=" * 60)

    try:
        # 1. Vault에서 기존 태그 추출
        print("\n[1단계] Vault에서 기존 태그 추출 중...")
        comparator = TagComparator()

        if not pathlib.Path(VAULT_PATH).exists():
            print(f"[WARNING] Vault 경로를 찾을 수 없습니다: {VAULT_PATH}")
            print("[INFO] 기존 태그 없이 테스트를 진행합니다")
            existing_tags = []
        else:
            existing_tags = list(comparator.tag_extractor.get_unique_tags(VAULT_PATH))
            print(f"✓ 기존 태그 {len(existing_tags)}개 발견")
            print(f"  예시: {sorted(existing_tags)[:10]}")
            if len(existing_tags) > 10:
                print(f"  ... 외 {len(existing_tags) - 10}개")

        # 2. 신규 태그 생성
        print(f"\n[2단계] '{TEST_FILE}'에서 신규 태그 생성 중...")

        # 체크리스트 설정
        checklist: ChecklistType = {
            "language": "en",
            "case_style": "lowercase",
            "separator": "hyphen",
            "tag_count_range": {"min": 2, "max": 3},
        }

        # 가이드라인 생성기 초기화
        guideline_gen = GuidelineGenerator(checklist)

        # 태그 생성기 초기화
        tag_gen = TagGenerator()

        # 마크다운 파일 읽기
        data_path = pathlib.Path(__file__).parent.parent.parent / "data" / TEST_FILE

        if not data_path.exists():
            print(f"[ERROR] 파일을 찾을 수 없습니다: {data_path}")
            exit(1)

        with open(data_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # 태그 생성
        new_tags = tag_gen.generate_tags(guideline_gen, md_content, TEST_FILE)
        print(f"✓ 신규 태그 생성 완료: {new_tags}")
        print(f"  태그 개수: {len(new_tags)}")

        # 3. 태그 비교 및 매칭
        print(f"\n[3단계] 신규 태그와 기존 태그 비교 중...")
        matches = comparator.compare_tags(new_tags, existing_tags)

        print("\n[매칭 결과]")
        print("-" * 60)
        for match in matches:
            status = "✓ 매칭됨" if not match.is_new else "✗ 신규"
            matched_info = (
                f"→ {match.matched_tag}" if match.matched_tag else "→ 추가 필요"
            )
            print(
                f"{status} | {match.new_tag:30s} {matched_info:25s} (유사도: {match.similarity:.3f})"
            )

        # 4. 최종 추천 태그
        final_tags = TagComparator.get_final_tags(matches)
        print(f"\n[최종 추천 태그]")
        print("-" * 60)
        print(final_tags)
        print(f"  최종 태그 개수: {len(final_tags)}")

        # 통계
        new_count = sum(1 for m in matches if m.is_new)
        matched_count = len(matches) - new_count
        print(f"\n[통계]")
        print(f"  신규 태그: {new_count}개")
        print(f"  매칭된 태그: {matched_count}개")

        print("\n" + "=" * 60)
        print("테스트 완료!")

    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {e}")
        traceback.print_exc()
        exit(1)
