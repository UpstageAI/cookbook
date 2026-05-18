
# Upstage Cookbook

This cookbook aims to highlight innovative use cases and outputs created by leveraging Upstage Solar and Document AI’s capabilities. We aim to inspire others by showcasing the versatility and excellence of Upstage features across various domains. The Upstage cookbook is open to the community. If you have an interesting idea for using APIs, spot a typo, or want to add or improve a guide, feel free to contribute!

### How to use? 

Get an API key from Upstage console to try examples in the cookbook. Set the environment variable `UPSTAGE_API_KEY` with your key, or create an `.env` file with the key.


### Submission Guidelines


**Content:**

- Source code for apps, programs, or computational projects assisted by the Upstage APIs.
- Tutorials, educational materials, or lesson plans developed with the Upstage APIs.
- Any other interesting applications that showcase the Upstage API's potential!

**Requirements:**

- Code/text entries should be in .md, .ipynb or other common formats.
- Include an overview describing the project/output and its purpose. Provide step-by-step instructions in a logical order and Include any relevant tips, notes, or variations.
- Projects should be original creations or properly credited if adapted from another source.
- Submissions should not contain explicit violating content.

**Rights:**

- You maintain ownership and rights over your submitted project.
- By submitting, you grant us permission to showcase and distribute the entry.
- Entries cannot infringe on any third-party copyrights or intellectual property.

Let us know if you need any other guidelines or have additional criteria to include! We’re happy to continue iterating on these submission rules.

Disclaimer: The views and opinions expressed in community and partner examples do not reflect those of Upstage.


### API List

| API | Description | Example usage |
| --- | --- | --- |
| Chat | Build assistants using Solar Mini Chat. | [Link](https://console.upstage.ai/docs/capabilities/chat) |
| Document Parse | Serialize documents with tables and figures. | [Link](https://console.upstage.ai/docs/capabilities/document-digitization/document-parsing) |
| Document OCR | Extract all text from any document. | [Link](https://console.upstage.ai/docs/capabilities/document-digitization/document-ocr) | 
| Information Extraction | Extract key information from target documents. | [Link](https://console.upstage.ai/docs/capabilities/information-extraction) | 
| Embedding | Embed strings to vectors. | [Link](https://console.upstage.ai/docs/capabilities/embeddings) |
| Groundedness Check | Verify groundedness of assistant's response. | [Link](https://console.upstage.ai/docs/capabilities/groundedness-checking) |

For more information, visit https://console.upstage.ai


## Cookbook List

### Recipes

Individual notebooks demonstrating core Upstage API usage.

| Notebook | Description |
| --- | --- |
| [Upstage features](recipes/upstage.ipynb) | Experiment with all Upstage APIs (Chat, Embedding, Document OCR, Layout Analysis, etc.) using HTTP, LangChain, and LlamaIndex. |
| [Function calling](recipes/function_calling.ipynb) | Basic function calling example with the Chat API. |
| [LlamaIndex RAG](recipes/llamaindex_rag.ipynb) | Build a Retrieval-Augmented-Generation pipeline using the llama-index Upstage integration package. |
| [Financial analysis](recipes/financial_analysis.ipynb) | Extract and analyze financial insights from 10-K documents using Layout Analysis, LangChain, and Chroma. |
| [How to count tokens](recipes/how_to_count_token.ipynb) | Count tokens using the Solar tokenizer. |

### Courses & Handbooks

| Resource | Description |
| --- | --- |
| [Solar Fullstack LLM 101](Solar-Fullstack-LLM-101) | A comprehensive 29-notebook course covering LLM fundamentals, RAG, document AI, and web app development with Gradio. |
| [Solar Pro2 Prompting Handbook](solar-pro2-prompting-handbook) | Prompt engineering guide for Solar Pro 2 (Korean & English). |
| [Hands-on](hands-on) | Practical hands-on exercises for Document OCR, Layout Analysis, and Key Information Extraction. |

### AWS

Deployment guides for running Upstage models on AWS infrastructure.

| Resource | Description |
| --- | --- |
| [JumpStart](aws/jumpstart) | SageMaker JumpStart notebooks for deploying Solar Chat, Embedding, Document OCR, and Document Parse models. |
| [Document Parse + API Gateway](aws/use_cases/dp-api-gateway) | Serverless REST API for document parsing (API Gateway → Lambda → SageMaker). |
| [Solar + SageMaker Lambda](aws/use_cases/solar-sagemaker-lambda) | Serverless LLM inference with OpenAI-compatible API and streaming support. |
| [Document Parse S3 Connector](aws/use_cases/dp-s3-connector) | Event-driven document processing pipeline (S3 → Lambda → SageMaker). |

### Community

Projects contributed by the community. See [Submission Guidelines](#submission-guidelines) to add yours.

| Project | Description |
| --- | --- |
| [MAGIC](community/agi-agent-application/AGI_Agent_hackathon_2025_MAGIC) | AI health checkup analyzer with OCR-based data extraction and hospital recommendations. |
| [Crypto Trading AI Agent](community/agi-agent-application/cryptocurrency-trading-ai-agent-agishark) | Autonomous cryptocurrency trading agent with market analysis and RAG-based strategy. |
| [RADRAG](community/agi-agent-application/radrag) | Radiology report standardization system mapping free-text to SNOMED CT concepts. |
| [UpDocs (Bremen)](community/document-based-application/Bremen) | AI-powered document writing feedback assistant. |
