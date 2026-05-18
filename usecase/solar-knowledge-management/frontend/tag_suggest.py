"""
노트 태그 추천 Streamlit 앱
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import re
import time
import traceback
import streamlit as st

from backend.tag_suggest import (
    TagExtractor,
    GuidelineGenerator,
    ChecklistType,
    TagGenerator,
    TagComparator,
    TagMatch,
    add_yaml_frontmatter,
)


def init_session_state():
    """세션 상태 초기화 (태그 추천 전용)"""
    # vault_path와 uploaded_file은 공통 요소여서, frontend/app.py 에서 관리

    # 체크리스트 (태그 생성 가이드라인)
    if "checklist" not in st.session_state:
        st.session_state.checklist = None
    # 기존 태그
    if "existing_tags" not in st.session_state:
        st.session_state.existing_tags = []
    # 신규 태그 (생성된 태그)
    if "new_tags" not in st.session_state:
        st.session_state.new_tags = []
    # 태그 비교
    if "matches" not in st.session_state:
        st.session_state.matches = []

    if "step" not in st.session_state:
        st.session_state.step = 1


def render_existing_tags_preview():
    """기존 태그 수집 결과"""
    vault_path_str = st.session_state.get("vault_path", "")
    if not vault_path_str:
        return

    vault_path = Path(vault_path_str.strip())
    if not vault_path.exists():
        st.warning(f"⚠️ Vault 경로를 찾을 수 없습니다: {vault_path_str}")
        return

    # 기존 태그가 아직 로드되지 않았다면 로드
    if not st.session_state.existing_tags:
        with st.spinner("기존 태그를 수집하는 중..."):
            try:
                extractor = TagExtractor()
                existing_tags = list(extractor.get_unique_tags(str(vault_path)))
                st.session_state.existing_tags = existing_tags
            except Exception as e:
                st.error(f"❌ 태그 수집 실패: {e}")
                return

    existing_tags = st.session_state.existing_tags

    # 결과 표시
    with st.expander("📊 기존 태그 미리보기", expanded=False):
        if existing_tags:
            st.info(f"✓ 총 **{len(existing_tags)}개**의 고유 태그 발견")

            # 빈도순으로 상위 10개 태그 표시
            try:
                extractor = TagExtractor()
                tag_counts = extractor.count_tags(str(vault_path))

                # 상위 10개 추출
                top_10_tags = list(tag_counts.items())[:10]

                st.markdown("**상위 10개 태그 (빈도순):**")
                st.code(", ".join([tag for tag, _ in top_10_tags]))

                if len(existing_tags) > 10:
                    st.caption(f"... 외 {len(existing_tags) - 10}개")
            except Exception as e:
                # 빈도 계산 실패 시 기존 방식으로 폴백
                st.markdown("**태그 목록 (일부):**")
                st.code(", ".join(sorted(existing_tags)[:10]))
                if len(existing_tags) > 10:
                    st.caption(f"... 외 {len(existing_tags) - 10}개")
        else:
            st.warning("⚠️ 기존 태그가 없습니다. 모든 태그가 새로운 태그로 추가됩니다.")


def render_checklist_form():
    """체크리스트 설문 폼 렌더링"""
    with st.container(border=True):
        st.markdown("#### 📝 태그 작성 가이드라인")
        col_lang, col_case = st.columns(2)
        col_sep, col_num = st.columns(2)

        # 주로 사용하는 언어
        with col_lang:
            st.markdown("**1/ 주로 사용하는 언어**")
            language = st.radio(
                "언어",
                options=["en", "ko"],
                format_func=lambda x: {
                    "en": "영어",
                    "ko": "한국어",
                }[x],
                label_visibility="collapsed",
                key="language_radio",
            )

        # 대소문자 규칙 (영어 사용 시)
        with col_case:
            st.markdown("**2/ 영어 대소문자 규칙**")
            case_style = None
            if language in ["en"]:
                case_style = st.radio(
                    "대소문자",
                    options=["lowercase", "uppercase"],
                    format_func=lambda x: {
                        "lowercase": "소문자 (e.g., `upstage`)",
                        "uppercase": "대문자 (e.g., `UPSTAGE`)",
                    }[x],
                    label_visibility="collapsed",
                    key="case_style_radio",
                )

        # 단어 구분자
        with col_sep:
            st.markdown("**3/ 단어 구분자**")
            separator = st.radio(
                "구분자",
                options=["hyphen", "underscore"],
                format_func=lambda x: {
                    "hyphen": "하이픈ㅤㅤ (e.g., `deep-learning`)",
                    "underscore": "언더스코어 (e.g., `deep_learning`)",
                }[x],
                label_visibility="collapsed",
                key="separator_radio",
            )

        # 태그 개수
        with col_num:
            st.markdown("**4/ 태그 개수 범위** (최소 2개, 최대 10개)")
            col_min, col_max = st.columns(2)
            with col_min:
                min_count = st.number_input(
                    "최소",
                    min_value=2,
                    max_value=10,
                    value=2,
                    key="min_count_input",
                )
            with col_max:
                max_count = st.number_input(
                    "최대",
                    min_value=2,
                    max_value=10,
                    value=5,
                    key="max_count_input",
                )

            # 최소값이 최대값보다 크면 경고
            if min_count > max_count:
                warning_min = st.warning("⚠️ 최소값이 최대값보다 클 수 없습니다.")
                time.sleep(1)
                warning_min.empty()
            # 최대값이 최소값보다 작으면 경고
            elif max_count < min_count:
                warning_max = st.warning("⚠️ 최대값이 최소값보다 작을 수 없습니다.")
                time.sleep(1)
                warning_max.empty()


        # 체크리스트 생성 (버튼 클릭 -> 과정 실행)
        _, guide_ok = st.columns(2)
        with guide_ok:
            st.markdown("")
            # step 3 이상이면 비활성화 (이미 태그가 생성됨)
            is_disabled = st.session_state.step >= 3
            if st.button(
                "✅ㅤ태그 생성",
                use_container_width=True,
                type="primary",
                disabled=is_disabled,
            ):
                # 최소/최대 검증
                if min_count > max_count:
                    error_min = st.error("❌ 최소값이 최대값보다 클 수 없습니다.")
                    time.sleep(1)
                    error_min.empty()
                elif max_count < min_count:
                    error_max = st.error("❌ 최대값이 최소값보다 작을 수 없습니다.")
                    time.sleep(1)
                    error_max.empty()

                checklist: ChecklistType = {
                    "language": language,
                    "separator": separator,
                    "tag_count_range": {"min": int(min_count), "max": int(max_count)},
                }

                if case_style:
                    checklist["case_style"] = case_style

                try:
                    # 유효성 검사
                    guideline_gen = GuidelineGenerator(checklist)
                    st.session_state.checklist = checklist

                    # 업로드된 파일 확인
                    if not st.session_state.get("uploaded_file"):
                        st.error("⚠️ 마크다운 파일을 업로드해주세요.")
                        return

                    # 태그 생성 프로세스 시작
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # 파일 내용 읽기
                    uploaded_file = st.session_state.uploaded_file
                    md_content = uploaded_file.getvalue().decode("utf-8")
                    filename = uploaded_file.name

                    # 1. 태그 생성
                    status_text.caption("[1/2] 신규 태그 생성 중 ...")
                    progress_bar.progress(30)

                    tag_gen = TagGenerator()

                    new_tags = tag_gen.generate_tags(
                        guideline_gen, md_content, filename
                    )

                    st.session_state.new_tags = new_tags
                    progress_bar.progress(60)

                    # 2. 기존 태그와 비교
                    status_text.caption("[2/2] 기존 태그와 비교 중 ...")
                    comparator = TagComparator()

                    matches = comparator.compare_tags(
                        new_tags, st.session_state.existing_tags
                    )
                    st.session_state.matches = matches

                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()

                    st.session_state.step = 3
                    st.rerun()

                except ValueError as e:
                    error_valueerror = st.error(f"❌ 오류: {e}")
                    time.sleep(1)
                    error_valueerror.empty()
                except Exception as e:
                    st.error(f"❌ 태그 생성 실패: {e}")
                    with st.expander("상세 오류 정보"):
                        st.code(traceback.format_exc())


def render_compare_tags():
    """기존, 신규 태그 결과 시각화"""
    with st.container(border=True):
        st.markdown("#### 📊 태그 비교 결과")

        if not st.session_state.matches:
            return
        matches: list[TagMatch] = st.session_state.matches

        # 통계
        new_count = sum(1 for m in matches if m.is_new)
        matched_count = len(matches) - new_count

        col_new_tags, col_match_tags, col_existing_tags = st.columns(3)
        with col_new_tags:
            st.metric("신규 태그", f"{new_count}개")
        with col_match_tags:
            st.metric("매칭된 태그", f"{matched_count}개")
        with col_existing_tags:
            st.metric("총 태그", f"{len(matches)}개")

        # 상세 결과
        for match in matches:
            if match.is_new:
                st.success(f"신규 : `{match.new_tag}` (유사도: {match.similarity:.2f})")
            else:
                st.info(
                    f"매칭 : `{match.new_tag}`ㅤ→ㅤ`{match.matched_tag}` (유사도: {match.similarity:.2f})"
                )

        # 최종 태그 확인 버튼
        st.text("")
        _, col_final_btn = st.columns(2)
        with col_final_btn:
            if st.button(
                "✨ㅤ최종 태그 제안", type="primary", use_container_width=True
            ):
                st.session_state.step = 4
                st.rerun()

    return matches


def render_final_offer(matches):
    """최종 태그 제안"""
    # 저장 상태 메시지 표시 및 새로고침 버튼
    save_msg_col, *_, reset_btn = st.columns([20, 1, 1, 3])

    with save_msg_col:
        # 저장 결과 메시지 표시
        if st.session_state.get("save_success_msg"):
            st.success(st.session_state.save_success_msg)
            st.session_state.save_success_msg = None
        elif st.session_state.get("save_error_msg"):
            st.error(st.session_state.save_error_msg)
            st.session_state.save_error_msg = None

    with reset_btn:
        if st.button(
            "🔄ㅤ새로고침",
            use_container_width=True,
            help="기존 태그를 수집하는 단계로 돌아갑니다",
        ):
            # 태그 추천 페이지 관련 키들만 삭제
            keys_to_delete = [
                "step",
                "checklist",
                "existing_tags",
                "new_tags",
                "matches",
                "save_success_msg",
                "save_error_msg",
            ]

            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]

            init_session_state()
            st.rerun()

    with st.container(border=True):
        st.markdown("#### ✨ 최종 태그 제안")

        # 정적 메서드로 호출 (인스턴스 생성 불필요)
        final_tags = TagComparator.get_final_tags(matches)

        # YAML frontmatter가 추가된 파일 생성
        uploaded_file = st.session_state.uploaded_file
        original_content = uploaded_file.getvalue().decode("utf-8")
        updated_content = add_yaml_frontmatter(original_content, final_tags)

        # YAML frontmatter 미리보기 (첫 번째 --- 부터 두 번째 --- 까지)
        yaml_match = re.match(r"(---\n.*?\n---)", updated_content, re.DOTALL)
        if yaml_match:
            yaml_preview = yaml_match.group(1)
            st.code(yaml_preview, language="yaml")
        else:
            st.code(updated_content[:200], language="yaml")  # fallback

        # 저장 및 다운로드 버튼
        st.text("")
        *_, download_btn = st.columns(4)

        with download_btn:
            # Vault에 저장 버튼
            vault_path = st.session_state.get("vault_path")
            if vault_path and Path(vault_path).exists():
                if st.button(
                    "💾ㅤVault에 저장", use_container_width=True, type="primary"
                ):
                    try:
                        save_path = Path(vault_path) / uploaded_file.name
                        save_path.write_text(updated_content, encoding="utf-8")
                        st.session_state.save_success_msg = f"✅ 저장 완료: {save_path}"
                        st.rerun()
                    except Exception as e:
                        st.session_state.save_error_msg = f"❌ 저장 실패: {e}"
                        st.rerun()
            else:
                # Vault 경로가 없으면 다운로드 버튼
                st.download_button(
                    label="⬇️ㅤ다운로드",
                    data=updated_content.encode("utf-8"),
                    file_name=uploaded_file.name,
                    mime="text/markdown",
                    use_container_width=True,
                    type="primary",
                )
            st.caption("💡 YAML frontmatter가 추가된 파일을 저장하세요")


def main():
    """메인 함수"""
    # 세션 상태 초기화
    init_session_state()

    # 메인 헤더
    st.title("🏷️ 태그 추천")
    st.caption("노트에 적합한 태그를 Upstage Solar Pro 2로 추천받아 보세요!")
    st.text("")

    # 단계별 렌더링
    # Step 1: 기존 태그 미리보기
    if st.session_state.step == 1:
        vault_path = st.session_state.get("vault_path")
        uploaded_file = st.session_state.get("uploaded_file")

        if vault_path and uploaded_file:
            st.info(
                f"- Vault 경로:ㅤ{vault_path}\n"
                f"- Markdown 파일:ㅤ{uploaded_file.name}\n\n"
                f"**💡 변경이 필요한 경우 왼쪽 사이드바에서 수정해 주세요.**"
            )
            if st.button("기존 태그 분석 시작", type="primary"):
                st.session_state.step = 2
                st.rerun()
        else:
            st.warning(
                "👈ㅤ왼쪽 사이드바에서 ***Vault 경로*** 와 ***Markdown 파일 업로드*** 설정을 완료해 주세요."
            )

    # Step 2-3: 기존 태그 미리보기 + 태그 작성 가이드라인 + 태그 비교 결과
    if st.session_state.step >= 2 and st.session_state.step < 4:
        render_existing_tags_preview()

        col1, col2 = st.columns(2)

        with col1:
            render_checklist_form()

        with col2:
            # Step 3: 태그 비교 결과
            if st.session_state.step >= 3:
                matches = render_compare_tags()

    # Step 4: 최종 추천 태그만 표시
    if st.session_state.step == 4:
        matches = st.session_state.matches
        render_final_offer(matches)


if __name__ == "__main__":
    main()
