"""
UpThink 메인 앱
"""

import os
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="UpThink", page_icon="💭", layout="wide")

# API Key 설정
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")


# 공통 사이드바 설정
def render_common_sidebar():
    """모든 페이지에서 공통으로 사용하는 사이드바"""
    with st.sidebar:
        # Vault 경로 입력
        st.text_input(
            "Vault 경로",
            placeholder="Obsidian Vault의 경로를 입력하세요",
            help="Obsidian Vault 디렉토리의 절대 경로를 입력하세요",
            key="vault_path",
        )

        # 파일 업로드
        st.file_uploader(
            "Markdown 파일 업로드",
            type=["md"],
            help="처리할 마크다운 파일을 업로드하세요",
            key="uploaded_file",
        )


# 공통 사이드바 렌더링
render_common_sidebar()


home = st.Page(
    "home.py",
    title="Intro",
    icon=":material/home:",
    default=True,
)

image_ocr = st.Page(
    "image_ocr.py",
    title="이미지 대체 텍스트 생성",
    icon=":material/image_search:",
)
tag_suggest = st.Page(
    "tag_suggest.py",
    title="태그 추천",
    icon=":material/new_label:",
)
related_note = st.Page(
    "related_note.py",
    title="연관 노트 추천",
    icon=":material/note_stack:",
)
note_split = st.Page(
    "note_split.py",
    title="노트 분할",
    icon=":material/split_scene:",
)
note_freshness = st.Page(
    "note_freshness.py",
    title="최신 정보 확인",
    icon=":material/update:",
)

pg = st.navigation(
    {
        "홈": [home],
        "노트 정리": [
            image_ocr,
            tag_suggest,
            related_note,
            note_split,
        ],
        "최신성 검증": [note_freshness],
    }
)
pg.run()
