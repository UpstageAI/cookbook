import streamlit as st
import requests
from utils import save_conversation

def render_pdf_form():
    st.title("PDF 폼 작성")
    
    # 파일 업로드
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
    
    if uploaded_file is not None:
        # 파일 내용 표시
        st.write("업로드된 파일:", uploaded_file.name)
        
        # 폼 입력
        with st.form("pdf_form"):
            company_name = st.text_input("회사명")
            product_name = st.text_input("제품명")
            quantity = st.number_input("수량", min_value=1)
            price = st.number_input("가격", min_value=0)
            
            submitted = st.form_submit_button("제출")
            
            if submitted:
                # API 호출
                files = {"file": uploaded_file.getvalue()}
                data = {
                    "company_name": company_name,
                    "product_name": product_name,
                    "quantity": quantity,
                    "price": price
                }
                
                response = requests.post(
                    "http://pdfvalidator-app:8001/check-pdf",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("폼이 성공적으로 제출되었습니다!")
                    
                    # 대화 저장
                    messages = [
                        {
                            "role": "user",
                            "content": {
                                "file_name": uploaded_file.name,
                                "form_data": data
                            }
                        },
                        {
                            "role": "assistant",
                            "content": result
                        }
                    ]
                    save_conversation("pdf_form", messages)
                else:
                    st.error("API 호출 중 오류가 발생했습니다.") 