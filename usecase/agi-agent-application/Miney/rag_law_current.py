
import os
from openai import OpenAI
import pandas as pd
from datasets import load_dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS  
from langchain_openai import OpenAIEmbeddings  
from langchain.prompts import PromptTemplate
import json
from Predict import bertPredict
from referecnes import getPrecedent

from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# 2. Load dataset (casename classification)
dataset = load_dataset("lbox/lbox_open", "casename_classification_plus", trust_remote_code=True)
df = pd.DataFrame(dataset['train'])

# 3. Filter only deposit-related cases
deposit_cases = df[df['casename'].isin(['보증금반환', '임대차보증금'])]

# 4. Prepare text chunks for retrieval
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=256,
    chunk_overlap=32,
    separators=["\n\n", "\n", ".", " "]
)

texts = [
    f"사례와 관련 법령: {row['facts']}\n"
    for _, row in deposit_cases.iterrows()
    if isinstance(row['facts'], str)
]

documents = text_splitter.split_text("\n".join(texts))

# 5. Create FAISS Vector Store using OpenAI Embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large", 
    openai_api_key=os.getenv("OPENAI_API_KEY") 
)
vector_store = FAISS.from_texts(documents, embedding=embedding_model)

# 6. Define Prompt Template for GPT-4
template = """[법률 분석 요청]
상황: {context}
질문: {question}
답변:"""

QA_PROMPT = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)

def rag(prompt, k=2):
    return "\n".join([c.page_content for c in vector_store.similarity_search(prompt, k)])

## Functions
functions = [
    {
        "type": "function",
        "name": "getPrecedent",
        "description": "관련된 판례를 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "상황에 대한 자유 형식의 설명"
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "type": "function",
        "name": "bertPredict",
        "description": "상황에 대한 민사 재판 승소율을 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "상황에 대한 자유 형식의 설명"
                }
            },
            "required": ["text"]
        }
    },
    {
        "type": "function",
        "name": "rag",
        "description": "상황에 유사 법률 db 자료를 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "상황에 대한 자유 형식의 설명"
                }
            },
            "required": ["prompt"]
        }
    }
]












# GPT Function Calling을 통해 사용자 질문 처리하는 메인 함수
def handle_user_query(query, conversation_history):
    contexts = vector_store.similarity_search(query, k=2)
    user_query = QA_PROMPT.format(context=contexts, question=query)
    # 대화 기록에 사용자 메시지 추가
    conversation_history.append({"role": "user", "content": user_query})
    
    # GPT-4에 사용자 질문 전달 (함수 리스트 포함)
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions="""
        나는 사용자 질문에 따라 필요한 경우 제공된 함수 중 하나를 선택해 호출할 수 있다. 각 함수는 다음 상황에서 호출한다:

1. getPrecedent 함수:
- 사용자가 상황과 관련된 판례를 요청할 때 호출

2. bertPredict 함수:
- 사용자가 특정 상황에서의 재판 승소율을 요청할 때 호출.

3. rag 함수:
- 사용자가 관련 법률 db에서 관련된 사항을 요청할 때 호출

위 기준에 맞지 않는 질문이나 일반적인 대화는 함수 활용 없이 답변한다. 사용자의 의도가 불분명하면 명확한 정보를 요청하고, 가능한 한 정확한 함수와 매개변수를 선택해 호출한다.

대화 맥락을 고려하여 이전 대화 내용을 참조하고 일관된 응답을 제공한다.
""",
        input=conversation_history,
        tools=functions,
        tool_choice="auto"
    )

    # 새로운 API에서 응답 구조 확인
    if response.status == "completed":
        # 툴 호출이 있는지 확인
        message = response.output[0]
        
        # 툴 호출이 있는 경우
        if message.type == "function_call":
            tool_call = message
            func_name = tool_call.name
            args = json.loads(tool_call.arguments)
            
            # GPT가 요청한 함수를 실제 실행
            if func_name == "getPrecedent":
                result = getPrecedent(**args)
            elif func_name == "bertPredict":
                result = bertPredict(**args)
            elif func_name == "rag":
                result = rag(**args)
            else:
                result = "요청한 기능이 존재하지 않습니다."

            # 함수 결과를 GPT에게 다시 전달하여 최종 응답 생성
            conversation_history.append(tool_call)
            conversation_history.append({
                "type": 'function_call_output',
                "call_id": tool_call.call_id,
                "output": result
            })

            final_response = client.responses.create(
                model="gpt-4o-mini",
                input=conversation_history,
            )

            assistant_response = final_response.output[0].content[0].text
            # 대화 기록에 어시스턴트 응답 추가
            conversation_history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
        
        # 툴 호출이 없는 경우 (일반 텍스트 응답)
        assistant_response = message.content[0].text
        # 대화 기록에 어시스턴트 응답 추가
        conversation_history.append({"role": "assistant", "content": assistant_response})
        return assistant_response
    
    error_message = "응답을 생성하는 중 오류가 발생했습니다."
    conversation_history.append({"role": "assistant", "content": error_message})
    return error_message



'''
# 7. Function to Generate Answer Using OpenAI's New API
def generate_answer(query, context):
    input_text = QA_PROMPT.format(context=context, question=query)
    
    response = openai.chat.completions.create( 
        model="gpt-4",
        messages=[
            {"role": "system", "content": "법률 질문을 도와드립니다."},
            {"role": "user", "content": input_text}
        ],
        max_tokens=1000, 
        temperature=0.7,
        top_p=0.9
    )
    
    return response.choices[0].message.content

# 8. Query Execution


    # print("\n[AI 법률 분석]\n", answer)
'''
