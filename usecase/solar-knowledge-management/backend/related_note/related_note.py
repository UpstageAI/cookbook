from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_upstage import UpstageEmbeddings
from pathlib import Path
import tiktoken
import math
from uuid import uuid4
import os
import re

load_dotenv()


class Related_Note:
    """
    Obsidian vault 안의 md 파일들을 임베딩하고,
    특정 노트에 대한 연관 노트 3개를 찾아 [[링크]]로 추가하는 클래스.

    - UpstageEmbeddings + Chroma DB 사용
    - embedded_markers.txt 로 "이미 임베딩된 파일"을 추적
    """

    def __init__(self, vault_path: str) -> None:
        """
        - vault_path / vector_store 경로 / embedded marker 경로 설정
        - Upstage 임베딩 객체 생성
        - Chroma 벡터스토어 로드 또는 새로 생성
        - embedded_markers.txt 파일이 없으면 빈 파일 생성
        * embedded_markers는 이미 임베딩된 노트들 기록해둠으로서 추후 중복 임베딩 및 저장 피하는 용도

        Args:
            vault_path (str): Obsidian Vault 디렉토리의 절대 경로
        """
        self.vault_path = Path(vault_path).resolve()
        base_path = Path(__file__).resolve()
        self.embedding_path = base_path.parent
        self.store_dir = self.embedding_path / "vector_store"
        self.marker_root = self.embedding_path / "embedded_markers.txt"

        # 임베딩 / 토크나이저 설정
        self.embeddings = UpstageEmbeddings(model="embedding-query")
        # 업스테이지 임베딩 최대 가능 인풋인 4000토큰 측정
        self.enc = tiktoken.encoding_for_model("text-embedding-3-small")

        # Chroma 벡터스토어 초기화
        self.vector_store = self._init_vector_store()

        # 마커 파일 보장
        self._ensure_marker_file()

    def _init_vector_store(self) -> Chroma:
        """
        Chroma 벡터스토어를 초기화합니다.

        Returns:
            Chroma: persist_directory를 가지는 Chroma 인스턴스.
        """
        if self.store_dir.exists():
            return Chroma(
                persist_directory=str(self.store_dir),
                embedding_function=self.embeddings,
            )
        else:
            # Chroma.from_texts 를 쓰기 위해 dummy 데이터 한 번 넣었다가 바로 삭제
            random_id = str(uuid4())
            vs = Chroma.from_texts(
                texts=["dummy_data"],
                ids=[random_id],
                embedding=self.embeddings,
                persist_directory=str(self.store_dir),
            )
            vs.delete(ids=[random_id])
            return vs

    def _ensure_marker_file(self) -> None:
        """
        embedded_markers.txt 파일이 없으면 빈 파일로 생성합니다.
        Args:
            None
        Returns:
            None
        """
        if not self.marker_root.exists():
            self.marker_root.write_text("", encoding="utf-8")

    # ──────────────────────────────────────────────────────────
    # 마커(이미 임베딩된 노트) 관련
    # ──────────────────────────────────────────────────────────
    def load_embedded_notes(self) -> set[str]:
        """
        이미 임베딩된 노트들의 상대 경로 집합을 읽어옵니다.
        Args:
            None
        Returns:
            set[str]: vault 기준 경로 집합.
        """
        if not self.marker_root.exists():
            return set()

        lines = self.marker_root.read_text(encoding="utf-8").splitlines()
        return {line.strip() for line in lines if line.strip()}

    def save_embedded_notes(self, new_notes: list[str]) -> None:
        """
        새로 임베딩된 노트들의 상대 경로를 마커 파일에 추가합니다.
        Args:
            new_notes (list[str]): vault 기준 상대 경로 리스트.
        Returns:
            None
        """
        with self.marker_root.open("a", encoding="utf-8") as f:
            for rel in new_notes:
                f.write(rel + "\n")

    # ──────────────────────────────────────────────────────────
    # 임베딩 대상 선택 / 청킹 / 전처리
    # ──────────────────────────────────────────────────────────
    def get_unembedded_notes(self) -> list[str]:
        """
        아직 임베딩되지 않은 md 파일 경로들을 찾습니다.
        - embedded_markers.txt에 없는 파일만 대상
        - 'upthink' 디렉토리 하위는 제외
        - 경로는 vault 기준 상대 경로로 반환

        Args:
            None
        Returns:
            list[str]: 아직 임베딩되지 않은 md 파일들의 상대 경로 리스트.

        * frontend의 경우, to_embed 리스트 내 파일을 임베딩하겠다는 메시지를 보여주면 될 것 같습니다.
        """
        embedded = self.load_embedded_notes()
        to_embed: list[str] = []

        for md_file in self.vault_path.rglob("*.md"):
            rel = md_file.relative_to(self.vault_path).as_posix()
            if ".venv" in rel.split("/"):
                continue
            if rel not in embedded:
                to_embed.append(rel)

        return to_embed

    def chunk_text(self, text: str) -> list[str]:
        """
        텍스트를 최대 약 4000 토큰 단위로 청킹합니다.
        Args:
            text (str): 원본 텍스트.
        Returns:
            list[str]: 청크 텍스트 리스트. (4000 토큰 이하이면 길이 1 리스트)
        """
        token_list = self.enc.encode(text)
        total_tokens = len(token_list)
        chunks: list[str] = []

        if total_tokens > 4000:
            n_chunks = math.ceil(total_tokens / 4000)
            chunk_size = math.ceil(total_tokens / n_chunks)
            for i in range(0, total_tokens, chunk_size):
                chunk_tokens = token_list[i : i + chunk_size]
                chunk_text = self.enc.decode(chunk_tokens)
                chunks.append(chunk_text)
        else:
            chunks.append(text)

        return chunks

    def clean_text(self, text: str) -> str:
        """
        md 파일 내용을 간단히 전처리합니다.
        - Windows/Unix 줄바꿈 정규화 (Windows 호환성)
        - 특수 공백 문자 제거 (non-breaking space 등)
        - 굵게(**) 마크다운 제거
        - 연속 개행을 하나로 축소
        - 앞뒤 공백 제거

        Args:
            text (str): 원본 텍스트.
        Returns:
            str: 전처리된 텍스트.
        """
        # Windows 줄바꿈(\r\n)을 Unix 스타일(\n)로 정규화
        x = text.replace("\r\n", "\n").replace("\r", "\n")
        x = re.sub(r"[\xa0\u200b]", "", x)
        x = re.sub(r"\*\*", "", x)
        x = re.sub(r"\n+", "\n", x)
        x = x.strip()
        return x

    # ──────────────────────────────────────────────────────────
    # 임베딩 실행
    # ──────────────────────────────────────────────────────────
    def index_unembedded_notes(self) -> None:
        """
        아직 임베딩되지 않은 md 파일들을 찾아 모두 임베딩합니다.
        - get_unembedded_notes()로 대상 탐색
        - clean_text() + chunk_text()로 전처리/청킹
        - Chroma.add_texts()로 벡터스토어에 추가
        - embedded_markers.txt에 기록

        Args:
            None
        Returns:
            None
        """
        to_embed = self.get_unembedded_notes()

        if not to_embed:
            return

        for note_rel in to_embed:
            note_path = self.vault_path / note_rel
            raw_text = note_path.read_text(encoding="utf-8")
            cleaned = self.clean_text(raw_text)

            # 빈 텍스트는 임베딩 건너뛰기 (Windows 호환성)
            if not cleaned or not cleaned.strip():
                # 빈 파일도 마커에 기록하여 다음에 다시 시도하지 않음
                self.save_embedded_notes([note_rel])
                continue

            chunks = self.chunk_text(cleaned)

            if len(chunks) > 1:
                for i, chunk in enumerate(chunks, start=1):
                    # 빈 청크는 건너뛰기
                    if not chunk or not chunk.strip():
                        continue
                    self.vector_store.add_texts(
                        ids=[str(uuid4())],
                        metadatas=[
                            {
                                "title": f"{Path(note_rel).stem}_{i}",
                                "path": note_rel,
                            }
                        ],
                        texts=[chunk],
                    )
            else:
                self.vector_store.add_texts(
                    ids=[str(uuid4())],
                    metadatas=[
                        {
                            "title": Path(note_rel).stem,
                            "path": note_rel,
                        }
                    ],
                    texts=[cleaned],
                )

            self.save_embedded_notes([note_rel])

    # ──────────────────────────────────────────────────────────
    # 연관 노트 찾기 & 링크 삽입
    # ──────────────────────────────────────────────────────────
    def find_related_notes(self, MY_VAULT_PATH: str, k: int = 3) -> list[str]:
        """
        주어진 노트와 의미적으로 유사한 md 파일 경로를 찾습니다.
        Args:
            MY_VAULT_PATH (str):
                vault 기준 상대 경로, 사용자가 input으로 넣을 경로
                예) "upthink/data/HCI 2025 학회 강의세션들.md"
            k (int, optional):
                최대 몇 개의 연관 노트를 반환할지. 기본값 3.
        Returns:
            list[str]:
                연관 노트들의 vault 기준 상대 경로 리스트.
                (자기 자신은 포함하지 않으며, 중복 제거됨)
                * frontend에 해당 노트들이 추천되었다는 문구가 간단하게 보여졌으면 좋겠습니다.
        """

        norm_query = Path(MY_VAULT_PATH).as_posix()
        query_note_path = self.vault_path / norm_query

        raw_text = query_note_path.read_text(encoding="utf-8")
        cleaned = self.clean_text(raw_text)
        query_chunks = self.chunk_text(cleaned)

        # 첫 번째 청크 기준으로 유사도 검색
        hits = self.vector_store.similarity_search(query_chunks[0], k=k + 4)
        related: list[str] = []
        for d in hits:
            raw_path = d.metadata.get("path", "")
            if not raw_path:
                continue
            norm_path = Path(raw_path).as_posix()

            # 자기 자신은 제외
            if norm_path == norm_query:
                continue

            # 중복 제외
            if norm_path in related:
                continue

            related.append(norm_path)

            if len(related) >= k:
                break
        return related

    def append_related_links(self, MY_VAULT_PATH: str, k: int = 3):
        """
        주어진 노트 파일의 끝에 "Related Notes" 섹션을 추가하고
        [[연관노트]] 링크를 최대 k개까지 삽입합니다.
        Args:
            MY_VAULT_PATH (str):
                vault 기준 상대 경로.
                예) r"upthink\\data\\HCI 2025 학회 강의세션들.md"
            k (int, optional):
                삽입할 링크 개수 (최대). 기본값 3.
        Returns:
            None
        """
        print(MY_VAULT_PATH)
        related = self.find_related_notes(MY_VAULT_PATH, k=k)
        if not related:
            return

        norm_query = Path(MY_VAULT_PATH).as_posix()
        target_path = self.vault_path / norm_query

        with target_path.open("a", encoding="utf-8") as f:
            list_ = []
            f.write("\n\n## 🔗 Related Notes\n")
            for path_rel in related[:k]:
                # Obsidian 링크에서는 확장자(.md)를 떼기 위해 [:-3]
                f.write(f"[[{path_rel[:-3]}]]\n")
                list_.append(path_rel[:-3])
            return list_


# ──────────────────────────────────────────────────────────
# 단독 실행용 예시
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Vault 경로를 지정해야 합니다
    MY_VAULT_PATH = "YOUR_VAULT_PATH_HERE"  # 예: "/Users/username/Documents/MyVault"

    engine = Related_Note(vault_path=MY_VAULT_PATH)

    # 1) 아직 임베딩 안 된 노트들 임베딩
    engine.index_unembedded_notes()

    # 2) 특정 노트에 대해 연관 노트 3개 링크 삽입
    engine.append_related_links(r"upthink\data\HCI 2025 학회 강의세션들.md", k=3)
