from openai import OpenAI
from typing import List
import os
from pydantic import BaseModel
import pandas as pd

class panlyae(BaseModel):
        no: str
        situation: str
        judgement : str
        evidence: str

def generator(text):
    client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    responses=client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """아래 판례를 요약해서 판결 이름, 상황, 판결, 근거로 정리해줘.

                out format: 
                no: str
                situation: str
                judgement : str
                evidence: str
                """
            },
            {
                "role":"user",
                "content":"""아래 판례를 요약해서 판결 이름, 상황, 판결, 근거로 정리해줘.
                판결 이름 예시: 대법원 20xx. xx. xx. 선고 xxxx다xxxxxx, 2xxxxx 판결

                no: 판결이름
                situation: 상황
                judgement: 판결
                evidence: 근거

                판례: """ + text
                + """
                out format: 
                no: str
                situation: str
                judgement : str
                evidence: str"""
                
            }
        ],
        response_format=panlyae
    )
    out = {'no': responses.choices[0].message.parsed.no,
           'judgement' : responses.choices[0].message.parsed.judgement,
           'situation' : responses.choices[0].message.parsed.situation,
           'judgement' : responses.choices[0].message.parsed.judgement,
           'evidence' : responses.choices[0].message.parsed.evidence
           }
          
    return(out)