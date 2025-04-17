from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from utils.parse import parse_pdf
from utils.ocr import ocr_image
from utils.chunk import chunk_text
from utils.embedding import embed_text
import tempfile
import shutil
import os

upload_router = APIRouter()

ALLOWED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/jpg"]
ALLOWED_PDF_TYPE = "application/pdf"


@upload_router.post("/upload", tags=["Upload"])
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES + [ALLOWED_PDF_TYPE]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only PDFs and images are allowed.")

    try:
        # Save to temporary file
        suffix = os.path.splitext(file.filename)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Use OCR for images, Parse for PDFs
        if file.content_type in ALLOWED_IMAGE_TYPES:
            extracted_text = ocr_image(tmp_path)
        elif file.content_type == ALLOWED_PDF_TYPE:
            extracted_text = parse_pdf(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Save the extracted text to a file
        with open('data/latest_document.txt', 'w', encoding='utf-8') as f:
            f.write(extracted_text)

        # Chunking
        chunks = chunk_text(extracted_text, file.filename)

        # Embedding & storing
        embed_text(chunks)

        return JSONResponse(content={"message": "File processed, chunked, embedded and stored successfully!"})
    
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
