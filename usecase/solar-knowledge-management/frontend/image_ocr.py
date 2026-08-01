"""
노트 내 이미지에서 텍스트 추출 -> 대체 텍스트 생성
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
import streamlit as st
from typing import Optional

from backend.image_ocr import MarkdownImageProcessor


def init_session_state():
    """세션 상태 초기화 (이미지 OCR 전용)"""
    # vault_path와 uploaded_file은 공통 요소여서, frontend/app.py 에서 관리
    if "image_ocr_step" not in st.session_state:
        st.session_state.image_ocr_step = 1


def main():
    """메인 함수"""
    init_session_state()

    # 메인 헤더
    st.title("🖼️ 이미지 대체 텍스트 생성")
    st.caption("노트 내 이미지가 어떤 정보를 가지고 있는지 쉽게 제공받을 수 있습니다!")
    st.text("")

    # API 키 확인
    UPSTAGE_API_KEY: Optional[str] = os.getenv("UPSTAGE_API_KEY")
    if not UPSTAGE_API_KEY:
        st.error(
            "⚠️ **UPSTAGE_API_KEY** 환경 변수가 설정되지 않았습니다. "
            "AI 기능을 사용하려면 터미널에 `export UPSTAGE_API_KEY='YOUR_KEY'` 명령을 실행하고 앱을 재시작하세요."
        )
        return

    # Step 1: Vault 경로 및 파일 확인
    if st.session_state.image_ocr_step == 1:
        vault_path_str = st.session_state.get("vault_path", "")
        uploaded_file = st.session_state.get("uploaded_file")

        if vault_path_str and uploaded_file:
            vault_root = Path(vault_path_str.strip())
            if not vault_root.is_dir():
                st.error(
                    f"오류: 입력된 경로 ({vault_path_str})는 유효한 폴더가 아닙니다."
                )
                return

            st.info(
                f"- Vault 경로:ㅤ{vault_path_str}\n"
                f"- Markdown 파일:ㅤ{uploaded_file.name}\n\n"
                f"**💡 변경이 필요한 경우 왼쪽 사이드바에서 수정해 주세요.**"
            )
            if st.button("이미지 대체 텍스트 생성 시작", type="primary"):
                st.session_state.image_ocr_step = 2
                st.rerun()
        else:
            st.warning(
                "👈ㅤ왼쪽 사이드바에서 ***Vault 경로*** 와 ***Markdown 파일 업로드*** 설정을 완료해 주세요."
            )

    # Step 2: 이미지 처리 (자동 실행)
    elif st.session_state.image_ocr_step == 2:
        vault_path_str = st.session_state.get("vault_path", "")
        uploaded_file = st.session_state.get("uploaded_file")
        vault_root = Path(vault_path_str.strip())

        try:
            # 마크다운 내용 읽기
            md_content = uploaded_file.getvalue().decode("utf-8")

            # 프로세서 초기화
            processor = MarkdownImageProcessor()

            # 진행 상황 표시
            progress_container = st.container()
            with progress_container:
                st.divider()
                st.subheader("🔍 OCR 분석 및 LLM 추론")
                progress_bar = st.progress(0, text="초기화 중...")
                status_text = st.empty()

            # 진행 상황 콜백 함수
            def progress_callback(current: int, total: int, img_src: str):
                progress = current / total
                progress_bar.progress(progress)
                status_text.caption(f"[{current}/{total}] '{img_src}' 처리 중...")

            # 이미지 처리 실행
            processed_md, processed_images = processor.process_images(
                md_content, vault_root, progress_callback
            )

            # 진행 상황 표시 완료
            progress_bar.empty()
            status_text.empty()

            # 결과를 세션에 저장
            st.session_state.processed_md = processed_md
            st.session_state.processed_images = processed_images

            # Step 3로 이동
            st.session_state.image_ocr_step = 3
            st.rerun()

        except Exception as e:
            st.error(f"❌ 이미지 처리 실패: {e}")
            with st.expander("상세 오류 정보"):
                import traceback

                st.code(traceback.format_exc())

    # Step 3: 처리 결과 표시
    elif st.session_state.image_ocr_step == 3:
        processed_md = st.session_state.get("processed_md", "")
        processed_images = st.session_state.get("processed_images", [])
        uploaded_file = st.session_state.get("uploaded_file")

        # 결과 확인
        if not processed_images:
            st.info(
                "🔍 대체 텍스트 생성이 필요한 이미지가 없거나 이미지가 포함되지 않았습니다."
            )
            return

        # 처리된 이미지 목록 표시
        with st.expander("📊 처리된 이미지 목록", expanded=False):
            for img_info in processed_images:
                st.caption(
                    f"'{img_info['src']}' 텍스트 생성 완료: *{img_info['new_alt_text'][:50]}...*"
                )

        st.success(
            f"✅ 이미지 처리 완료. {len(processed_images)}개 이미지가 업데이트되었습니다."
        )

        # 결과 표시
        st.divider()
        st.subheader("✅ 처리 결과 확인")

        col_download, _, col_reset = st.columns([1, 2, 1])

        with col_reset:
            if st.button(
                "🔄ㅤ새로고침",
                use_container_width=True,
                type="secondary",
                help="처음 단계로 돌아갑니다",
            ):
                # 세션 데이터 정리
                if "processed_md" in st.session_state:
                    del st.session_state.processed_md
                if "processed_images" in st.session_state:
                    del st.session_state.processed_images
                st.session_state.image_ocr_step = 1
                st.rerun()

        with col_download:
            st.download_button(
                label="⬇️ㅤ다운로드",
                data=processed_md,
                file_name=f"processed_{uploaded_file.name}",
                type="primary",
                mime="text/markdown",
                use_container_width=True,
            )

        st.code(processed_md, language="markdown")


if __name__ == "__main__":
    main()
