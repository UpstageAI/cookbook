import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from datasets import load_dataset
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

# 모델 및 토크나이저 로드
MODEL_NAME = "monologg/kobert"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
bert_model = AutoModel.from_pretrained(MODEL_NAME, trust_remote_code=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# KoBERT 기반 회귀 모델 정의
class KoBERTRegressor(nn.Module):
    def __init__(self, bert, hidden_size=768, dropout_prob=0.3):  # Dropout 추가
        super(KoBERTRegressor, self).__init__()
        self.bert = bert
        self.norm = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout_prob)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.norm(cls_output)
        cls_output = self.dropout(cls_output)  # Dropout 적용
        return torch.sigmoid(self.fc(cls_output))


# 모델 초기화
model = KoBERTRegressor(bert_model).to(device)
model.load_state_dict(torch.load("./Predict/Iamidiot.pth", map_location=device))
model.eval()

# 예측 함수
def predict(text):
    with torch.no_grad():
        encoded = tokenizer(text, padding="max_length", truncation=True, max_length=512, return_tensors="pt")
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)
        return min(max(model(input_ids, attention_mask).item() , 0.) , 1.)
