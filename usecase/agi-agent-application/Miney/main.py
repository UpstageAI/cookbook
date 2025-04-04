import streamlit as st
import base64
from io import BytesIO
from PyPDF2 import PdfReader
from streamlit_lottie import st_lottie
import requests
from upstage import extract_text_with_upstage, mask_personal_info, chat_with_openai, parse_to_json
import tempfile
from risk_assessor import LegalRiskAssessor
from answer import get_legal_advice
from PIL import Image

json_result = None
# 세션 상태 초기화
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "rental_type" not in st.session_state:
    st.session_state.rental_type = None

st.set_page_config(page_title="M$ney.", layout="wide")


# ----- PDF 뷰어 함수 -----
def show_pdf(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

def load_lottie_url(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except Exception:
        return None


lottie_url = "https://lottie.host/21891569-1b6f-44bb-9eda-36b302ebb906/fGMM009Fec.json"
lottie_ani = load_lottie_url(lottie_url)


# ----- 페이지 라우팅 -----

# ----- 랜딩 페이지 -----
if st.session_state.page == "landing":
    # 배경색 및 스타일 적용
    st.markdown("""
    <style>
                
    @font-face {
    font-family: 'MaruBuriBold';
    src: url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.eot);
    src: url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.eot?#iefix) format("embedded-opentype"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.woff2) format("woff2"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.woff) format("woff"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.ttf) format("truetype");
}
                
    @font-face {
    font-family: 'MaruBuri';
    src: url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Regular.eot);
    src: url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Regular.eot?#iefix) format("embedded-opentype"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Regular.woff2) format("woff2"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Regular.woff) format("woff"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Regular.ttf) format("truetype");
}

html, body, div, span, input, label, textarea, button, section, article, aside, header, footer, p, * {
            font-family: 'MaruBuri', sans-serif !important;
        }
.mango-title {
    font-family: 'MaruBuriBold' !important;
    font-size: 52px;
    color: #4285F4;
    text-align: center;
    margin-bottom: 20px;
    line-height: 1.4;
}
                
    .mango-title .dot {
    color: #FF9BD2; 
}
                
    html, body, .stApp, .main, .block-container {
        background-color: #FFF !important;
    }
    
   
    .subtitle {
        font-family: 'MaruBuri' !important;
        font-size: 20px;
        font-weight: 500;
        color: #111;
        text-align: center
    }
                
    .subcatch {
        font-family: 'MaruBuri' !important;
        font-size: 16px;
        font-weight: 500;
        color: #111;
        text-align: center
    }
                
    .catchline {
        font-family: 'MaruBuri' !important;
        font-size: 16px;
        font-weight: 500;
        color: #686D76;
        text-align: center
    }
    
    div.stButton > button {
    font-family: 'MaruBuri' !important;
    background-color:#3D3B40;
    color: white;
    padding: 20px 30px;
    font-size: 30px;
    font-weight: bold;
    border-radius: 4px;
    border: none;
    margin-bottom: 10px;
    width: 80%;
}
div.stButton > button:hover {
    font-family: 'MaruBuri' !important;
    background-color: #FF9BD2;
    color: #3D3B40;            
    opacity: 0.8;
}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
<hr style="border: 3px solid #000; margin: 20px 0;">
""", unsafe_allow_html=True)
    
    # 두 개의 컬럼 구성 (좌: 소개 / 우: 버튼)
    left, right = st.columns([3, 2])
    
    # 왼쪽 소개
    with left:
        if lottie_ani:
            st_lottie(lottie_ani, height=200, key="landing_lottie")
        else:
            st.markdown("""
            <div style='font-size: 80px; text-align: center;'>
                🤑
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<h1 class="mango-title">  M$ney<span class="dot">.</span></h1>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">보증금, 더는 혼자 싸우지 마세요!</div>', unsafe_allow_html=True)
        st.markdown('<div class="subcatch">나만의 보증금 AI 지킴이: M$ney</div>', unsafe_allow_html=True)
        st.markdown('<div class="catchline">  </div>', unsafe_allow_html=True)
        st.markdown('<div class="catchline">M$ney가 처음이라면 정확한 분석을 위해 튜토리얼을 확인해주세요!</div>', unsafe_allow_html=True)
    
    # 오른쪽 버튼 - HTML 버튼 태그 사용
    with right:
        st.markdown("""
        <div style="border: 2px solid #FFF; padding: 50px; border-radius: 10px;">
        </div>
        """, unsafe_allow_html=True)
        if st.button("튜토리얼 보기"):
            st.session_state.page = "tutorial"
            st.rerun()
        if st.button("내 돈 돌려받기"):
            st.session_state.page = "ai"
            st.rerun()


# ----- 튜토리얼 페이지 -----
elif st.session_state.page == "tutorial":
    st.markdown("""
        <style>
        
        @font-face {
        font-family: 'MaruBuriBold';
        src: url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.eot);
        src: url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.eot?#iefix) format("embedded-opentype"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.woff2) format("woff2"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.woff) format("woff"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.ttf) format("truetype");
    }
                
        html, body, div, span, input, label, textarea, button, section, article, aside, header, footer, p, h1, h2, h3, h4, h5, h6, * {
            font-family: 'MaruBuri', sans-serif !important;
        }
        
        html, body, .stApp, .main, .block-container {
        background-color: #FAE7F3 !important;
    }
                
        .orange-header {
            font-family:'MaruBuriBold',sans-serif !important;
            font-size:35px;
            color: #3D3B40;
            margin-bottom: 10px;
        }
        
        .orange-header .dot {
        color: #FF9BD2; 
    }

        div.stButton > button {
            font-family: 'MaruBuri', sans-serif !important;
            background-color:#3D3B40;
            color: white;
            border: none;
            padding: 0.6em 1.3em;
            border-radius: 5px;
            transition: background-color 0.3s ease;
            font-size: 16px;
            display: flex; 
            justify-content: center;
        }

        div.stButton > button:hover {
            font-family: 'MaruBuri', sans-serif !important;
            background-color: #FF9BD2;
            color: #3D3B40;            
            opacity: 0.8;
        }
                
        .sentence {
            font-family:'MaruBuriBold',sans-serif !important;
            font-size:16px;
            color: #3D3B40;
            margin-bottom: 10px;
        }

        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="orange-header">M$ney<span class="dot">.</span> 사용설명서</div>', unsafe_allow_html=True)
        image_paths = ["tutorial1.png", "tutorial2.png", "tutorial3.png"]

        # 이미지 출력
        for path in image_paths:
            image = Image.open(path)
            st.image(image, use_container_width=True)

    
    with col2:    
        st.markdown("""
        </br></br></br></br>
        <div class="sentence"> ⚠️ 이 웹사이트는 light 모드로 봐주세요! ⚠️</div>  
        <div class="sentence" style="background-color:#fff; padding:20px; border-radius:10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px;">
            1. 임대차 계약서의 첫 페이지를 업로드해 주세요. (반드시 PDF 파일이어야 합니다!)
        </div>
        <div class="sentence" style="background-color:#fff; padding:20px; border-radius:10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px;">
            2. M$ney가 읽어온 계약서를 확인 후 M$ney 에게 계약서 내용을 전달해 주세요. 수정이 가능합니다!
        </div>
         <div class="sentence" style="background-color:#fff; padding:20px; border-radius:10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px;">
            3. 임대차 계약 전문가 M$ney가 계약서를 분석하고, 불리하거나 주의해야 할 조항을 꼼꼼히 확인해줘요.
        </div>
        <div class="sentence" style="background-color:#fff; padding:20px; border-radius:10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px;">
            4. 더 정확한 조언을 받으려면, 상황을 구체적으로 설명해 주세요. M$ney가 관련 판례를 바탕으로 취해야 할 조치를 제안해드립니다.
        </div>
        <div class="sentence" style="background-color:#fff; padding:20px; border-radius:10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px;">
            5. 궁금한 점이 생기셨다면, 언제든 M$ney에게 질문해 보세요! 세심한 AI 분석을 바탕으로 정확한 답변을 드릴게요.
        </div>
        </br></br></br>
        """, unsafe_allow_html=True)

        col_left, col_center, col_right = st.columns([1, 1, 1])

        with col_center:
            if st.button("M$ney 사용하기"):
                st.session_state.page = "ai"
                st.rerun()

# ----- AI 분석 페이지 -----
elif st.session_state.page == "ai":
    st.markdown("""
        <style>
        
        @font-face {
        font-family: 'MaruBuriBold';
        src: url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.eot);
        src: url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.eot?#iefix) format("embedded-opentype"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.woff2) format("woff2"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.woff) format("woff"), url(https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Bold.ttf) format("truetype");
    }
                
        html, body, div, span, input, label, button, section, article, aside, header, footer, p, h1, h2, h3, h4, h5, h6, * {
            font-family: 'MaruBuri', sans-serif !important;
        }
                
        textarea {
            background-color: #FAE7F3 !important;  /* 연분홍 배경 */
            color: #3D3B40 !important;             /* 텍스트 색상 */
            font-family: 'MaruBuri', sans-serif !important;
            font-size: 16px !important;
            border-radius: 10px !important;
            padding: 1rem !important;
        }
               
        .orange-header {
            font-family:'MaruBuriBold',sans-serif !important;
            font-size:35px;
            color: #3D3B40;
            margin-bottom: 10px;
        }
        
        .orange-header .dot {
        color: #FF9BD2; 
    }

        div.stButton > button {
            font-family: 'MaruBuri', sans-serif !important;
            background-color:#3D3B40;
            color: white;
            border: none;
            padding: 0.6em 1.3em;
            border-radius: 5px;
            transition: background-color 0.3s ease;
            font-size: 16px;
        }

        div.stButton > button:hover {
            font-family: 'MaruBuri', sans-serif !important;
            background-color: #FF9BD2;
            color: #3D3B40;            
            opacity: 0.8;
        }
        
         .subheader {
            font-family:'MaruBuriBold',sans-serif !important;
            font-size:20px;
            color: #3D3B40;
            margin-bottom: 10px;
        }
                
        .sentences {
            font-family:'MaruBuriBold',sans-serif !important;
            font-size:16px;
            color: #3D3B40;
            margin-bottom: 10px;
        }

        details.guide-box {
            background-color:#FAE7F3;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #FFB74D;
            margin-bottom: 20px;
            width: 80%;
            margin-left: auto;
            margin-right: auto;
            font-size: 16px;
        }
        summary {
            font-weight: bold;
            cursor: pointer;
            color: #E65100;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])  

    with col1:
        st.markdown('<h1 class="orange-header">M$ney<span class="dot">.</span></h1>', unsafe_allow_html=True)

    with col2:
        st.markdown(" ")
        if st.button("튜토리얼로 돌아가기"): 
            st.session_state.page = "tutorial"
            st.rerun()


    col1, col2 = st.columns(2)

    # ==== Prompt: 양식 정리 ====
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

    with col1:
        st.markdown('<div class="subheader">계약서를 업로드해 주세요</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(label="계약서를 AI가 분석해드리며, 불리한 조항이 있는지 확인합니다.", type=["pdf"])

        if uploaded_file:
            file_bytes = uploaded_file.read()
            file_stream = BytesIO(file_bytes)            

    with col2:
        if uploaded_file:
            st.markdown('<div class="subheader">M$ney의 계약서 주요 정보 요약</div>', unsafe_allow_html=True)
            # OCR 및 AI 처리 수행 (캐싱을 통해 여러 번 반복 방지)
            if "raw_text" not in st.session_state:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                with st.spinner("🔍 OCR로 텍스트 추출 중..."):
                    st.session_state.raw_text = extract_text_with_upstage(tmp_path)

            raw_text = st.session_state.raw_text
            masked_text = mask_personal_info(raw_text)

            if raw_text:
                if "formatted_text" not in st.session_state:
                    with st.spinner("📑 적절한 양식으로 변환 중..."):
                        st.session_state.formatted_text = chat_with_openai(FORMAT_PROMPT, masked_text)

                if st.session_state.formatted_text:
                    st.markdown('<div class="sentences">계약서를 읽어왔습니다</div>', unsafe_allow_html=True)
                    # 사용자가 수정할 수 있는 텍스트 영역
                    edited_text = st.text_area("검토 후 오타가 있으면 수정해주세요", value=st.session_state.formatted_text, height=350)
                    
                    # 사용자가 텍스트를 수정하면 세션 상태 업데이트
                    if edited_text != st.session_state.formatted_text:
                        st.session_state.formatted_text = edited_text

                    if st.button("M$ney ai에 계약서 전달하기"):
                        st.session_state.json_result = parse_to_json(st.session_state.formatted_text)
                        json_result = st.session_state.json_result
                        if json_result:

                            # 위험도 평가 실행
                            from risk_assessor import LegalRiskAssessor
                            risk_assessor = LegalRiskAssessor()
                            result = risk_assessor.assess_contract(json_result)
                                    # 세션에 저장!
                            st.session_state.contract_data = result["contract_data"]
                            st.session_state.categorized_clauses = result["categorized_clauses"]
                            st.session_state.analysis_done = True

                            categorized = result["categorized_clauses"]

                            # 분석 결과가 있을 때 항상 표시
                            if "categorized_clauses" in st.session_state:
                                categorized = st.session_state.categorized_clauses

                                if categorized["불리"]:
                                    st.markdown("### ❗ 불리한 조항", unsafe_allow_html=True)
                                    for clause in categorized["불리"]:
                                        title = clause.get("조항", "📌 특약사항")
                                        content = clause["내용"]
                                        st.markdown(f"""
                                        <div style="background-color: #ffe6e6; padding: 10px 15px; border-left: 6px solid #ff4d4d; margin: 10px 0; border-radius: 5px;">
                                        <strong>{title}</strong><br>{content}
                                        </div>
                                        """, unsafe_allow_html=True)

                                if categorized["주의"]:
                                    st.markdown("### ⚠️ 주의가 필요한 조항", unsafe_allow_html=True)
                                    for clause in categorized["주의"]:
                                        title = clause.get("조항", "📌 특약사항")
                                        content = clause["내용"]
                                        st.markdown(f"""
                                        <div style="background-color: #fff5e6; padding: 10px 15px; border-left: 6px solid #ffa31a; margin: 10px 0; border-radius: 5px;">
                                        <strong>{title}</strong><br>{content}
                                        </div>
                                        """, unsafe_allow_html=True)

                else:
                    st.error("❌ 양식 정리에 실패했습니다.")
            else:
                st.error("❌ OCR 처리에 실패했습니다.")

    
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="subheader">어떤 문제가 있으신가요?</div>', unsafe_allow_html=True)
        user_situation = st.text_area(
            "여러분의 든든한 법률 파트너가 되어 드릴게요! 상황을 자세히 설명해주세요.",
            placeholder="퇴실했는데, 집주인이 벽지 더러워졌다고 200만원을 공제하고 300만원만 주려 합니다."
        )

        if st.button("M$ney에게 지금 상황을 전달했어요"):
            if not user_situation.strip():
                st.warning("상황을 입력해 주세요!")
            elif "contract_data" not in st.session_state:
                st.warning("계약서를 먼저 분석하고 M$ney에 전달해 주세요.")
            elif not uploaded_file:
                st.warning("먼저 계약서를 업로드해 주세요.")
            else:
                # AI 호출 예시
                legal_advice = response = get_legal_advice(user_situation, st.session_state.json_result, 0)
                st.session_state.legal_advice = legal_advice


    with col2:
        if 'legal_advice' in st.session_state and st.session_state.legal_advice:
            st.markdown('<div class="subheader">🚨 판례를 바탕으로 취해야 할 행동을 조언드립니다.</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="subtle-box">
            {st.session_state.legal_advice}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("왼쪽에 반드시 상황을 입력하고 버튼을 눌러주세요!")



    st.markdown("---")

    if "question_history" not in st.session_state:
        st.session_state.question_history = []

    # ai_prompt가 존재할 때만 표시
    if 'ai_prompt' in st.session_state and st.session_state.ai_prompt:
        st.markdown('<div class="subheader">M$ney의 분석 결과</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtle-box">', unsafe_allow_html=True)
        st.markdown(st.session_state.ai_prompt)
        st.markdown('</div>', unsafe_allow_html=True)

    # 질문 입력창
    st.markdown('<div class="subheader">M$ney에서 궁금한 점을 질문해주세요.</div>', unsafe_allow_html=True)
    user_prompt = st.text_area("M$ney가 정확한 답변을 드릴게요!", placeholder="예: 계약기간을 채우지 못했어요...")

    # 질문 버튼 클릭 시 처리
    if st.button("질문하기"):
        if not uploaded_file:
            st.warning("먼저 계약서를 업로드해 주세요.")
        elif "contract_data" not in st.session_state:
            st.warning("계약서를 먼저 분석하고 M$ney에 전달해 주세요.")
        elif not user_prompt.strip():
            st.warning("질문을 입력해 주세요.")
        elif len(st.session_state.question_history) >= 10:
            st.error("⚠️ 무료 사용자는 질문을 최대 10개까지 할 수 있어요.\n더 많은 질문을 원하시면 M$ney Pro를 이용해 주세요! 새로고침 시 홈화면으로 이동합니다.")

        else:
            json_result = st.session_state.json_result
            response = get_legal_advice(user_prompt, json_result, 1)
            qa = f"**Q. {user_prompt}**\n\n{response}"
            st.session_state.ai_prompt = qa
            st.session_state.question_history.append({"question": user_prompt, "answer": response})
            st.rerun()

    if st.session_state.question_history:
        st.markdown("---")
        st.markdown('<div class="subheader">이전 질문 보기</div>', unsafe_allow_html=True)
        for i, item in enumerate(st.session_state.question_history):
            with st.expander(f"Q{i+1}: {item['question']}"):
                st.markdown(f"**Q. {item['question']}**")
                st.markdown(item['answer'])


    
