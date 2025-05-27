import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
from tqdm import tqdm

# 경로 설정
PROGRAM_PATH = os.path.abspath(os.getcwd())
ASSETS_PATH = os.path.join(PROGRAM_PATH, "assets")

TERMINOLOGY_PATH = os.path.join(ASSETS_PATH, "dataflattened_terminology.csv") 
FAISS_INDEX_PATH = os.path.join(ASSETS_PATH, "faiss_index_snomed")

# 모델 로드
model_name = "sentence-transformers/all-MiniLM-L12-v2"
model = SentenceTransformer(model_name)

# 데이터 로드
df_snomed_ct = pd.read_csv(TERMINOLOGY_PATH)
concept_names = df_snomed_ct["concept_name"].astype(str).tolist()
concept_ids = df_snomed_ct["concept_id"].tolist()

concept_type_subset = [
    "procedure", #top level category
    "body structure", #top level category
    "finding", #top level category
    "disorder", #child of finding
    "morphologic abnomrality", #child of body structure
    "regime/therapy", #child of procedure
    "cell structure", #child of body structure
]

for concept_type in concept_type_subset:
    df_concept_type = df_snomed_ct[df_snomed_ct["hierarchy"] == concept_type]
    concept_names = df_concept_type["concept_name"].astype(str).tolist()
    concept_ids = df_concept_type["concept_id"].tolist()

    print(f"Embedding {len(concept_names)} SNOMED terms for '{concept_type}'...")
    embeddings = model.encode(concept_names, show_progress_bar=True, batch_size=64)

    # FAISS index 생성
    dimension = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 저장 경로 지정
    safe_concept_type = concept_type.strip().lower().replace("/", "_").replace(" ", "_")
    id_map_path = os.path.join(ASSETS_PATH, f"snomed_id_mapping_{safe_concept_type}.tsv")
    faiss_index_path = os.path.join(ASSETS_PATH, f"faiss_index_{safe_concept_type}.index")

    # ID 매핑 저장
    pd.DataFrame({
        "concept_id": concept_ids,
        "concept_name": concept_names
    }).to_csv(id_map_path, sep="\t", index=False)

    # FAISS 인덱스 저장
    faiss.write_index(index, faiss_index_path)
    print(f"Saved: {safe_concept_type}")