from typing import Dict

import reflex as rx


class NotebookState(rx.State):
    """{text on link: router path}"""

    # Upstage
    # Upstage: Dict[str, str] = {
    #     "function_calling": "function_calling",
    #     "financial_analysis": "financial_analysis",
    #     "how_to_count_token": "how_to_count_token",
    #     "llamaindex_rag": "llamaindex_rag",
    #     "upstage": "upstage",
    # }

    # Solar Full stack LLM
    Solar_LLM: Dict[str, str] = {
        "README": "README",
        "hello_solar": "hello_solar",
        "prompt_engineering": "prompt_engineering",
        "summary_writing_translation": "summary_writing_translation",
        "chat_with_history": "chat_with_history",
        "docvision": "docvision",
        "reasoning": "reasoning",
        "auto_marketing": "auto_marketing",
        "auto_filling": "auto_filling",
        "contract_advising": "contract_advising",
        "fact_check_with_kg": "fact_check_with_kg",
        "all": "all",
        "all_edu": "all_edu",
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
        "langgraph_self_rag": "langgraph_self_rag",
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
