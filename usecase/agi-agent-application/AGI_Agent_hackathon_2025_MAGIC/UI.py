import streamlit as st
import streamlit.components.v1 as components
from streamlit_pdf_viewer import pdf_viewer
from streamlit_geolocation import streamlit_geolocation
from main import *
import os
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
import pandas as pd
import threading, queue, time, random
from rag_based_query_system import HealthRAGSystem



########## 세션 상태 초기화 ###########

# 업스테이지 api
if 'API_KEY' not in st.session_state: # API key 담을 변수 설정
	if os.path.exists('.env'): 	# 로컬에서 테스트 실행 시 API KEY 가져오기 
		load_dotenv()
		st.session_state.API_KEY = os.getenv("API_KEY")
	else: # 스트림릿 웹에서 실행 시
		st.session_state.API_KEY = st.secrets["API_KEY"]

if 'masked_API_KEY' not in st.session_state:
	st.session_state.masked_API_KEY = ""

# 사용자 정보
if 'gender' not in st.session_state:
	st.session_state.gender = None

if 'age' not in st.session_state:
	st.session_state.age = None

# 구글맵 api
if os.path.exists('.env'): 	# 로컬에서 테스트 실행 시 
	load_dotenv()
	GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
else: # 스트림릿 웹에서 실행 시
	GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
	

if 'viewer_visible' not in st.session_state: # 파일 뷰어 상태 설정
	st.session_state.viewer_visible = False

if 'last_uploaded_file' not in st.session_state:
	st.session_state.last_uploaded_file = None

if 'has_result' not in st.session_state: # 결과 상태 설정
    st.session_state.has_result = False
    st.session_state.simple_explanation = ""

if 'health_info' not in st.session_state: # 건강 정보 (JSON) 상태 설정
	st.session_state.health_info = None

if 'reason_for_specialty' not in st.session_state: # 진료과 추천 이유
	st.session_state.reason_for_specialty = None

if 'specialty' not in st.session_state: # 추천 진료과 상태 
	st.session_state.specialty = None

# 챗봇 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None


df_loading_text = pd.read_csv('data/loading_text.csv', index_col = 'index', encoding='utf-8-sig') # 로딩 시 보여줄 건강 안내 문구
df_clinics = pd.read_pickle('data/clinics_info.pkl') # 병원 정보 데이터


########## functions ###########

# 건강검진 파일 업로드 후 실행 함수
def initial_run():
	if not uploaded_file: # 파일 없을 경우
		with container_file:
			st.markdown("파일을 업로드해주세요")
		return None

	if st.session_state.gender is None or st.session_state.age is None:
		with container_file:
			st.markdown("성별과 나이를 입력해주세요")
		return None
	
	file_path = save_file(uploaded_file) # 파일 저장 및 파일 경로 return

	completion_event = threading.Event() # 스레드 완료 이벤트
	result_queue = queue.Queue() # 결과 저장용 큐 생성

	# 스레드 실행
	def thread_worker(API_KEY, file_path, result_queue):
		try:
			health_info = return_json(API_KEY, file_path, result_queue) # 검진 결과 JSON
			summary = return_summary(API_KEY, health_info) # 핵심 요약
			simple_explanation = return_simple_explanation(API_KEY, health_info, summary, result_queue) # 친절한 설명
			reason, specialty = suggest_specialty(API_KEY, health_info, summary, result_queue) # 진료과 추천
		except Exception as e:
			result_queue.put(("error", str(e)))
		finally:
			completion_event.set()

	# API 호출 스레드 시작
	api_thread = threading.Thread(
		target=thread_worker,
		args=(st.session_state.API_KEY, file_path, result_queue)
	)
	api_thread.daemon = True
	api_thread.start()

	# 로딩 표시 영역
	loading_container = st.empty()
	start_time = time.time()
	index = random.randrange(1, 101)
	last_change = start_time

	# 스레드(LLM 추론) 끝날 때까지 로딩 화면
	while not completion_event.is_set():
		current_time = time.time()
		elapsed = int(current_time - start_time)

		# 7초마다 메시지 변경
		if current_time - last_change >= 7:
			index = random.randrange(1, 101)
			last_change = current_time

		# 로딩 표시 업데이트
		loading_container.markdown(f"""
        <div class="loading-box">
			<h2>친절한 설명을 준비중이에요</h2>
            <div class="loading-spinner"></div>
			<p>알고 계셨나요?</p>
            <p>{df_loading_text.loc[index, 'info']}</p>
            <p style="font-size: 12px; color: #666;">경과 시간: {elapsed}초</p>
        </div>
        """, unsafe_allow_html=True)

		# 짧은 대기 후 상태 확인
		time.sleep(0.1)
	
	# 로딩 표시 제거
	loading_container.empty()

	# 결과 수집 및 처리
	results = {}
	while not result_queue.empty():
		key, value = result_queue.get()
		results[key] = value
	
	st.session_state.health_info = results['health_info']
	st.session_state.simple_explanation = results['simple_explanation']
	# st.session_state.summary = summary
	st.session_state.has_result = True
	st.session_state.viewer_visible = False # 파일 뷰어 끄기
	st.session_state.reason_for_specialty = results['reason']
	st.session_state.specialty = results['specialty']

