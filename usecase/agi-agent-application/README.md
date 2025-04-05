# 🛠️ RADRAG

### 📌 Overview

This project was developed as part of the AGI Agent Application Hackathon.  
It aims to solve a critical bottleneck in data standardization for healthcare systems.  
In particular, standardized data is essential not only for accurate insurance claims but also for securing competitive, high-quality datasets in the AI era.  
At institutions like Severance Hospital, a dedicated Data Services Team is working on structured data, but unstructured clinical texts such as free-text descriptions remain largely untouched.  
This project addresses that gap by enabling the standardization of radiology free-text reports.

RADRAG is a **Retrieval-Augmented Generation (RAG)** based tool that standardizes free-text radiology reports into **SNOMED CT** concepts.
It is designed for use in **clinical settings**, integrating external terminology knowledge and extraction models to enable precise concept mapping.

### 🚀 Key Features

✅ Real-time EMR Integration: Enables real-time standardization of clinical notes directly connected to EMR systems, helping to break down data silos.
✅ Batch File Standardization: Supports one-click standardization of existing unstructured report archives.

### 🖼️ Demo / Screenshots

![image](https://github.com/user-attachments/assets/e155609e-34f8-4828-8143-8c9422f2ee0d)
[Optional demo video link: e.g., YouTube]

### 🧩 Tech Stack

- **Frontend**: React + Tailwind + Typescript
- **Backend**: Flask
- **Others**: **Upstage API**, Lanchain, sentence-transformer model, Vite, Vercel, cloudtype

### 🏗️ Project Structure

```
📁 project-name/
├── frontend/
├── backend/
├── rag/
├── README.md
```

## Preparing the Dataset

### 1. Download SNOMED CT

- Download the [SNOMED CT International version](https://www.nlm.nih.gov/healthit/snomedct/index.html) from the UMLS website.
- Registration and license approval are required.
- Once downloaded, store the vocabulary files in the `data/` directory.
  ⚠️ The SNOMED CT files are **not included** in this repository due to licensing restrictions.

### 2. Flatten SNOMED CT Hierarchy

SNOMED CT is hierarchical by design. To enable effective embedding and search, a flat version of the terminology is needed:

```bash
python process_data.py make-flattened-terminology
```

### 3. Generate SNOMED CT Dictionary

This step creates a dictionary file containing terms related to the flattened concept list:

```bash
python process_data.py generate-sct-dictionary --output-path assets/newdict_snomed.txt
```

## Building the FAISS Index

We use sentence-transformers/all-MiniLM-L12-v2 as our embedding model.
Concepts are grouped by concept_type_subset, and separate FAISS indices are built for each group.

Relevant code: [rag/generate_snomedct_faiss.py](https://github.com/burnout909/RADRAG/blob/main/rag/generate_snomedct_faiss.py)

## Free-text Extraction & Mapping

We use the **Upstage Information Extraction API**, which supports key-based entity extraction.
Keys are aligned with the concept_type_subset definitions used for SNOMED CT.

The extracted results are mapped to the nearest concepts in the corresponding FAISS index.

Relevant code: [rag/extraction.py](https://github.com/burnout909/RADRAG/blob/main/rag/extraction.py)

### 🙌 Team Members

| Name         | Role               | GitHub                                   |
| ------------ | ------------------ | ---------------------------------------- |
| Kim Minseong | Leed Developer     | [@kimups](https://github.com/johndoe)    |
| Lee Junyeong | Backend Developer  | [@parkstage](https://github.com/janedev) |
| Kark Minuk   | Frontend Developer | [@parkstage](https://github.com/janedev) |

### ⏰ Development Period

- Last updated: 2025-04-05

### 📄 License

This project is licensed under the [MIT license](https://opensource.org/licenses/MIT).  
See the LICENSE file for more details.
