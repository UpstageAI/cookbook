"""All pages made with .md, .ipynb"""

import os

from .common import create_route_component
from .utils import to_solar_path

# index
index = create_route_component(route="/", file_path="README.md")

# root
# function_calling = create_route_component(
#     route="/function_calling",
#     file_path="function_calling.ipynb",
# )
# financial_analysis = create_route_component(
#     route="/financial_analysis",
#     file_path="financial_analysis.ipynb",
# )
# how_to_count_token = create_route_component(
#     route="/how_to_count_token",
#     file_path="how_to_count_token.ipynb",
# )
# llamaindex_rag = create_route_component(
#     route="/llamaindex_rag",
#     file_path="llamaindex_rag.ipynb",
# )
# upstage = create_route_component(
#     route="/upstage",
#     file_path="upstage.ipynb",
# )

# upstage/solar-hull-stack-llm-101
readme = create_route_component(
    route="/README",
    file_path=to_solar_path("README.md"),
)
hello_solar = create_route_component(
    route="/hello_solar",
    file_path=to_solar_path("01_hello_solar.ipynb"),
)
prompt_engineering = create_route_component(
    route="/prompt_engineering",
    file_path=to_solar_path("02_prompt_engineering.ipynb"),
)
hallucinations = create_route_component(
    route="/hallucinations",
    file_path=to_solar_path("03_hallucinations.ipynb"),
)
cag_gc = create_route_component(
    route="/CAG_GC",
    file_path=to_solar_path("04_CAG_GC.ipynb"),
)
chromadb = create_route_component(
    route="/ChromaDB",
    file_path=to_solar_path("05_1_ChromaDB.ipynb"),
)
mongodb = create_route_component(
    route="/MongoDB",
    file_path=to_solar_path("05_2_MongoDB.ipynb"),
)
oracledb = create_route_component(
    route="/OracleDB",
    file_path=to_solar_path("05_3_OracleDB.ipynb"),
)
pdf_cag = create_route_component(
    route="/PDF_CAG",
    file_path=to_solar_path("06_PDF_CAG.ipynb"),
)
la_cag = create_route_component(
    route="/LA_CAG",
    file_path=to_solar_path("07_LA_CAG.ipynb"),
)
rag = create_route_component(
    route="/RAG",
    file_path=to_solar_path("08_RAG.ipynb"),
)
smart_rag = create_route_component(
    route="/Smart_RAG",
    file_path=to_solar_path("09_1_Smart_RAG.ipynb"),
)
langgraph_self_rag = create_route_component(
    route="/langgraph_self_rag",
    file_path=to_solar_path("09_2_langgraph_self_RAG.ipynb"),
)
tool_rag = create_route_component(
    route="/tool_RAG",
    file_path=to_solar_path("10_tool_RAG.ipynb"),
)
summary_writing_translation = create_route_component(
    route="/summary_writing_translation",
    file_path=to_solar_path("11_summary_writing_translation.ipynb"),
)
chat_with_history = create_route_component(
    route="/chat_with_history",
    file_path=to_solar_path("12_chat_with_history.ipynb"),
)
docvision = create_route_component(
    route="/docvision",
    file_path=to_solar_path("13_docvision.ipynb"),
)
reasoning = create_route_component(
    route="/reasoning",
    file_path=to_solar_path("14_Reasoning.ipynb"),
)
auto_marketing = create_route_component(
    route="/auto_marketing",
    file_path=to_solar_path("15_auto_marketing.ipynb"),
)
auto_filling = create_route_component(
    route="/auto_filling",
    file_path=to_solar_path("16_auto_filling.ipynb"),
)
contract_advising = create_route_component(
    route="/contract_advising",
    file_path=to_solar_path("17_contract_advising.ipynb"),
)
fact_check_with_kg = create_route_component(
    route="/fact_check_with_kg",
    file_path=to_solar_path("18_fact_check_with_kg.ipynb"),
)
gradio = create_route_component(
    route="/gradio",
    file_path=to_solar_path("80_gradio.ipynb"),
)
gradio_stream = create_route_component(
    route="/gradio_stream",
    file_path=to_solar_path("81_gradio_stream.ipynb"),
)
gradio_chatpdf = create_route_component(
    route="/gradio_chatpdf",
    file_path=to_solar_path("82_gradio_chatpdf.ipynb"),
)
all_edu = create_route_component(
    route="/all_edu",
    file_path=to_solar_path("98_all_edu.ipynb"),
)
all = create_route_component(
    route="/all",
    file_path=to_solar_path("99_all.ipynb"),
)
