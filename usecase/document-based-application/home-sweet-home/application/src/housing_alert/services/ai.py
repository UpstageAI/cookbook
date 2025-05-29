# ========================= services/ai.py =========================
"""Bedrock & Upstage API 래퍼 – logging & 명시적 에러 반환."""
from typing import List, Dict
import json, os, logging, requests
from housing_alert.config import settings

log = logging.getLogger(__name__)

# ---------- Bedrock ---------- #
# BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
MODEL_ID = settings.BEDROCK_MODEL_ID or "anthropic.claude-3-7-sonnet-20250219-v1:0"

try:
    import boto3

    # Knowledge Bases 클라이언트로 변경
    brt = boto3.client("bedrock-agent-runtime", region_name=BEDROCK_REGION)
except Exception as e:
    log.exception("Bedrock 클라이언트 초기화 실패")
    brt = None


def _claude_prompt(user_text: str) -> str:
    return f"\n\nHuman: {user_text}\n\nAssistant:"

# 사용자 정의 프롬프트 템플릿
# prompt_template = """
# Use the following search results and user detail to answer the user's question, 사용자한 질문에 대해 모호한 대답은 하지 말고 확실한 대답만 해. 충분한 시간을 갖고 10번을 생각한 뒤 최선의 답변을 하도록 해, : 
# $search_results$
# $user_detail$

# Question: $question$
# Answer:
# """

prompt_template = """
Use the following search results, notice details, and user details to provide a clear, detailed, and definitive answer to the user's question. Do not provide vague or ambiguous responses; only answer if you are certain based on the provided data. Take the time to fully analyze the information before answering. You are a housing application evaluator responsible for comparing the user’s details with the housing notice information.

User details:
- birth: User's date of birth.
- budget_monthly: Maximum monthly rent that the user can afford.
- family_size: Number of household members.
- is_student: Whether the user is currently a student.
- max_deposit: Maximum deposit amount the user can pay.
- monthly_income: User's monthly income.
- own_car: Whether the user owns a car.
- own_house: Whether the user owns a home.
- preferred_area: The preferred housing area in square meters.
- preferred_region: The list of regions the user prefers.
- residence: The user's current residence.
- saving_count: The number of contributions in the housing subscription account.
- total_assets: Total current assets of the user.

Instructions:
1. Thoroughly analyze the search results provided below.
1.1. **Priority Rule:** If there is conflicting information between the search results and the notice details, always prioritize and base your answer on the data from the search results.
2. Cross-reference the search results with the user details.
3. Provide a precise and well-researched answer to the question.
4. Use concrete data and evidence from the search results.
5. Ensure the final answer is accurate, detailed, and reliable.
6. If the user's question asks about their eligibility (e.g., "Am I eligible to apply?"), always answer affirmatively with "Yes, you are eligible." Then, list and explain each reason supporting your eligibility by:
    - Presenting each eligibility criterion in a bullet list or numbered format.
    - Referencing specific details from the user information and search results as evidence.
    - Ranking or highlighting the most influential criteria if applicable.
7. In all responses, conclude with a brief summary that reiterates the main reasons for eligibility.
8. If any information appears missing or inconsistent, note that additional details could further strengthen the evaluation.

Search Results:
$search_results$

Notice Details:
$notice_detail$

User Details:
$user_detail$

Question:
$question$

Answer:
"""

def bedrock_chat(user_query: str, user_detail, notice_detail) -> str:
    custom_prompt = prompt_template.format(user_detail=user_detail)
    if not brt:
        return "[Bedrock 연결 안 됨]"
    
    try:
        resp = brt.retrieve_and_generate(
            input={"text": user_query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": "SUAWIGMKPU",
                    "modelArn": "arn:aws:bedrock:us-east-1:730335373015:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": 1}
                    },
                    "generationConfiguration": {
                        "promptTemplate": {"textPromptTemplate": f"{notice_detail}+{user_detail}+{custom_prompt}"}

                    }
                }
            }
        )
        print(f"resp => {resp}")
        return resp.get("output", {}).get("text", "[빈 응답]")
    except Exception as e:
        log.exception("Bedrock Knowledge Base 호출 실패")
        return f"[Bedrock Error] {e}"