import streamlit as st
import requests
import openai
import os
import tempfile
import re
import json
from dotenv import load_dotenv

# 환경 변수 로딩
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
openai.api_key = OPENAI_API_KEY

# ==== 개인정보 마스킹 함수 ====
def mask_personal_info(text: str) -> str:
    text = re.sub(r'\b\d{6}[-]?\d{7}\b', '******-*******', text)
    text = re.sub(r'010[-\s]?\d{4}[-\s]?\d{4}', '010-****-****', text)
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[이메일]', text)
    text = re.sub(r'(지정계좌|계좌번호)\s*[:：]?\s*[^\n]+', '지정계좌: [계좌정보]', text)
    text = re.sub(r'(임대인\s*주\s*소|임차인\s*주\s*소|주소\s*[:：])[^\n\r]{5,40}', '[주소]', text)

    return text

# ==== Prompt 1: 오타/줄바꿈 정리 ====
# 이 프롬프트는 더 이상 사용하지 않습니다
# FIX_PROMPT = """OCR로 추출된 계약서 텍스트를 정리해줘. 줄바꿈, 띄어쓰기, 오타만 수정하고, 조항의 의미나 순서는 바꾸지 마.

# [예시]
# 입력: 제2조[존속기간]임대인은 위부동산을임대차목적대로 사용할수있도록 한다
# 출력: 제2조 [존속기간] 임대인은 위 부동산을 임대차 목적대로 사용할 수 있도록 한다.

# 입력: """

# ==== Prompt 2: 양식 정리 ====

FORMAT_PROMPT = """계약서를 아래 양식으로 정리해줘. JSON 변환을 위한 형식이므로 정확히 따라줘. 반드시 텍스트 형식으로 출력하고, JSON 형식으로 출력하지 마.

[주의사항]
1. 입력된 계약서의 모든 조항을 반드시 포함해야 합니다. 누락하면 안 됩니다.
2. 제1조가 보증금/차임 관련 내용이면 계약 항목에서 제외하고, 제2조부터 시작합니다.
3. 문장의 어미는 반드시 '~다.' 체로 통일하고, '~합니다', '~됩니다' 등의 정중한 말투는 사용하지 마세요.
4. 계약 부분에서 각 조항 뒤에 반드시 콜론(:)을 붙여주세요. 예: "제2조 [존속기간]: 내용"
5. 특약사항이 없는 경우에도 "특약사항:" 항목은 반드시 포함하고 "- 없음"으로 표시해주세요.

[출력 형식]
구분: [월세/전세]
보증금: [금액]원
차임: [금액]원

계약:
[모든 계약 조항을 순서대로 나열]

특약사항:
[특약사항 목록 또는 "- 없음"]

[예시 입력]
부동산(원룸) 월세 계약서

임대인과 임차인 쌍방은 아래 표시 부동산에 관하여 다음 계약 내용과 같이 임대차계약을 체결한다.

1. 부동산의 표시
소재지 서울특별시 마포구 서교동 448-28 301호
토지 목적 연적 148.8 m2
건물 구조 철근콘크리트구조 용도 다가구주택 연적 304.17 m2
임대할 부분 301호 면적 20 m2

2. 계약내용
제1조 [목적] 위 부동산의 임대차에 한하여 임대인과 임차인은 합의에 의하여 임차보증금 및 차임을 아래와 같이 지급하기로 한다.
보증금 금액 일천만원정 (₩10,000,000)
계약금 금액 일백만원정은 계약시에 지급하고 영수함. ※영수자 (인)
잔금 금액 구백만원정 온 2025년 02월 22일에 지급한다.
차임금 육십만원정은 매월 22일(후불) 지급한다.

제2조 [존속기간] 임대인은 위 부동산을 임대차 목적대로 사용할 수 있는 상태로 2025년 02월 22일까지 임차인에게 인도하며, 임대차 기간은 인도일로부터 2027년 02월 21일(24개월)까지로 한다.

제3조 [용도변경 및 전대 등] 임차인은 임대인의 동의 없이 위 부동산의 용도나 구조를 변경하거나 전대, 임차권 양도 또는 담보제공을 하지 못하며 임대차 목적 이외의 용도로 사용할 수 없다.

[예시 출력]
구분: 월세
보증금: 10,000,000원
차임: 600,000원

계약:
제2조 [존속기간]: 임대인은 위 부동산을 임대차 목적대로 사용할 수 있는 상태로 2025년 02월 22일까지 임차인에게 인도하며, 임대차 기간은 인도일로부터 2027년 02월 21일(24개월)까지로 한다.

제3조 [용도변경 및 전대 등]: 임차인은 임대인의 동의 없이 위 부동산의 용도나 구조를 변경하거나 전대, 임차권 양도 또는 담보제공을 하지 못하며 임대차 목적 이외의 용도로 사용할 수 없다.

특약사항:
- 없음

입력: """

