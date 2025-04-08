from openai import OpenAI
from typing import List
import os
from pydantic import BaseModel
import pandas as pd

class SearchingTerms(BaseModel):
        Terms: List[int]

def selector(text, n=3):
    csv_test = pd.read_csv('./referecnes/reference.pdf.csv')
    file = ''.join([str(i)+'. ' + csv_test['content'][i] + '\n' for i in range(20)])
    
    client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    responses=client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": '''주어진 상황에 가장 적합한 판례를 ''' + str(n) + '''개 선택해서 인덱스를 출력해줘
                '''
            },
            {
                "role":"user",
                "content": '''주어진 상황에 가장 적합한 판례를 ''' + str(n) + '''개 선택해서 인덱스를 출력해줘
                output format: List[int] with length = n
                context: ''' + text + '''
                judicial precedent: ''' + file
            }
        ],
        response_format=SearchingTerms
    )
    out = []
    for i in responses.choices[0].message.parsed.Terms:
          out.append(csv_test['file'][i])
    return(out)
