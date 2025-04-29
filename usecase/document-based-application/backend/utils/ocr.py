import requests
import dotenv
import os

dotenv.load_dotenv()

UPSTAGE_API_KEY = os.environ.get("UPSTAGE_API_KEY")
if UPSTAGE_API_KEY is None:
    raise ValueError("UPSTAGE_API_KEY not set in environment variables.")
UPSTAGE_OCR_URL = "https://api.upstage.ai/v1/document-digitization"


def ocr_image(file_path: str) -> str:
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    files = {"document": open(file_path, "rb")}
    data = {"model": "ocr"}

    response = requests.post(UPSTAGE_OCR_URL, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise Exception(f"OCR failed: {response.text}")

    result = response.json()
    return result.get("text") or result.get("html") or str(result)
