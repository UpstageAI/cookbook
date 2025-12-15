# pip install -qU langchain-core langchain-upstage
 
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
load_dotenv()
 
chat = ChatUpstage(api_key=os.getenv("UPSTAGE_API_KEY"), model="solar-pro2")
 
messages = [
    HumanMessage(
        content="Hi, how are you?"
    )
]

response = chat.invoke(messages)
print(response)