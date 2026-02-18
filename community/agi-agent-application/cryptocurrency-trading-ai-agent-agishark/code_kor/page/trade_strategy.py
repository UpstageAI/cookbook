import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
from tools.rag.document_processor import process_uploaded_file
from tools.rag.rag import delete_from_vector_store, async_process

def get_pdf_display(pdf_path):
    """PDF 파일의 첫 페이지를 이미지로 변환"""
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0]
        zoom = 2  # 해상도를 2배로 증가
        mat = fitz.Matrix(zoom, zoom)
        pix = first_page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        return img_data
    except Exception as e:
        st.error(f"PDF 변환 중 오류 발생: {str(e)}")
        return None

def get_pdf_download_link(pdf_path):
    """PDF 파일의 다운로드 링크 생성"""
    with open(pdf_path, "rb") as file:
        pdf_bytes = file.read()
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(pdf_path)}">다운로드</a>'

def delete_pdf(file_path, storage_dir):
    """PDF 파일 삭제"""
    try:
        file_name = os.path.basename(file_path)
        
        # 파일 삭제
        os.remove(file_path)
        
        # 삭제 상태를 세션 스테이트에 저장
        if 'deleted_files' not in st.session_state:
            st.session_state.deleted_files = set()
        st.session_state.deleted_files.add(f"{storage_dir}_{file_name}")
        
        # RAG 저장소인 경우 벡터 스토어에서도 삭제
        if storage_dir == "tools/web2pdf/rag_doc_storage" and 'vector_store_id' in st.session_state:
            # 벡터 스토어에서 삭제
            async_process(delete_from_vector_store, file_name)
            print(f"벡터 스토어에서 '{file_name}' 삭제 요청 시작")
        
        return True
    except Exception as e:
        st.error(f"파일 삭제 중 오류 발생: {str(e)}")
        return False

def display_pdf_section(title, storage_dir):
    """PDF 섹션 표시"""
    st.subheader(title)
    
    # 파일 업로드
    uploaded_file = st.file_uploader(f"PDF 파일 업로드 ({title})", type="pdf", key=f"uploader_{storage_dir}")
    if uploaded_file is not None:
        try:
            file_path = os.path.join(storage_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
                
            # RAG 문서 저장소인 경우, 자동으로 문서 처리
            if storage_dir == "tools/web2pdf/rag_doc_storage":
                # OpenAI API 키 확인
                if not st.session_state.get('openai_key'):
                    st.error("OpenAI API 키가 설정되지 않았습니다. API 설정 탭에서 키를 입력해주세요.")
                else:
                    # 비동기 처리 시작
                    process_uploaded_file(file_path, uploaded_file.name)
                    message = "업로드 완료. 문서가 RAG 시스템에 자동으로 추가되고 있습니다."
                    if not st.session_state.get('upstage_api_key'):
                        message += " (Upstage 파싱 없이 직접 업로드)"
                    st.success(message)
            else:
                st.success(f"'{uploaded_file.name}' 파일이 업로드되었습니다.")
        except Exception as e:
            st.error(f"파일 업로드 중 오류 발생: {str(e)}")
    
    # PDF 파일 목록 표시
    pdf_files = [f for f in os.listdir(storage_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        st.info("저장된 PDF 파일이 없습니다. 파일을 업로드해주세요.")
        return
    
    # PDF 파일들 표시
    for idx, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(storage_dir, pdf_file)
        file_key = f"{storage_dir}_{pdf_file}"
        
        # 삭제된 파일은 건너뛰기
        if 'deleted_files' in st.session_state and file_key in st.session_state.deleted_files:
            continue
        
        # PDF 미리보기 이미지 표시
        pdf_image = get_pdf_display(pdf_path)
        if pdf_image:
            st.image(pdf_image, use_container_width=True)
            st.caption(pdf_file)
            
            # 버튼들을 가로로 배치
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(get_pdf_download_link(pdf_path), unsafe_allow_html=True)
            with col2:
                if st.button(f"삭제", key=f"delete_{file_key}"):
                    if delete_pdf(pdf_path, storage_dir):
                        st.rerun()

def show_trade_strategy():
    st.title("✨ AI 투자 전략")
    
    # 저장 디렉토리 설정
    pdf_storage = "tools/web2pdf/always_see_doc_storage"
    rag_storage = "tools/web2pdf/rag_doc_storage"
    os.makedirs(pdf_storage, exist_ok=True)
    os.makedirs(rag_storage, exist_ok=True)
    
    # API 키 상태 확인 및 경고 표시
    if not st.session_state.get('openai_key'):
        st.warning("OpenAI API 키가 설정되지 않았습니다. RAG 문서 처리 기능을 사용하려면 API 설정 탭에서 키를 입력해주세요.")
    
    # 2개의 컬럼으로 나누기
    col1, col2 = st.columns(2)
    
    # 왼쪽 컬럼: 항시 참조 문서
    with col1:
        display_pdf_section("항시 참조 문서", pdf_storage)
    
    # 오른쪽 컬럼: RAG 문서
    with col2:
        display_pdf_section("RAG 문서", rag_storage)
