import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pymysql
import json
 
from openai import OpenAI # openai==1.52.2
 

 
# Use with stream=False
# print(stream.choices[0].message.content)
# 1. 프롬프트에서 조건 추출
def extract_conditions(prompt):
    # return """{
    # "journal_name": "CVPR"
    # }"""
    system_prompt = f"""
    당신은 논문 추천 조건을 추출하는 시스템입니다.
    가능한 키는 min_year, max_year, journal_name, keywords, min_citation입니다.
    JSON 형식으로만 응답하세요.
    아래 프롬프트에 대해 위 키들을 지정하세요. 만약 명시되어 있지 않다면 넣지 않아도 됩니다.

    프롬프트: "{prompt}"
    """
    client = OpenAI(
        api_key="up_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
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
    return(full_response)

# 3. 논문 후보 필터링 + 유사도 계산
def find_top_papers(prompt):
    conn = pymysql.connect(host='localhost', user='root', password='1234', db='papers')
    conditions = extract_conditions(prompt)
    parsed = json.loads(conditions)
    query = "SELECT * FROM papers WHERE 1=1"
    if "journal_name" in parsed:
        query += f" AND publications = '{parsed['journal_name']}'"
    if "min_citation" in parsed:
        query += f" AND citations >= {parsed['min_citation']}"
    print(query)
    df = pd.read_sql(query, conn)
    #vectors = model.encode(df['index_term'].tolist(), convert_to_numpy=True)
    #prompt_vec = get_vector(prompt)
    #sims = cosine_similarity([prompt_vec], vectors)[0]
    #top_indices = sims.argsort()[::-1][:3]

    # 'date' 컬럼 기준으로 내림차순 정렬 (오름차순 정렬하려면 ascending=True로 설정)
    df_sorted = df.sort_values(by='date', ascending=False)

    # 상위 3개 데이터 반환
    print(df_sorted.head(3))
    return df_sorted.head(3).to_dict(orient="records")
