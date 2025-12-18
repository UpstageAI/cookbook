"""
연관 노트 추천 Streamlit 앱
"""

import sys
from pathlib import Path
import streamlit as st

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.related_note import Related_Note


@st.cache_resource
def get_engine(vault_path: str):
    """엔진 인스턴스를 캐싱하여 재사용 (Chroma DB 연결 충돌 방지)"""
    return Related_Note(vault_path=vault_path)


def init_session_state():
    """세션 상태 초기화"""
    if "show_input" not in st.session_state:
        st.session_state.show_input = False


def render_embedding_section(engine):
    """임베딩 섹션 렌더링"""
    notes_to_embed = engine.get_unembedded_notes()

    st.warning("🌀 아직 임베딩되지 않은 노트가 있습니다.")
    st.write(f"총 {len(notes_to_embed)}개 노트가 임베딩 대상입니다:")

    with st.expander("📄 임베딩 대상 노트 목록 보기"):
        for note in notes_to_embed:
            st.text(f"- {note}")

    if st.button("임베딩 시작하기 🚀"):
        with st.spinner("노트 임베딩 중입니다... 시간이 조금 걸릴 수 있습니다."):
            engine.index_unembedded_notes()

        st.success("✅ 임베딩이 완료되었습니다!")
        st.balloons()
        st.rerun()


def render_recommendation_section(engine):
    """추천 섹션 렌더링"""
    st.success("🎉 모든 노트가 이미 임베딩되었습니다!")
    st.write("바로 추천 노트를 생성할 수 있습니다.")

    # 단계별 UI
    if not st.session_state.show_input:
        # STEP 1: 노트 경로 입력 버튼
        if st.button("노트 경로 입력", type="primary"):
            st.session_state.show_input = True
            st.rerun()
    else:
        # STEP 2: 텍스트 입력 및 추천 결과
        target_note = st.text_input(
            "추천을 받을 노트 경로를 입력 후 Enter를 눌러주세요.",
            key="target_note_input",
            value=st.session_state.get("last_target_note", ""),
        )

        if target_note:
            # 추천 결과가 세션에 없으면 새로 생성
            if (
                "related_results" not in st.session_state
                or st.session_state.get("last_target_note") != target_note
            ):
                with st.spinner("연관 노트를 찾는 중입니다..."):
                    related = engine.append_related_links(target_note, k=3)
                    st.session_state.related_results = related
                    st.session_state.last_target_note = target_note

        # 추천 결과가 있으면 표시 (입력 여부와 무관)
        if "related_results" in st.session_state and st.session_state.related_results:
            related = st.session_state.related_results

            st.subheader("🔗 추천 노트 3개")
            for r in related:
                st.markdown(r)

            # 새로고침 버튼
            st.text("")
            *_, reset_btn = st.columns([5, 1])
            with reset_btn:
                if st.button(
                    "🔄ㅤ새로고침",
                    use_container_width=True,
                    help="처음 단계로 돌아갑니다",
                ):
                    # 연관 노트 페이지 관련 키 초기화
                    st.session_state.show_input = False
                    keys_to_delete = [
                        "target_note_input",
                        "related_results",
                        "last_target_note",
                    ]
                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        elif target_note:
            st.info("연관된 노트를 찾지 못했습니다.")


def main():
    """메인 함수"""
    # 세션 상태 초기화
    init_session_state()

    # 메인 헤더
    st.title("📝 연관 노트 추천")
    st.caption("업로드한 노트와 관련성 높은 내용을 가진 노트들을 추천받아 보세요!")
    st.text("")

    # Vault 경로 확인
    vault_path = st.session_state.get("vault_path", "")

    if not vault_path:
        st.warning("👈 왼쪽 사이드바에서 ***Vault 경로*** 를 입력해주세요.")
        st.stop()

    # 경로 유효성 검사
    vault_dir = Path(vault_path)
    if not vault_dir.exists() or not vault_dir.is_dir():
        st.error(f"❌ 유효하지 않은 경로입니다: {vault_path}")
        st.stop()

    # 엔진 초기화 (캐싱됨)
    try:
        engine = get_engine(vault_path=vault_path)
        st.success(
            f"""✅ Vault 연결 완료: {vault_path}

(Vault 경로의 변경이 필요한 경우 왼쪽 사이드바에서 수정해 주세요.)"""
        )
    except Exception as e:
        st.error(f"❌ 엔진 초기화 실패: {e}")
        st.stop()

    # 임베딩 안 된 노트 확인
    notes_to_embed = engine.get_unembedded_notes()

    if not notes_to_embed:
        # 모든 노트가 임베딩된 경우: 추천 섹션
        render_recommendation_section(engine)
    else:
        # 임베딩 안 된 노트가 있는 경우: 임베딩 섹션
        render_embedding_section(engine)


if __name__ == "__main__":
    main()
