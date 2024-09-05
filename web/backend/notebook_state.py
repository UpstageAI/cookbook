from typing import Dict

import reflex as rx


class NotebookState(rx.State):
    """{text on link: router path}"""

    # Upstage
    Upstage: Dict[str, str] = {
        "function_calling": "function_calling",
        "financial_analysis": "financial_analysis",
        "how_to_count_token": "how_to_count_token",
        "llamaindex_rag": "llamaindex_rag",
        "upstage": "upstage",
    }

    # LangGraph
    LangGraph_Self_RAG: Dict[str, str] = {"langgraph_self_rag": "langgraph_self_rag"}

    # Solar Full stack LLM
    Solar_LLM: Dict[str, str] = {
        "README": "README",
        "hello_solar": "hello_solar",
        "prompt_engineering": "prompt_engineering",
        "summary_writing_translation": "summary_writing_translation",
        "chat_with_history": "chat_with_history",
        "all_edu": "all_edu",
        "all": "all",
    }

    Solar_RAG: Dict[str, str] = {
        "hallucinations": "hallucinations",
        "CAG_GC": "CAG_GC",
        "ChromaDB": "ChromaDB",
        "MongoDB": "MongoDB",
        "OracleDB": "OracleDB",
        "PDF_CAG": "PDF_CAG",
        "LA_CAG": "LA_CAG",
        "RAG": "RAG",
        "Smart_RAG": "Smart_RAG",
        "tool_RAG": "tool_RAG",
    }

    Gradio: Dict[str, str] = {
        "gradio": "gradio",
        "gradio_stream": "gradio_stream",
        "gradio_chatpdf": "gradio_chatpdf",
    }

    @classmethod
    def get_keys(cls):
        return list(cls.__annotations__.keys())

    @classmethod
    def get_values(cls):
        return [getattr(cls, key) for key in cls.get_keys()]
