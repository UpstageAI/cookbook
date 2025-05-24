import streamlit as st
from uuid import uuid4
import logging, logging.handlers, os, json, pathlib

from housing_alert.services import db, ai

import logging
import logging.handlers
import os

# ─────────── 로깅 설정 (파일 + 콘솔) ───────────
LOG_FILE = "/var/log/hackathon_app.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
        ),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("hackerton_app")

# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Housing Alert",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------ Query params ----------------
params = st.query_params
uid = params.get("user_id", None)
nid = params.get("id", None)
# ------------------------------------------------

# 전국 시·군·구 사전 예시 ─ 실제 서비스에선 S3·로컬 JSON 로드 권장
# provinces = {"서울특별시": ["강남구","강동구",...], "경기도": ["수원시","성남시",...], ...}
import json, pathlib

provinces = json.loads(
    pathlib.Path("korea_regions.json").read_text()
)  # 17개 시·도 · 250여 시·군·구
# print(provinces)
# =================================================
# 1) 등록 페이지
# =================================================
if not (uid and nid):

    st.title("🏠 청년 주택청약 알림 – 사용자 등록")
    st.caption("★ 는 필수 입력")

    # ---------- ① 기본 정보 ----------
    with st.expander("① 기본 정보", expanded=True):
        colA, colB = st.columns(2)
        with colA:
            email = st.text_input("★ 이메일", placeholder="you@example.com")
            birth = st.date_input("★ 생년월일")
            is_student = st.checkbox("재학 여부")

        with colB:
            gender = st.selectbox("성별 (선택)", ["미선택", "남성", "여성", "기타"])
            family_size = st.number_input("세대 구성원 수", 1, 10, step=1)

    # ---------- ② 경제 정보 ----------
    with st.expander("② 경제 정보"):
        income = st.number_input("월 소득(만원) (세전)", 0, step=100)
        total_assets = st.number_input("총 자산(만원)", 0, step=100)
        own_house = st.radio("주택 보유", ["무주택", "자가 보유"], horizontal=True)
        own_car = st.checkbox("자가용 보유")
        # car_value     = st.number_input("차량 가액(만원)", 0, step=100, disabled=not own_car)
        saving_count = st.number_input("청약통장 납입 횟수", 0, step=1)

    # ---------- ③ 거주·선호 ----------
    with st.expander("③ 거주·선호"):
        residence = st.text_input("현재 거주지 (시/도)")
        preferred_area = st.number_input(
            "선호 전용면적(㎡)", 0.0, step=1.0, format="%.1f"
        )

        st.markdown("##### 💰 예산")
        colJ, colR = st.columns(2)
        with colJ:
            budget_deposit = st.number_input("보증금(만원)", 0, step=100)
        with colR:
            budget_monthly = st.number_input("월세 예산(만원)", 0, step=5)

        # near_subway = st.checkbox("역세권(도보 10분)")

    # ---------- ④ 편의시설 ----------
    # with st.expander("④ 근처 편의시설(선택)"):
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         has_gym  = st.checkbox("헬스장")
    #         has_park = st.checkbox("공원")
    #     with col2:
    #         has_er   = st.checkbox("응급실")
    #         has_mart = st.checkbox("대형마트")

    # ---------- ⑤ 선호 지역(복수 선택) ----------
    with st.expander("④ 선호 지역(복수 선택)", expanded=False):
        import json, pathlib

        regions_path = pathlib.Path("korea_regions.json")  # ← JSON 경로
        provinces_all = json.loads(regions_path.read_text(encoding="utf-8"))

        # Check if provinces_all is a dictionary or a list
        if isinstance(provinces_all, dict):
            # If it's a dictionary, use the grouping logic:
            selected_provinces = st.multiselect(
                "선호 시/도 선택 (다중)",
                list(provinces_all.keys()),
                placeholder="예: 서울특별시, 경기도 …",
            )

            preferred_regions = {}
            if selected_provinces:
                st.markdown("##### 세부 시·군·구 선택")
                for p in selected_provinces:
                    sub_opts = provinces_all[p]["direct"].copy()
                    # Include detailed options from city sub-groups, if any:
                    for city, gu_list in provinces_all[p]["city"].items():
                        sub_opts.extend([f"{city} {g}" for g in gu_list])

                    chosen = st.multiselect(f"  {p}", sub_opts, key=f"ms_{p}")
                    preferred_regions[p] = chosen
        else:
            # If provinces_all is a list, simply use a multiselect with the list
            preferred_regions = st.multiselect(
                "선호 지역 선택 (다중)",
                provinces_all,
                placeholder="예: 강릉시, 거제시, …",
            )
    # ---------- 저장 ----------
    if st.button("저장", type="primary"):
        if not email:
            st.error("이메일은 필수입니다.")
            st.stop()
        if not birth:
            st.error("생년월일은 필수입니다.")
            st.stop()
        


        # Normalize preferred regions: remove the trailing "시" if present.
        if isinstance(preferred_regions, dict):
            normalized_preferred_regions = {}
            for prov, region_list in preferred_regions.items():
                normalized_preferred_regions[prov] = [
                    r[:-1] if r.endswith("시") else r for r in region_list
                ]
        else:
            normalized_preferred_regions = [
                r[:-1] if r.endswith("시") else r for r in preferred_regions
            ]

        # print(normalized_preferred_regions)
        uid = str(uuid4())
        db.save_user(
            {
                "user_id": uid,
                "email": email,
                "birth": birth.isoformat(),
                "gender": gender if gender != "미선택" else None,
                "is_student": is_student,
                # 경제
                "monthly_income": int(income)*10000,
                "total_assets": int(total_assets)*10000,
                "own_house": own_house,
                "own_car": own_car,
                # "car_value": int(car_value) if own_car else None,
                "saving_count": int(saving_count),
                # 거주·선호
                "residence": residence,
                "preferred_area": int(preferred_area),
                "max_deposit": int(budget_deposit)*10000,
                "budget_monthly": int(budget_monthly)*10000,
                "family_size": int(family_size),
                # "near_subway": near_subway,
                # 편의시설
                # "facility_gym": has_gym,
                # "facility_park": has_park,
                # "facility_er": has_er,
                # "facility_mart": has_mart,
                # 선호 지역
                "preferred_regions": set(normalized_preferred_regions),
            }
        )
        st.success(f"✅ 저장 완료! User ID: {uid}")
        st.stop()