# 파일 저장 함수
def save_file(uploaded_file):
	if not os.path.exists('uploaded_files'):
		os.makedirs('uploaded_files')
	file_name = uploaded_file.name
	file_path = os.path.join('uploaded_files', file_name)
	with open(file_path, 'wb') as f:
		f.write(uploaded_file.getbuffer())

	return file_path

# 병원 찾기 함수
def search_clinics(specialty, k=3):
	if specialty == '해당없음':
		with container_result:
			st.markdown('추천 진료 병원이 없습니다.')

		return None

	if user_location['latitude'] == None:
		with container_result:
			st.markdown('위치 정보가 필요합니다. 위치 정보 활용 버튼을 클릭해주세요.')

		return None
	
	# 위치 정보
	latitude = user_location['latitude']
	longitude = user_location['longitude']

	clinics = get_nearest_clinics(df_clinics, longitude, latitude, specialty, k) # 병원 정보
	with container_result: # 병원 정보 출력
		for i, row in clinics.iterrows():
			st.button(row['요양기관명'], on_click=show_map, args=({row['요양기관명']},)) # 병원 이름 클릭 시 지도 표시
			st.markdown(f"""
			**주소:** {row['주소']}  
			**전화번호:** {row['전화번호']}  
			**홈페이지:** {row['병원홈페이지']}
			""")

# 지도 표시 함수
def show_map(place_name):
	map_url = f"""
	<iframe 
	    src="https://www.google.com/maps/embed/v1/place?key={GOOGLE_MAPS_API_KEY}&q={place_name}&language=ko" 
	    width="600" 
	    height="450" 
	    style="border:0;" 
	    allowfullscreen="" 
	    loading="lazy">
	</iframe>
	"""
	with container_map:
		components.html(map_url, height=500)



########## UI ###########

# 웹 탭 꾸미기
st.set_page_config(
    page_title="AI 건강검진결과 분석 도우미 - MAGIC",
)

# # 사이드바 
# with st.sidebar:

# 	def on_submit(): # API key submit 버튼 클릭 시
# 		st.session_state.API_KEY = st.session_state.temp_key # api key
# 		# api key 마스킹
# 		temp_chars = list(st.session_state.API_KEY)
# 		for i in range(len(temp_chars[4:-1])):
# 			temp_chars[i+4] = "*"
# 		st.session_state.masked_API_KEY = "".join(temp_chars)

# 		st.session_state.temp_key = ""
	
# 	# API key 입력 form
# 	with st.form("api_key_form", clear_on_submit=False):
# 		intput_API_KEY = st.text_input(
# 			label = f"Upstage API Key: {st.session_state.masked_API_KEY}",
# 			placeholder = "Upstage API Key를 입력하세요",
# 			key = "temp_key",
# 		)

# 		btn_api_key_submit = st.form_submit_button("Submit", on_click=on_submit)


