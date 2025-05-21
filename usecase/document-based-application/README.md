# 📄 DocZilla

### 📌 Overview
This project was developed as part of the AGI Agent Application Hackathon. It aims to solve the challenge of understanding, verifying, and summarizing documents (such as contracts or policies) using an LLM-powered agent, enabling automated compliance checks, summarization, and intelligent extraction of insights.

### 🚀 Key Features
- ✅ **Document Upload & Parsing**: Admins and users can upload documents which are parsed, summarized, or checked against internal policies.
- ✅ **Slack Notification**: Automatically generates a summary of the latest uploaded document and sends it to a Slack channel via webhook.
- ✅ **Compliance Checklist Extraction**: Parses internal policy documents and uses the LLM to extract a structured, testable checklist to compare against future contracts.
### Demo 🎉
Experience the project in action with our live demo. Click the link below for a guided walkthrough showcasing document upload, parsing, compliance checklist extraction, and Slack integration.

[Watch Live Demo](https://example.com/demo)

![pic1](/screenshots/pic1.jpg)

![pic2](/screenshots/pic2.jpg)

![pic3](/screenshots/pic3.jpg)

[Watch Demo Video](https://drive.google.com/file/d/16xkGJr7-6aurjEV-tFU9HOB-LRJxrJI7/view?usp=sharing)

### 🧩 Tech Stack
- **Frontend**: Next.js, Tailwind CSS
- **Backend**: FastAPI
- **Database**: FAISS (vector database)
- **Others**: OpenAI API (solar-pro via Upstage), LangChain, Slack Webhooks

### 🏗️ Project Structure


### 🧩 Tech Stack
- **Frontend**: [e.g., React, Vue, HTML/CSS]
- **Backend**: [e.g., Node.js, Flask, Django]
- **Database**: [e.g., MongoDB, MySQL, Firebase]
- **Others**: [e.g., OpenAI API, LangChain, HuggingFace, Docker]

### 🏗️ Project Structure
```
📁 The-Nomads/
├── frontend/
│    ├── components.json             # Central config for UI component references.
│    ├── next.config.mjs             # Next.js custom configuration settings.
│    ├── package-lock.json           # Auto-generated lockfile for npm dependency versions.
│    ├── package.json                # Project metadata and frontend dependencies.
│    ├── tailwind.config.ts          # Tailwind CSS theme and utility configuration.
│    ├── tsconfig.json               # TypeScript compiler options and path aliases.
│    ├── app/
│    │   ├── globals.css             # Global styles applied across the entire app.
│    │   ├── layout copy.tsx         # Backup or experimental layout file.
│    │   ├── layout.tsx              # Root layout component for consistent app structure.
│    │   ├── page.tsx                # Landing page of the application.
│    │   ├── dashboard/
│    │   │   └── page.tsx            # User dashboard displaying chat interface and uploads.
│    │   └── pricing/
│    │       └── page.tsx            # Pricing page showing subscription plans.
│    ├── components/
│    │   ├── action-panel.tsx        # Button panel for user interactions.
│    │   ├── action-sidebar.tsx      # Sidebar showing actions or document options.
│    │   ├── app-sidebar.tsx         # Main app sidebar for navigation.
│    │   ├── chat-interface.tsx      # Main component for displaying chat sessions.
│    │   ├── chat-panel.tsx          # Panel to display chat messages and input field.
│    │   ├── file-uploader.tsx       # Component for uploading policy and contract files.
│    │   ├── landing-page.tsx        # Component structuring the homepage content.
│    │   ├── login-form.tsx          # Authentication form for login.
│    │   ├── signup-form.tsx         # Authentication form for new user registration.
│    │   ├── theme-provider.tsx      # Context for dark/light mode and theme settings.
│    │   ├── pricing/
│    │   │   ├── pricing-cards.tsx   # Reusable pricing plan cards.
│    │   │   ├── pricing-header.tsx  # Header text and layout for pricing section.
│    │   │   └── pricing-toggle.tsx  # Toggle between monthly/yearly billing.
│    │   └── ui/                     # Shared low-level UI components (e.g., buttons, modals).
│    ├── hooks/                      # Custom React hooks for managing state and logic.
│    ├── lib/                        # Helper functions and client-side utilities.
│    ├── public/                     # Static files like logos, icons, etc.
│    ├── services/
│    │   ├── chat.ts                 # API handler for sending/receiving chat messages.
│    │   └── upload.ts               # API handler for file upload requests.
│    ├── styles/
│    │   └── globals.css             # Duplicate reference for styling, used by legacy files.
│    └── types/
│        └── chat.ts                 # Type definitions related to chat message objects.
├── backend/
│    ├── main.py                     # FastAPI app
│    ├── routes/
│    │   ├── upload.py               # uploading documents to be parsed and then stored in the vector database
│    │   ├── query.py                # embedding the query (prompt), and compare it to the vectore database using cosine similarity
│    │   ├── chat.py                 # managing the session connection between the user and the LLM
│    │   ├── slack.py                # summarizing the document and send the summary to slack
│    │   └── policy.py               # uploading the internal policy to the database and checking the contracts against it
│    ├── utils/
│    │   ├── parse.py                # Upstage API helper for parsing docs
│    │   ├── ocr.py                  # Upstage API helper for ocr images
│    │   ├── embedding.py            # converting string to vector representations (embeddings)
│    │   ├── chunk.py                # dividing the big documents into smaller, relatable parts, utilizing metadata
│    │   ├── llm.py                  # managing chat sessions while keeping the history
│    │   └── retrieve.py             # comparing the queries to the vectors in the database and retrieve the most similar ones
│    ├── vector_store/
│    │   ├── embedding_store.pkl     # saved FAISS index
│    │   └── latest_document.pkl     # keeping track of the latest added document (is overwritten every time we upload)
│    ├── schemas/
│    │   └── chat_payload.py         # pydantic model for the chat session object
│    ├── data/
│    │   ├── policy_checklist.txt    # the extracted checklist from the policy
│    │   └── latest_document.txt     # the parsed data from the latest document
│    └── .env                        # UPSTAGE_API_KEY, etc.
└── README.md
```

### 🔧 Setup & Installation

```bash
# Clone the repository
git clone https://github.com/M-Abdelhakem/the-nomads.git

# Move to the frontend directory and run
cd frontend
npm install
npm run dev

# Move to the backend directory and run
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 📁 Dataset & References
- **Dataset used**: We generated mock data to simulate some of the usecases we tackled
- **References / Resources**:  
[Internal Policy](https://docs.google.com/document/d/1XjfkSbxQ71sWHhwZoj0pSUSvL26ohWWMSRlrKMtejeE/edit?usp=sharing)  
[Contract 1](https://docs.google.com/document/d/15c5c4Q74BrJIYqFnrnuER_DL_DUXL1kRM2-6qZOUvFk/edit?usp=sharing)  
[Contract 2](https://docs.google.com/document/d/1YufhygMcE5dVumpEL7naMiaBGG6DSTW3HV1vMPWIKKs/edit?usp=sharing)  

### 🙌 Team Members

| Name        | Role               | GitHub                             |
|-------------|--------------------|------------------------------------|
| Mohanad Abdelhakem     | Full-Stack Developer | [@M-Abdelhakem](https://github.com/M-Abdelhakem) |
| Madiyar Zhunussov  | Full-Stack Developer  | [@madiyarzm](https://github.com/madiyarzm) |

### ⏰ Development Period
- Last updated: 2025-04-13

### 📄 License
This project is licensed under the [MIT license](https://opensource.org/licenses/MIT).  
See the LICENSE file for more details.

### 💬 Additional Notes
- Feel free to include any other relevant notes or links here.