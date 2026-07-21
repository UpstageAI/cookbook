> 📢 **Notice:**  
> All teams submitting their project must create a README.md file following this guideline.  
> Please make sure to replace all placeholder texts (e.g., [Project Title], [Describe feature]) with actual content.

# 🛠️ FORMula - THE Form Filling Agent For You

### 📌 Overview
This project was developed as part of the AGI Agent Application Hackathon. It aims to solve the common pain point of filling out complex forms and documents, especially when users are unsure of how to write them or what information is valid.

### 🚀 Key Features
- ✅ **Chatbot Service**:
   - Q&A on domain-related topics.
   - Integrated web search.
   - Conversation history storage.
- ✅  **PDF Document Validation**:
   - Extract document information and compare with internal data.
   - Real-time information retrieval (via web search).
   - Other fixes.
- ✅ **Domain Knowledge: Trade & Customs Assistant**:
   - Check for regulatory compliance.
   - Inspection for hazardous substances/food additives.
   - Provide analysis of all fields and what are missing.

### 🧩 Tech Stack
- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: 
- **Others**: Docker, LangChain, GPT-4o Search Preview, Solar Pro, Upstage Document Parsing API, Upstage Embeddings API, Upstage Information Extract API

### 🏗️ Project Structure
```
📁 agi_hackathon-team_ODE/
├── Chatbot/                   # Chatbot backend server
│   ├── main.py                # FastAPI
│   ├── requirements.txt       
│   ├── .env                   # Chatbot(fastapi) .env keys
│   ├── vector_db/             # Vector DB storage
│   ├── data/                  # Data storage
│   └── base_knowledge_memory.json  # Basic knowledge memory
│
├── Streamlit/                 # Frontend
│   ├── main.py                # Streamlit web interface
│   ├── pdf_form.py            
│   ├── sidebar.py             
│   ├── utils.py               
│   ├── requirements.txt       
│   ├── .env                   # Frontend(streamlit-app) .env keys
│   ├── data/                  # Data storage
│   └── .streamlit/            # Streamlit configuration
│
├── PDFValidator/              # PDF document validation backend
│   ├── main.py                # FastAPI
│   ├── requirements.txt       
│   ├── .env                   # pdfvalidator .env keys
│   ├── data/                  # Data storage
│   └── memory.json            # Memory storage
│
├── Database/                  # Main data storage
│   ├── Merged/                # Merged data
│   ├── Embedding/             # Embedding data
│   └── Connection/            # Database connection
│
├── .devcontainer/             
├── docker-compose.yaml        # Docker Compose configuration
└── README.md                  # README
```

### 🔧 Setup & Installation

```bash
# Clone the repository
git clone https://github.com/bindingflare/agi_hackathon-team_ODE.git
cd agi_hackathon-team_ODE
```

```bash
# Copy zip file to ./Database (Keep file structure intact!)
```

```bash
# Set API Keys (.env)
./Chatbot/.env
UPSTAGE_API_KEY = "your_api_key"
UPSTAGE_EMBEDDING_KEY = "your_api_key"

./PDFValidator/.env
UPSTAGE_API_KEY = "your_api_key"

./Streamlit/.env
UPSTAGE_API_KEY = "your_api_key"
OPENAI_API_KEY = "your_api_key"
```

```bash
# Run with Docker Compose
docker-compose up -d
```

```bash
# Access Streamlit UI
http://localhost:8501
```

### 📁 Dataset & References
- **Dataset used**: US Customs & Border Protection, FDA - Food & Drug Administration (USA), KITA - Korea International Trade Association, KATI Database (aT - Korea Agro-Fisheries & Food Trade Corporation)
- **References / Resources**:  
  1. https://www.cbp.gov/newsroom/publications/forms (Example: CBP Form 7533)
 
  3. https://www.fda.gov/about-fda/reports-manuals-forms/forms (Example: FDA-2541d)
  4. https://www.fda.gov/food/guidance-regulation-food-and-dietary-supplements/guidance-documents-regulatory-information-topic-food-and-dietary-supplements
  5. https://www.fda.gov/food/guidance-regulation-food-and-dietary-supplements
  6. https://www.fda.gov/industry/fda-import-process/prior-notice-imported-foods
  
  7. https://www.kita.net/board/format/formatList.do (Example: 한미 FTA 원산지증명서)
  
  8. https://www.kati.net/additive/additiveList.do

### 🙌 Team Members

| Name   | Role   | Github                     |
|--------|--------|---------------------------|
| 방준현 | Team Lead  | [@bindingflare](https://github.com/bindingflare)         |
| 손재훈 | Backend, Chatbot    | [@wognsths](https://github.com/wognsths)   |
| 이재영 | Modelling  | [@sleepylee02](https://github.com/sleepylee02)   |
| 윤희찬 | Backend, Modelling    | [@quant-jason](https://github.com/quant-jason)   |
| 김정인 | Front-End    | [@jungin7612](https://github.com/jungin7612)   |

### ⏰ Development Period
- Last updated: 2025-04-04

### 📄 License
This project is licensed under the [MIT license](https://opensource.org/licenses/MIT).  
See the LICENSE file for more details.

### 💬 Additional Notes
- Feel free to include any other relevant notes or links here.


