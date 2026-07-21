import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import base64
import sys
from langchain_upstage import ChatUpstage
from langchain.schema import HumanMessage
import requests
from sidebar import render_chat_interface
from utils import (
    save_conversation, 
    load_conversations, 
    perform_web_search, 
    save_search_result, 
    load_search_history,
    load_user_info,
    enhance_prompt_with_web_search
)
import itertools
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

# Document processing function
def process_document_with_upstage(file_bytes):
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}"
    }
    files = {
        "document": ("document.pdf", file_bytes, "application/pdf")
    }
    data = {
        "ocr": "force" if force_ocr else "auto",
        "coordinates": "true",
        "chart_recognition": "true",
        "output_formats": json.dumps(["html"]),
        "model": "document-parse",
        "base64_encoding": json.dumps([])
    }

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        result = response.json()

        text_content = result.get("content", {}).get("html", "").strip() # only use content.text

        if not text_content:
            st.warning("No plain text found in the document (content.text is empty).")

        if TEST_DEBUG_MODE:
            # Debug: Show raw content
            st.subheader("📦 Raw 'content.text' from Document API")
            st.code(text_content[:3000], language="markdown")

        return text_content, None

    except Exception as e:
        return None, e
    
def stream_response(prompt):
    chat = ChatUpstage(
        upstage_api_key=upstage_api_key,
        model_name="solar-pro-241126",
        temperature=0.1,
        stream=True,
    )

    # Use `stream_raw` instead of __call__ to get the streaming generator
    stream = chat.stream([HumanMessage(content=prompt)])

    for chunk in stream:
        # Each chunk should be a ChatMessage — yield its content
        if hasattr(chunk, "content"):
            yield chunk.content

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 페이지 설정
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    .scrollable-container {
        max-height: 300px;
        overflow-y: auto;
        padding-right: 10px; /* optional: avoids clipping scrollbar */
    }
    </style>
    """, unsafe_allow_html=True)

# 채팅 상태 및 인터페이스 초기화 (sidebar.py의 기능 활용)
render_chat_interface()

DEBUG_MODE = False
TEST_DEBUG_MODE = False

# Upstage API key 로드
upstage_api_key = os.getenv("UPSTAGE_API_KEY")

st.title("📄FORMula")

tab0, tab1, tab2 = st.tabs(["Step 0: Import JSON", "Step 1: Form Upload", "Step 2: Form Validate"])

# --- Step 0: Import JSOn ---
with tab0:
    st.header("Step 0: Import data in JSON format")
    # Text area to paste JSON input
    json_input = st.text_area("Paste your JSON here:", height=300)

    if st.button("Submit"):
        try:
            # Try to parse and send JSON
            parsed_json = json.loads(json_input)
            response = requests.post("http://localhost:8000/your-endpoint", json=parsed_json)

            if response.status_code == 200:
                st.success("Data sent successfully!")
                st.write(response.json())
            else:
                st.error(f"Failed to send data: {response.status_code}")
                st.write(response.text)
        except json.JSONDecodeError:
            st.error("Invalid JSON format")

# --- Step 1: Form Upload ---
with tab1:
    st.header("Step 1: Input prompt with initial form")
    
    top_container = st.container()

    with top_container:
        status_placeholder = st.empty()
    
    with st.form("chat_input_form", clear_on_submit=False):
        step1_web_search_enabled = st.toggle("Web Search (for more up-to date information)", key="step1_web_search_enabled")

        initial_text = st.session_state.get("history_prompt", "")
        user_text = st.text_area("Type your message", value=initial_text)
        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
        force_ocr = st.checkbox("Force OCR (for scanned/image PDFs)", value=False)
        submit_button = st.form_submit_button("Submit")
        if "history_prompt" in st.session_state:
            del st.session_state.history_prompt
    
    if submit_button and (user_text or uploaded_file):
        with top_container:
            # status_placeholder.info("Loading...")

            user_msg = {"text": user_text, "file": uploaded_file}
            # 여기서는 대화 기록을 sidebar의 딕셔너리 형식과 별도로 처리할 수 있음.
            # 예시로 st.session_state.chat_history에 append하지 않고, 주로 채팅 API와 저장함.
            
            if TEST_DEBUG_MODE:
                with st.chat_message("user"):
                    st.markdown(user_text)
                    if uploaded_file:
                        st.markdown("Uploaded PDF:")
                        st.write(uploaded_file.name)
            prompt = user_text
            extracted_text = ""

            if st.session_state.step1_web_search_enabled:
                prompt = enhance_prompt_with_web_search(prompt, True)
            
            col1, col2 = st.columns(2, gap="small")
            
            if uploaded_file:
                file_bytes = uploaded_file.read()
                extracted_text, error = process_document_with_upstage(file_bytes)

                with st.spinner("Parsing document...", show_time=True):
                    extracted_text, error = process_document_with_upstage(file_bytes)

                if extracted_text:
                    if TEST_DEBUG_MODE:
                        st.subheader("📄 Parsed Document Content")
                        st.code(extracted_text[:3000], language="markdown")

                    prompt += f"\n\nAdditional context from document:\n{extracted_text}"

                    if TEST_DEBUG_MODE:
                        st.subheader("🖥️ Rendered Document HTML")
                        st.components.v1.html(extracted_text, height=600, scrolling=True)
                elif error:
                    status_placeholder.error(f"Document API error: {error}")
                
                base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
                pdf_display = f"""
                <div class="pdf-container">
                    <embed 
                        src="data:application/pdf;base64,{base64_pdf}" 
                        width="100%"
                        height="700" 
                        type="application/pdf">
                </div>
                """

                with col1:
                    st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                status_placeholder.warning("No PDF uploaded, defaulting to prompt response.")
            
            with col2:
                status_placeholder.success("✅ Done!")

                st.subheader("🤖 Solar Response")
                with st.chat_message("assistant"):
                    st.write_stream(stream_response(prompt))
                    
                    # messages = [
                    #     {"role": "user", "content": {"text": user_text, "file": uploaded_file.name if uploaded_file else None}},
                    #     {"role": "assistant", "content": response_text}
                    # ]
                    # save_conversation("document_processing", messages)
                    
                    # user_info = None  
                    # if user_info:
                    #     from utils import save_user_info
                    #     save_user_info(user_info)
    
# --- Step 2: Form Validate ---
with tab2:
    st.header("Step 2: Upload form for internal scan")

    top_container_2 = st.container()
    
    with st.form("pdf_edit_form", clear_on_submit=False):
        pdf_file_edit = st.file_uploader("Upload editted PDF", type=["pdf"])
        # force_ocr_edit = st.checkbox("Force OCR (for scanned/image PDFs)", value=False)
        submit_pdf_button = st.form_submit_button("Submit")

    if submit_pdf_button:
        with top_container_2:
            status_placeholder2 = st.empty()

            if pdf_file_edit is not None: 
                # Streamlit's uploaded_file is already a file-like object
                files = {
                    "file": (pdf_file_edit.name, pdf_file_edit, "application/pdf")
                }

                with st.spinner("Checking document...", show_time=True):
                    response = requests.post("http://pdfvalidator-app:8001/check-pdf", files=files)

                if response.status_code == 200:
                    status_placeholder2.success("✅ Check complete.")
                else:
                    status_placeholder2.error(f"Error: {response.status_code}")
                pdf_file_edit.seek(0)
                
                # PDF Viewer: Display raw PDF as embedded iframe
                file_bytes_edit = pdf_file_edit.read()
                base64_pdf_edit = base64.b64encode(file_bytes_edit).decode('utf-8')
                pdf_display_edit = f"""
                    <embed 
                        src="data:application/pdf;base64,{base64_pdf_edit}" 
                        width="100%" 
                        height="700" 
                        type="application/pdf">
                """
                
                col1, col2 = st.columns(2, gap="medium", vertical_alignment="top", border=False)
                
                # Add content to the first column
                with col1:
                    st.subheader("PDF Editor")
                    st.markdown(pdf_display_edit, unsafe_allow_html=True)

                # Add content to the second column
                with col2:
                    st.subheader("Internal scan Response")

                    # Send prompt to Solar (ChatUpstage)
                    if response.status_code == 200:
                        st.json(response.json())
                    else:
                        status_placeholder2.error(response.text)
            else:
                status_placeholder2.error(f"Please upload a file")