st.title("AI 건강검진결과 분석 도우미")
st.subheader('안녕하세요! 저는 MAGIC이에요.')
st.markdown('')

# 사용자 정보 입력 칸
container_user_info = st.container()
with container_user_info:
    st.subheader("기본 정보")
    
    col1, col2 = st.columns(2)
    with col1:
        gender = st.radio("성별", ["남성", "여성"], key="gender_input", horizontal=True)
        if gender:
            st.session_state.gender = gender
    
    with col2:
        age = st.number_input("나이", min_value=1, max_value=120, step=1, key="age_input")
        if age > 0:
            st.session_state.age = age

# 파일 업로드 칸
container_file = st.container()
with container_file:
    st.subheader("건강검진 결과 업로드")
    uploaded_file = st.file_uploader("PDF 또는 이미지 파일을 선택하세요", type=['pdf', 'jpg', 'jpeg', 'png'])

    # 실행 버튼
    btn_run = st.button("분석 시작", on_click=initial_run)
    
    # 파일 업로드 시 파일 첫 페이지 표시
    if uploaded_file: 
        if uploaded_file != st.session_state.last_uploaded_file: # 상태 변경
            st.session_state.viewer_visible = True
            st.session_state.last_uploaded_file = uploaded_file
            st.session_state.has_result = False

        if st.session_state.viewer_visible: 
            if uploaded_file.type == "application/pdf": # pdf 파일일 경우
                temp = uploaded_file.getvalue()
                viewer = pdf_viewer(input=temp, pages_to_render=[1])
            else: # 이미지 파일일 경우
                image = Image.open(uploaded_file)
                viewer = st.image(image, use_container_width=True)

# 결과 표시 칸
container_result = st.container()

if 'has_result' in st.session_state and st.session_state.has_result:
    # 결과 표시
    with container_result:
        # 친절한 설명
        st.subheader("건강검진 결과 설명")
        st.markdown(st.session_state.simple_explanation) 

        # 추천 진료과
        st.subheader("나에게 맞는 진료과는?")
        st.markdown(st.session_state.specialty)
        st.markdown(f"({st.session_state.reason_for_specialty})")

        # 병원 추천
        st.subheader("추천 병원") # 추천 병원
        col_geolocation1, col_geolocation2 = st.columns([1, 8])
        with col_geolocation1:
            user_location = streamlit_geolocation()
        with col_geolocation2:
            st.markdown("위치 정보 활용을 위해 왼쪽 버튼을 클릭해주세요")
        
        st.button("나에게 맞는 병원 찾기", on_click=search_clinics, args = (st.session_state.specialty,))
        # 위치 정보 확인



# 지도 표시 칸
container_map = st.container()


# 구분선 추가
st.divider()

# 챗봇 섹션
st.subheader("건강 상담 챗봇")
st.markdown("건강 검진 결과나 의학적 궁금증에 대해 질문해보세요.")

# 이전 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 받기
if prompt := st.chat_input("질문을 입력하세요"):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 챗봇 응답 생성
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 생각 중...")
        
        try:
            if st.session_state.API_KEY and st.session_state.health_info:
                # rag_based_query_system의 main 함수를 직접 호출하여 응답 생성
                from rag_based_query_system import main as rag_main
                response = rag_main(
                    api_key=st.session_state.API_KEY,
                    health_status=st.session_state.health_info,
                    user_query=prompt
                )
            else:
                # 필요한 정보가 없는 경우 기본 응답
                if not st.session_state.API_KEY:
                    response = "API 키를 입력해주세요."
                elif not st.session_state.health_info:
                    response = "건강 검진 결과를 먼저 업로드해주세요."
                else:
                    response = "챗봇 시스템 초기화 중입니다. 잠시 후 다시 시도해주세요."
        except Exception as e:
            response = f"오류가 발생했습니다: {str(e)}"
        
        message_placeholder.markdown(response)
    
    # 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": response})


# CSS 스타일 정의 (로딩 모달 스타일)
st.markdown("""
<style>
    .loading-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 15px auto;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)