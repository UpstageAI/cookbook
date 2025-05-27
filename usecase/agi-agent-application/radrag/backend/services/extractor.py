import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from services.pdf_utils import text_to_pdf, encode_to_base64
from services.faiss_mapper import mapping

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(BASE_DIR, "..", "assets") 
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
MIME_TYPE = "application/pdf"

client = OpenAI(
    base_url="https://api.upstage.ai/v1/information-extraction",
    api_key=UPSTAGE_API_KEY
)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "document_schema",
        "schema": {
            "type": "object",
            "properties": {
                "procedure": {"type": "string"},
                "finding": {"type": "string"},
                "body_structure": {"type": "string"},
                "disorder": {"type": "string"},
                "morphologic_abnormality": {"type": "string"},
                "regime_therapy": {"type": "string"},
                "cell_structure": {"type": "string"}
            },
            "required": [
                "procedure", "finding", "body_structure", "disorder",
                "morphologic_abnormality", "regime_therapy", "cell_structure"
            ]
        }
    }
}

def message_formatter(coded):
    return [{
        "role": "user",
        "content": [{
            "type": "image_url",
            "image_url": {"url": f"data:{MIME_TYPE};base64,{coded}"},
        }],
    }]

def extraction_and_mapping(text_input):
    pdf_path = text_to_pdf(text_input)
    base64_encoded = encode_to_base64(pdf_path)
    
    response = client.chat.completions.create(
        model="information-extract",
        messages=message_formatter(base64_encoded),
        response_format=RESPONSE_FORMAT,
    )
    output_json = json.loads(response.choices[0].message.content)
    df = mapping(output_json, ASSETS_PATH, model)
    return df