# =================================================
# 2) Q&A 페이지
# =================================================
else:
    user = db.get_user(uid)
    notice = db.get_notice(nid)
    
    if not user:
        log.warning("User not found  uid=%s", uid)
    if not notice:
        log.warning("Notice not found  nid=%s", nid)

    if not (user and notice):
        st.error("사용자 또는 공고 정보를 찾을 수 없습니다.")
        st.stop()

    st.title(f"🏠 {notice.get('notice_name','청약 공고')} – Q&A")

    # if notice.get("notice_s3"):
    #     url = storage.create_presigned_url(notice["notice_s3"])
    #     st.markdown(f"[📄 PDF 다운로드]({url})")

    if notice.get("notice_url"):
        st.markdown(f"[🌐 공고 보기]({notice['notice_url']})")

    st.divider()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    q = st.chat_input("공고에 대해 질문해 보세요…")
    if q:
        st.session_state.messages.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
            
            
        if "rental_conditions" in notice:
            for condition in notice["rental_conditions"]:
                if isinstance(condition, dict) and "net_leasable_area" in condition:
                    condition.pop("net_leasable_area", None)

        print(notice)

        # 이후 bedrock_chat을 호출
        a = ai.bedrock_chat(q, user, notice)

        # a = ai.bedrock_chat(q, user, notice)

        st.session_state.messages.append({"role": "assistant", "content": a})
        with st.chat_message("assistant"):
            st.markdown(a)
