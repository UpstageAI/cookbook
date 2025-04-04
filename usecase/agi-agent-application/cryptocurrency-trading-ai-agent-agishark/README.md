# 🦈 Cryptocurrency Trading AI Agent [AGISHARK]

### 📌 Overview
This project was developed as part of the AGI Agent Application Hackathon. It's an AI-based trading bot that can check cryptocurrency market information, analyze trading strategies, and execute real trades.

### 🚀 Key Features
- ✅ **Powerful AI Agent**: 
  - Web search capability
  - X (Twitter) search 
  - Autonomous order execution and listing
  - Document database access
  - Multiple AI model selection options
- ✅ **Real-time Exchange Information with Upbit API**:
  - Price and chart viewing for major cryptocurrencies
  - Market trend analysis and visualization
  - Asset management
  - Coin transaction history
- ✅ **Automated Investment Strategies**:
  - AI Agent's automated trading system
  - Customized investment instructions and preference management
  - Large-volume investment guidance management through PDF and RAG documents

### 🖼️ Demo / Screenshots
🎬 [Watch Demo Video on YouTube](https://youtu.be/P0XjDOIf6Fg?si=Luczh8t9vt0eWYJi)

### 🧩 Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: JSON for state management
- **Others**: OpenAI API, Upstage API, Upbit API, X Bearer Token, Vector stores for RAG

### 🏗️ Project Structure
```
📁 cryptocurrency-trading-ai-agent-agishark/
├── app.py                    # Main application entry point
├── init.py                   # Initialization file
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore file
├── page/                     # Streamlit pages
│   ├── api_setting.py        # API configuration interface
│   ├── auto_trader_page.py   # Automated trading interface
│   ├── portfolio.py          # Portfolio management
│   ├── sidebar.py            # App sidebar component
│   ├── trade_history.py      # Trading history view
│   ├── trade_market.py       # Market view
│   └── trade_strategy.py     # Strategy configuration
├── tools/                    # Core functionality tools
│   ├── auto_trader/          # Automated trading logic
│   ├── document_parser/      # PDF and document processing
│   ├── information_extract/  # Data extraction utilities
│   ├── rag/                  # Retrieval-Augmented Generation
│   ├── search_X/             # X (Twitter) search functionality
│   ├── upbit/                # Upbit API integration
│   ├── web2pdf/              # Web to PDF conversion
│   └── web_search/           # Web search capabilities
├── model/                    # AI models
│   └── open_ai_agent.py      # OpenAI integration
├── util/                     # Utility functions
└── data/                     # Data storage
    ├── api_key_store.json    # API key storage
    ├── agent_state.json      # Agent state management
    ├── agent_work_time.json  # Agent work time tracking
    └── vector_store_id.json  # Vector storage IDs
```

### 🔧 Setup & Installation
```bash
cd cryptocurrency-trading-ai-agent-agishark

# Install required packages
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### 📁 Required APIs & References
- **Required APIs**:
  1. **Upstage API Key** (Document Parser, Information Extracter)
  2. **OpenAI API Key** (OpenAI Agent, Web Search, Vector Store)
     - Available at: https://platform.openai.com/api-keys
  3. **Upbit Access Key, Secret Key**
     - Requires K-Bank account setup
     - Available at: https://upbit.com/mypage/open_api_management
     - Note: One key can be used from only one IP address at a time
  4. **X Bearer Token** (Search)
     - Login at: https://developer.x.com/en/portal/dashboard
     - Click the key icon in Project App
     - Generate Bearer Token from Authentication Tokens

### 🙌 Team Members

| Name        | Role               | GitHub                             |
|-------------|--------------------|------------------------------------|
| Jaewan Shin | Development Lead, Frontend, Agent Design, RAG | [@alemem64](https://github.com/alemem64) |
| Jihun Jang  | Investment Strategy Page, Document Management System, Web2PDF, Presentation | [@pinesound05](https://github.com/pinesound05) |
| Yujin Cha   | Web Search, X Search, Document Parser, Information Extract Integration | [@yujinc726](https://github.com/yujinc726) |
| Mingyu Shin | Upbit Agent Tool Development | [@girafxxx-beep](https://github.com/girafxxx-beep) |

### ⏰ Development Period
- **2025-03-29**: 
  - Initial project setup and repository creation
  
- **2025-03-30 ~ 2025-03-31**: 
  - Basic UI construction (Streamlit)
  - Upbit API integration (account connection, trading functionality)
  - Document Parser and Information Extract testing
  - Web-to-PDF conversion feature implementation
  - Sidebar and chat interface development
  
- **2025-04-01 ~ 2025-04-02**: 
  - OpenAI Agent integration and conversation history functionality
  - Agent restart feature implementation
  - Investment strategy page UI and functionality (upload/download/delete)
  - Investment preference settings (customized instructions, risk tolerance, trading period)
  - Web2PDF features and document management system enhancement
  - X (Twitter) search tool addition
  
- **2025-04-03 ~ 2025-04-04**: 
  - AI Agent tools expansion (trading coin list, price lookup, trade execution)
  - WebSearch tool and X (Twitter) search completion
  - RAG (Retrieval-Augmented Generation) integration
  - Automated trading system development and UI improvements
  - Exception handling and bug fixes
  - README documentation and final refinements

### 📄 License
This project is licensed under the [MIT license](https://opensource.org/licenses/MIT).  
See the LICENSE file for more details.

### 💬 Additional Notes
- **Recommended Environment**: Python 3.11.11

- **Troubleshooting**:
  1. **For numpy/pandas installation errors**:
     ```bash
     pip uninstall numpy pandas
     pip install numpy>=1.26.0 pandas>=2.1.0
     ```

  2. **For Mac users**:
     Run this before installation:
     ```bash
     pip install --upgrade pip wheel setuptools
     ```
