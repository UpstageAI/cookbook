from fastapi import APIRouter, HTTPException
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
from typing import Optional

slack_router = APIRouter()

load_dotenv()

# Initialize OpenAI client (Upstage Solar)
client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1"
)

# Slack webhook URL
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Path to latest document
LATEST_DOC_PATH = "data/latest_document.txt"

@slack_router.post("/send-slack", tags=["Slack"])
async def send_slack_summary(only_summary: Optional[bool] = None):
    try:
        # Step 1: Read the latest document
        if not os.path.exists(LATEST_DOC_PATH):
            raise HTTPException(status_code=404, detail="Latest document not found.")

        with open(LATEST_DOC_PATH, "r", encoding="utf-8") as f:
            document_text = f.read()

        if not document_text.strip():
            raise HTTPException(status_code=400, detail="Latest document is empty.")

        # Step 2: Ask the model for a summary
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Write an organized summary of the document in an organized and easy-to-follow way."
            },
            {
                "role": "user",
                "content": document_text
            }
        ]

        response = client.chat.completions.create(
            model="solar-pro",
            messages=messages
        )

        summary = response.choices[0].message.content.strip()
        if only_summary:
            return {
                "status": "success",
                "message": "Summary sent to Slack successfully.",
                "summary": summary
            }

        # Step 3: Send the summary to Slack
        payload = {"text": f"*Summary of Latest Document:*\n{summary}"}
        slack_response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if slack_response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send message to Slack: {slack_response.text}"
            )

        return {
            "status": "success",
            "message": "Summary sent to Slack successfully.",
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
