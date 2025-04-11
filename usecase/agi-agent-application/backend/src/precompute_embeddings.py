import json
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def precompute_embeddings():
    print("Loading model...")
    model = SentenceTransformer("nlpai-lab/KURE-v1")
    
    print("Loading case database...")
    with open("../datasets/case_db.json", 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    print("Computing embeddings...")
    case_texts = []
    case_embeddings = []
    
    for case in tqdm(cases, desc="Computing embeddings"):
        case_texts.append(case['key'])
        case_embeddings.append(model.encode(case['key']))
    
    # 임베딩을 numpy 배열로 저장
    np.savez('../datasets/precomputed_embeddings.npz',
             texts=case_texts,
             embeddings=np.array(case_embeddings))
    
    print("Embeddings saved successfully!")

if __name__ == "__main__":
    precompute_embeddings()