# ==== OCR 요청 함수 ====
def extract_text_with_upstage(file_path):
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    mime = "application/pdf" if file_path.endswith(".pdf") else "image/jpeg"

    files = {
        "document": (os.path.basename(file_path), open(file_path, "rb"), mime),
        "model": (None, "ocr")
    }

    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        return None

# ==== OpenAI 호출 함수 ====
def chat_with_openai(prompt, user_input):
    try:
        messages = [
            {"role": "system", "content": "너는 계약서 전문가야."},
            {"role": "user", "content": prompt + user_input}
        ]
        res = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI 호출 오류: {e}")
        return None

# ==== JSON 파싱 함수 ====
def parse_to_json(text):
    try:
        result = {
            "구분": re.search(r"구분: (.+)", text).group(1).strip(),
            "보증금": re.search(r"보증금: (.+)", text).group(1).strip(),
            "차임": re.search(r"차임: (.+)", text).group(1).strip(),
            "계약": [
                {
                    "조항": m.group(1).strip(),
                    "내용": m.group(2).strip()
                }
                for m in re.finditer(r"(제\d+조 \[[^\]]+\]): (.+)", text)
                if not "제1조" in m.group(1)
            ],
            "특약사항": re.findall(r"- (.+)", text.split("특약사항:")[-1])
        }
        return result
    except Exception as e:
        st.error("JSON 변환 중 오류 발생: " + str(e))
        return None

# ==== Streamlit 앱 ====
#st.set_page_config(page_title="계약서 OCR + 정리기", layout="centered")
#st.title("📄 임대차 계약서 OCR + 정리 + 양식 변환")

"""uploaded_file = st.file_uploader("📤 계약서 파일 업로드 (PDF 등)", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    if "raw_text" not in st.session_state:
        with st.spinner("🔍 OCR로 텍스트 추출 중..."):
            st.session_state.raw_text = extract_text_with_upstage(tmp_path)

    raw_text = st.session_state.raw_text

    if raw_text:
        st.subheader("🪼 OCR 결과 원문")
        st.text_area("OCR 결과", raw_text, height=250)

        masked_text = mask_personal_info(raw_text)

        st.subheader("🐙 개인정보 마스킹된 버전")
        st.text_area("보안을 위해 개인정보는 마스킹된다던가...암튼 한 마디라도 더 하려고 만들어봤엉", masked_text, height=250)

        # 양식 정리 결과를 세션 상태에 저장
        if "formatted_text" not in st.session_state:
            with st.spinner("🧱 적절한 양식으로 변환 중..."):
                st.session_state.formatted_text = chat_with_openai(FORMAT_PROMPT, masked_text)

        if st.session_state.formatted_text:
            st.subheader("🦧 양식 정리본 (최종본)")
            # 사용자가 수정할 수 있는 텍스트 영역
            edited_text = st.text_area("최종 결과 (사용자가 오타 수정 가능)", value=st.session_state.formatted_text, height=350)
            
            # 사용자가 텍스트를 수정하면 세션 상태 업데이트
            if edited_text != st.session_state.formatted_text:
                st.session_state.formatted_text = edited_text

            if st.button("📩 계약서 저장 (JSON 변환)"):
                json_result = parse_to_json(st.session_state.formatted_text)
                if json_result:
                    st.subheader("🐠 JSON 변환 결과")
                    st.json(json_result)
        else:
            st.error("❌ 양식 정리에 실패했습니다.")
    else:
        st.error("❌ OCR 처리에 실패했습니다.")"""
