
# Upstage Cookbook

This cookbook aims to highlight innovative use cases and outputs created by leveraging Upstage Solar and Document AI’s capabilities. We aim to inspire others by showcasing the versatility and excellence of Upstage features across various domains. The Upstage cookbook is open to the community. If you have an interesting idea for using APIs, spot a typo, or want to add or improve a guide, feel free to contribute!

### How to use?

Get an API key from Upstage console to try examples in the cookbook. Set the environment variable `UPSTAGE_API_KEY` with your key, or create an .env file with the key.

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
| Chat | Build assistants using Solar Mini Chat. | [Link](https://developers.upstage.ai/docs/apis/chat) |
| Text Embedding | Embed strings to vectors. | [Link](https://developers.upstage.ai/docs/apis/embeddings) |
| Translation | Context-aware translation that leverages previous dialogues to ensure unmatched coherence and continuity in your conversations. | [Link](https://developers.upstage.ai/docs/apis/translation) | 
| Groundedness Check | Verify groundedness of assistant's response. | [Link](https://developers.upstage.ai/docs/apis/groundedness-check) |
| Layout Analysis | Serialize documents with tables and figures. | [Link](https://developers.upstage.ai/docs/apis/layout-analysis) |
| Key Information Extraction | Extract key information from target documents. | [Link](https://developers.upstage.ai/docs/apis/extraction) | 
| Document OCR | Extract all text from any document. | [Link](https://developers.upstage.ai/docs/apis/document-ocr) | 
 


  
## Cookbook List

| Category | Notebook | Description |
| --- | --- | --- |
| Solar-LLM-ZeroToAll | [01_hello_solar.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/01_hello_solar.ipynb) | This notebook serves as an introductory guide to the Solar-LLM series. It walks through the initial setup and basic functionalities of the Solar framework, designed to help users understand and leverage Solar for various applications. The notebook covers installation, configuration, and a simple demonstration to get users up and running with Solar.  |
| Solar-LLM-ZeroToAll | [02_prompt_engineering.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/02_prompt_engineering.ipynb) | This notebook explores conversational prompt engineering and question generation. It covers few-shot examples, keyword/topic generation, and Chain-of-Thought (CoT) prompting.  |
| Solar-LLM-ZeroToAll | [03_hallucinations.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/03_hallucinations.ipynb) | This notebook examines techniques to enhance the factual accuracy and truthfulness of responses from large language models (LLMs). It covers prompt engineering methods like few-shot examples, chain-of-thought prompting, and keyword prompting to prevent hallucinations. |
| Solar-LLM-ZeroToAll | [04_CAG_GC.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/04_CAG_GC.ipynb) | This notebook shows how to use Solar and Langchain for answering questions based on a given context and checking the groundedness (factual accuracy) of the answers using the Upstage Groundedness Check API. |
| Solar-LLM-ZeroToAll | [05_PDF_CAG.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/05_PDF_CAG.ipynb) | Check how to analyze PDF documents using Solar. It includes steps to extract text from PDFs, process the text using various natural language processing techniques, and generate comprehensive analyses.  |
| Solar-LLM-ZeroToAll | [06_LA_CAG.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/06_LA_CAG.ipynb) | Explore how to perform layout analysis on documents using a Solar. It includes techniques for detecting and interpreting the structural elements of a document, such as headings, paragraphs, tables, and figures. And chat based on result. |
| Solar-LLM-ZeroToAll | [07_RAG.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/07_RAG.ipynb) | Learn how to implement Retrieval Augmented Generation (RAG). It showcases how to load documents, create a retriever, and use it with an Solar to answer questions based on retrieved relevant information. |
| Solar-LLM-ZeroToAll | [08_Emb_RAG.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/08_Emb_RAG.ipynb) | This notebook demonstrates how to use Retrieval Augmented Generation (RAG) with semantic vector search for more relevant information retrieval, leveraging techniques like document embedding and vectorstores. It also suggests exploring a hybrid approach that combines keyword search with semantic search to provide comprehensive context for question answering using an Solar. |
| Solar-LLM-ZeroToAll | [09_1_Persistent_ChromaDB.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/09_1_Persistent_ChromaDB.ipynb) | Get how to create a vector store using the Chroma vectorstore and Upstage Embeddings for semantic search. This allows for efficient storage and retrieval of embedded document vectors for semantic search queries. |
| Solar-LLM-ZeroToAll | [09_2_MongoDB.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/09_2_MongoDB.ipynb) | How to set up a MongoDB Atlas cluster and create vector search indexes for semantic search. It shows how to use the MongoDBAtlasVectorSearch class from LangChain to store documents and their embeddings in MongoDB, and perform hybrid searches that combine keyword-based and vector-based retrieval techniques, with results ranked using reciprocal rank fusion. |
| Solar-LLM-ZeroToAll | [09_3_OracleDB.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/09_3_OracleDB.ipynb) | This notebook shows how to use the OracleVectorDB library to store and retrieve text data using vector embeddings. It showcases splitting text into chunks, creating vector embeddings, and indexing/searching the embedded text data. |
| Solar-LLM-ZeroToAll | [09_4_GraphDB.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/09_4_GraphDB.ipynb) | This notebook demonstrates how to use GraphDB capabilities with Neo4j to store and query structured data in the form of nodes and relationships.It covers creating graph documents from text, adding them to a Neo4j database, visualizing the graph, creating a vector index on the graph data, and performing similarity searches and question-answering using the indexed graph. |
| Solar-LLM-ZeroToAll | [10_Smart_RAG.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/10_Smart_RAG.ipynb) | Explore how to use LangChain to build a Smart RAG system that can answer questions either from a given context or by searching the internet if the context is insufficient. It utilizes the UpstageEmbeddings model, the Tavily search API, and conditional logic to determine if a question can be answered from the context. If not, it searches Tavily and augments the context before providing the final answer. |
| Solar-LLM-ZeroToAll | [11_tool_RAG.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/11_tool_RAG.ipynb) | Learn how to building a Tool RAG system using LangChain, which can answer queries by intelligently selecting and utilizing different tools or data sources. |
| Solar-LLM-ZeroToAll | [12_summary_writing_translation.ipynb](https://github.com/UpstageAI/cookbook/blob/main/Solar-LLM-ZeroToAll/12_summary_writing_translation.ipynb) | This notebook shows using the LangChain library with the Upstage Embeddings model for various natural language processing tasks such as summarization, text simplification, and translation. It showcases how to create prompts and chains for summarizing text, rewriting text to be more understandable, translating English to Korean, and providing translations in a specific style by conditioning on examples. |
|  | [langgraph_self_rag.ipynb](https://github.com/UpstageAI/cookbook/blob/main/LangGraph-Self-RAG/langgraph_self_rag.ipynb) | This notebook provides a comprehensive guide on implementing Self Retrieval-Augmented-Generation (Self-RAG) using LangGraph. It demonstrates how to enhance text generation by integrating self-retrieval mechanisms, allowing the model to dynamically fetch relevant information to improve accuracy and relevance.  |
|  | [function_calling.ipynb](https://github.com/UpstageAI/cookbook/blob/main/function_calling.ipynb) | This notebook provides the most basic way to use function calling. |
|  | [llamaindex_rag.ipynb](https://github.com/UpstageAI/cookbook/blob/main/llamaindex_rag.ipynb) | In this notebook provides a comprehensive way to build a Retrieval-Augmented-Generation using the llama-index Upstage integration package. |

