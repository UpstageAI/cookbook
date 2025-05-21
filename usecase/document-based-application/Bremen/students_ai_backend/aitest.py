from openai import OpenAI # openai==1.52.2
import json

 
# Use with stream=False
# print(stream.choices[0].message.content)
# 1. 프롬프트에서 조건 추출
def extract_conditions(prompt):
    system_prompt = f"""
    당신은 논문 추천 조건을 추출하는 시스템입니다.
    가능한 키는 min_year, max_year, journal_name, keywords, min_citation입니다.
    JSON 형식으로만 응답하세요.
    아래 프롬프트에 대해 위 키들을 지정하세요. 만약 명시되어 있지 않다면 넣지 않아도 됩니다.

    프롬프트: "{prompt}"
    """
    client = OpenAI(
        api_key="up_XA8y5rqH0YSVI722edRwzXn9agOQz",
        base_url="https://api.upstage.ai/v1"
    )
    
    stream = client.chat.completions.create(
        model="solar-pro",
        messages=[
            {
                "role": "user",
                "content": system_prompt
            }
        ],
        stream=True,
    )
    
    full_response = ""

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content

    print(full_response)
    
    parsed = json.loads(full_response)
    print(parsed)
    print(parsed['journal_name'])
    if "journal_name" in parsed:
        print("in parsed")
    if "journal_name" in full_response:
        print("in full")
        
extract_conditions('I want to submit to CVPR')