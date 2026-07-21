from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os, json, tempfile, base64
import pandas as pd
import base64
from datetime import datetime
from openai import OpenAI
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()

# -------------------- 설정 및 준비된 데이터 --------------------
app = FastAPI()
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
chat = ChatUpstage(api_key=UPSTAGE_API_KEY, model="solar-pro")
base_dir = os.path.dirname(os.path.abspath(__file__))
memory_path = os.path.join(base_dir, "memory.json")


# 메모리(기준값) 데이터
with open("memory.json", "r", encoding="utf-8") as f:
    memory_data = json.load(f)

# "준비된" CSV 로딩 (각각 combined_text 열이 있음)
harmful_df = pd.read_csv("harmful_substances_prepared.csv")  # 유해물질
additives_df = pd.read_csv("food_additives_prepared.csv")    # 식품첨가물
# customs_df = pd.read_csv("customs_issues_prepared.csv")      # 통관 문제

def filter_df_prepared(df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    """combined_text 열에서 keywords 중 1개 이상 포함되면 필터링"""
    # Ensure all keywords are strings
    keywords = [str(kw) for kw in keywords]

    mask = df["combined_text"].apply(
        lambda val: any(kw in str(val) for kw in keywords)
    )
    return df[mask]

def get_conversation_file_path():
    """conversation_memory.json 파일의 절대 경로를 반환"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    return os.path.join(project_root, "conversation_memory.json")

# -------------------- 신규: Information Extraction API 클라이언트 --------------------
client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1/information-extraction"
)
client2 = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1/information-extraction/schema-generation"
)

def encode_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    return base64.b64encode(file_bytes).decode("utf-8")


def chunked_summarize_csv(title: str, csv_text: str, chat_obj: ChatUpstage, max_lines_per_chunk: int = 50) -> str:
    """
    CSV 텍스트를 여러 chunk로 나눈 뒤 각각에 대해 요약하고,
    마지막에 전체 내용을 종합 요약하여 반환한다.
    """
    lines = csv_text.splitlines()
    if not lines:
        return f"- {title}: 관련 정보 없음"

    # 청크별 요약 결과 저장
    partial_summaries = []

    # chunk 단위로 분할하여 부분 요약
    for start in range(0, len(lines), max_lines_per_chunk):
        end = start + max_lines_per_chunk
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines)

        prompt_summary = f"""
[Chunk {start//max_lines_per_chunk + 1}] 아래는 {title} 관련 CSV 일부입니다:

{chunk_text}

해당 부분에 포함된 주요 성분/이슈를 바탕으로, 수출입 업무시 주의해야 할 사항을 요약해 주세요.
함량 제한 등 구체적인 정보와 명확한 수치를 바탕으로 미국 기준으로 작성하세요. 
        """
        summary_result = chat_obj.invoke([HumanMessage(content=prompt_summary)])
        partial_summaries.append(summary_result.content.strip())

    # 모든 chunk 요약을 모아 최종 종합 요약
    combined_text = "\n".join(
        f"<Chunk #{i+1} 요약>\n{partial_summaries[i]}"
        for i in range(len(partial_summaries))
    )

    final_prompt = f"""
다음은 {title}에 대한 여러 Chunk 요약 결과입니다:

{combined_text}

위 내용을 종합하여, {title}와 관련된 최종 주의사항을 간략히 정리해 주세요.
단, 요약과정에서 수치나 구체적인 내용을 생략하거나 빠뜨리면 안됩니다.
"""
    final_summary = chat_obj.invoke([HumanMessage(content=final_prompt)])

    return f"- {title}:\n" + final_summary.content.strip()


# -------------------- 메인 로직 --------------------
@app.post("/check-pdf")
async def check_pdf(file: UploadFile = File(...)):
    """
    1) 업로드된 PDF(또는 이미지)를 임시파일에 저장
    2) 임시파일을 base64 인코딩하여 Information Extraction API 호출
    3) 응답 문자열(extracted_str)을 중간 챗봇(ChatUpstage) 통해 재가공 (필요 데이터 추출)
    4) 기준값(memory.json)과 비교
    5) CSV 검색(유해물질, 첨가물, 통관문제) -> 주의사항 요약(청크 단위로 나눠 요약 후 종합)
    6) 최종 결과를 JSON으로 반환 + 대화이력 저장
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # ---------------------------------------------------------------
        # [1] Information Extraction API 호출 (PDF -> base64 -> API)
        # ---------------------------------------------------------------
        pdf_base64_data = encode_file_to_base64(tmp_path)

        # (A) 스키마 생성 API 호출
        schema_response = client2.chat.completions.create(
            model="information-extract",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:application/pdf;base64,{pdf_base64_data}"}
                        }
                    ]
                }
            ],
        )
        schema = json.loads(schema_response.choices[0].message.content)

        # (B) 정보추출 API 호출 (생성된 스키마를 그대로 넘기는 예시)
        extraction_response = client.chat.completions.create(
            model="information-extract",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:application/pdf;base64,{pdf_base64_data}"}
                        }
                    ]
                }
            ],
            response_format=schema
        )

        # extraction_response.choices[0].message.content가 실제 추출한 문자열
        extracted_str = extraction_response.choices[0].message.content
        # print(f"[DEBUG] extraction_response: {extracted_str}")

        # ---------------------------------------------------------------
        # [2] 중간 챗봇 단계 - extracted_str에서 'keywords', 'parsed_text' 등 추출
        # ---------------------------------------------------------------
        middle_prompt = f"""
        다음 정보추출 결과가 있습니다. 
        이 문자열에서 'keywords' 목록과 'extracted_text'만 정리한 JSON을 출력해 주세요.
        'keywords'는 문자열로 구성된 리스트, 'extracted_text'는 문자열 형태로 반환해 주세요.
        'keywords'는 상품명, 성분, 포함 물질 등에 해당할 수 있는 단어만 모두 포함하세요.
        'extracted_text'는 회사 정보와 관련 있는 이름, 주소 등 정보를 모두 포함하세요.

        정보추출 결과: {extracted_str}
        """

        mid_chat_result = chat.invoke([HumanMessage(content=middle_prompt)])
        # mid_chat_result.content는 ChatUpstage가 만들어 준 JSON 문자열일 것
        # print(f"[DEBUG] mid_chat_result: {mid_chat_result.content}")

        # 실제 JSON 파싱 (실패 시 fallback)
        try:
            parsed_json = json.loads(mid_chat_result.content)
        except json.JSONDecodeError:
            parsed_json = {"keywords": [], "extracted_text": ""}

        # 실제로 키워드/문서텍스트를 가져옴
        keywords = parsed_json.get("keywords", [])
        parsed_text = parsed_json.get("extracted_text", "")

        # ---------------------------------------------------------------
        # [3] 기준값(memory.json)과 비교
        # ---------------------------------------------------------------
        prompt_compare = f"""
아래는 문서에서 추출된 텍스트입니다:

{parsed_text}

그리고 내부 시스템에 저장된 기준값은 다음과 같습니다:

{json.dumps(memory_data, ensure_ascii=False, indent=2)}

문서 내 데이터가 메모리 기준값과 일치하는지 확인하고, 불일치하거나 문제가 되는 부분이 있으면 모두 상세히 지적해주세요.
        """
        compare_result = chat.invoke([HumanMessage(content=prompt_compare)])

        # ---------------------------------------------------------------
        # [4] CSV 필터링 -> 주의사항 요약 (청크 단위 요약 사용)
        # ---------------------------------------------------------------
        harmful_match = filter_df_prepared(harmful_df, keywords)
        additive_match = filter_df_prepared(additives_df, keywords)
        # customs_match = filter_df_prepared(customs_df, keywords)

        def summarize_rows(title, df_match):
            if df_match.empty:
                return f"- {title}: 관련 정보 없음"
            else:
                # CSV 문자열 생성
                csv_text = df_match.drop(columns=["combined_text"]).to_csv(index=False)

                # 청크 단위 요약 함수 사용
                return chunked_summarize_csv(title, csv_text, chat)

        caution_summary = "\n\n".join([
            summarize_rows("유해물질", harmful_match),
            summarize_rows("식품첨가물", additive_match)
            # summarize_rows("통관 문제사항", customs_match)
        ])

        # ---------------------------------------------------------------
        # [5] 대화 이력 저장
        # ---------------------------------------------------------------
        # messages = [
        #     {
        #         "role": "user",
        #         "content": f"PDF 파일 검증 요청: {file.filename}"
        #     },
        #     {
        #         "role": "assistant",
        #         "content": {
        #             "중간추출결과": parsed_json,  # 중간 단계 결과
        #             "불일치검사결과": compare_result.content,
        #             "성분및통관주의사항": caution_summary
        #         }
        #     }
        # ]

        # try:
        #     file_path = get_conversation_file_path()
        #     if os.path.exists(file_path):
        #         with open(file_path, 'r', encoding='utf-8') as f:
        #             memory = json.load(f)
        #     else:
        #         memory = {}

        #     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     if "pdf_validation" not in memory:
        #         memory["pdf_validation"] = {}

        #     memory["pdf_validation"][current_time] = messages

        #     with open(file_path, 'w', encoding='utf-8') as f:
        #         json.dump(memory, f, ensure_ascii=False, indent=2)

        #     print(f"대화가 저장되었습니다: {file_path}")

        # except Exception as e:
        #     print(f"대화 저장 중 오류 발생: {str(e)}")

        # ---------------------------------------------------------------
        # [6] 최종 결과 반환
        # ---------------------------------------------------------------
        return JSONResponse(content={
            "불일치검사결과": compare_result.content,
            "성분및통관주의사항": caution_summary
        })

    finally:
        os.remove(tmp_path)


@app.post("/upload-json")
async def upload_json(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed.")

    try:
        contents = await file.read()
        data = json.loads(contents)
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"message": "memory.json has been updated successfully."}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Check if required files exist
        required_files = {
            "memory.json": os.path.exists("memory.json"),
            "harmful_substances_prepared.csv": os.path.exists("harmful_substances_prepared.csv"),
            "food_additives_prepared.csv": os.path.exists("food_additives_prepared.csv")
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "pdf-validator",
            "required_files": required_files,
            "upstage_api_key_configured": bool(UPSTAGE_API_KEY)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)