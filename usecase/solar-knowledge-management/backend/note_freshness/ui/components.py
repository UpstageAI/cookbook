"""Reusable UI components for Streamlit application."""

import streamlit as st
from typing import List, Optional, Dict


def render_file_input_section():
    """Render the file input section."""
    st.markdown("## 1. 노트 검증")

    note_path = st.text_input(
        "노트 경로",
        placeholder="/path/to/your/note.md",
        help="최신성을 검토할 마크다운 노트 파일의 경로",
    )

    save_folder = st.text_input(
        "저장 폴더 경로 (선택사항)",
        placeholder="미입력시 위에서 입력한 노트가 있는 경로에 저장됩니다",
        help="검색 결과와 가이드를 저장할 폴더",
    )

    return note_path, save_folder


def render_template_selection_section(default_template: str = ""):
    """Render the template selection and editing section."""
    st.markdown("## 2. 추출 템플릿 설정")

    st.markdown(
        """
    아래 템플릿은 노트에서 최신성 검토를 위한 키워드와 쿼리를 추출하는 데 사용됩니다.
    필요에 따라 수정할 수 있습니다.
    """
    )

    template_content = st.text_area(
        "추출 설명 템플릿",
        value=default_template,
        height=300,
        help="Upstage Information Extraction API에 전달할 설명",
    )

    return template_content


def render_metadata_review_section(keywords: List[str], queries: List[str]):
    """Render the metadata review and editing section."""
    st.markdown("## 3. 추출 결과 검토")

    st.markdown("추출된 키워드와 쿼리를 검토하고 필요시 수정하세요.")

    # Keywords editing
    st.markdown("### 검색 키워드 (Wikipedia)")
    keywords_text = st.text_area(
        "키워드 (한 줄에 하나씩)",
        value="\n".join(keywords),
        height=150,
        help="Wikipedia 검색에 사용할 키워드",
    )
    edited_keywords = [kw.strip() for kw in keywords_text.split("\n") if kw.strip()]

    # Queries editing
    st.markdown("### 검색 쿼리 (Tavily)")
    queries_text = st.text_area(
        "쿼리 (한 줄에 하나씩)",
        value="\n".join(queries),
        height=150,
        help="Tavily 검색에 사용할 쿼리",
    )
    edited_queries = [q.strip() for q in queries_text.split("\n") if q.strip()]

    return edited_keywords, edited_queries


def render_search_results_section(wiki_results: List[dict], tavily_results: List[dict]):
    """Render the search results section."""
    st.markdown("## 4. 검색 결과")

    # Wikipedia results
    if wiki_results:
        st.markdown("### Wikipedia 검색 결과")
        for result in wiki_results:
            with st.expander(
                f"📖 {result.get('title', 'Unknown')} ({result.get('keyword', '')})"
            ):
                st.markdown(f"**요약:** {result.get('summary', 'N/A')[:500]}...")
                if result.get("url"):
                    st.markdown(f"[Wikipedia 링크]({result['url']})")

    # Tavily results
    if tavily_results:
        st.markdown("### Tavily 검색 결과")
        for result in tavily_results:
            query = result.get("query", "")
            st.markdown(f"#### 쿼리: {query}")
            for item in result.get("results", []):
                with st.expander(f"🔍 {item.get('title', 'Unknown')}"):
                    st.markdown(f"**내용:** {item.get('content', 'N/A')[:500]}...")
                    if item.get("url"):
                        st.markdown(f"[원본 링크]({item['url']})")


def render_guide_preview(guide_content: str):
    """Render the generated guide preview."""
    st.markdown("## 5. 최신성 검토 가이드")

    with st.expander("가이드 전체 보기", expanded=True):
        st.markdown(guide_content)


def render_error(message: str):
    """Render an error message."""
    st.error(f"❌ {message}")


def render_success(message: str):
    """Render a success message."""
    st.success(f"✅ {message}")


def render_info(message: str):
    """Render an info message."""
    st.info(f"ℹ️ {message}")
