from fpdf import FPDF 
import textwrap 
import base64 

def text_to_pdf(text, pdf_path="user_input.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    # 텍스트를 줄바꿈 포함하여 100자 단위로 자름
    lines = []
    for line in text.split('\n'):
        wrapped = textwrap.wrap(line, width=100)
        lines.extend(wrapped if wrapped else [" "])  # 빈 줄 유지

    # 각 줄을 PDF에 cell로 출력
    for line in lines:
        pdf.cell(0, 10, line, ln=True)

    pdf.output(pdf_path)
    return pdf_path

# Read file
def encode_to_base64(file_path):
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        return base64_encoded