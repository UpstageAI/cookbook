import json
import os
from typing import Dict, List, Optional

import plotly.graph_objs as go
import reflex as rx
import requests

from ..templates import template
from .utils import convert_local_image_paths, format_code_lint, is_url, strip_ansi_codes

BASE_RAW_PATH = os.getcwd()
BASE_IMAGE_PATH = (
    "https://raw.githubusercontent.com/UpstageAI/cookbook/main/Solar-Fullstack-LLM-101/"
)


def _read_jupyter(path: str) -> List[Dict]:
    if is_url(path=path):
        response = requests.get(path)
        notebook = response.json()
    else:
        with open(path, "r", encoding="utf-8") as file:
            notebook = json.load(file)
    return notebook["cells"]


def _render_output(output: Dict) -> rx.Component:
    output_type = output["output_type"]
    if output_type == "stream":
        return rx.text("".join(output.get("text", "")), color="gray")
    elif output_type in {"display_data", "execute_result"}:
        data = output.get("data", {})
        if "text/plain" in data:
            return rx.text("".join(data["text/plain"]))
        if "text/html" in data:
            return rx.html("".join(data["text/html"]))
        if "image/png" in data:
            return rx.image(src=f"data:image/png;base64,{data['image/png']}")
        if "application/vnd.plotly.v1+json" in data:
            return rx.plotly(data=go.Figure(data.get("application/vnd.plotly.v1+json")))
    elif output_type == "error":
        cleaned_message = strip_ansi_codes("<br>".join(output.get("traceback", [])))
        return rx.markdown(cleaned_message, color="red")
    return rx.text("Unsupported output type")


def _style_cell(cell: dict, image_base_path: Optional[str]) -> rx.Component:
    cell_type = cell.get("cell_type", "unknown")
    content = "".join(cell.get("source", ""))
    if len(content) == 0:
        return rx.spacer(spacing="0")

    components = []
    if cell_type == "code":
        components.append(
            rx.code_block(
                format_code_lint(content),
                language="python",
                show_line_numbers=True,
                can_copy=True,
                width="100%",
            )
        )
        for output in cell.get("outputs", []):
            components.append(_render_output(output))
    elif cell_type == "markdown":
        components.append(
            rx.markdown(
                convert_local_image_paths(
                    markdown_text=content, image_base_path=image_base_path
                ),
            )
        )
    else:
        components.append(rx.text("Unsupported cell type"))
    return rx.vstack(*components)


def read_jupyter(path: str, image_base_path: Optional[str] = None) -> rx.Component:
    _cells = _read_jupyter(path=path)
    return rx.vstack(
        *[_style_cell(cell=cell, image_base_path=image_base_path) for cell in _cells],
        width="100%",
    )


def read_markdown(path: str) -> str:
    if is_url(path=path):
        response = requests.get(path)
        content = response.text
    else:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
    return content


def create_route_component(route: str, file_path: str, **kwargs) -> rx.Component:
    @template(route=route, **kwargs)
    def dynamic_component() -> rx.Component:
        try:
            _file_path = os.path.abspath(os.path.join(BASE_RAW_PATH, file_path))
            if file_path.endswith(".ipynb"):
                return read_jupyter(path=_file_path, image_base_path=BASE_IMAGE_PATH)

            if file_path.endswith(".md"):
                return rx.markdown(
                    convert_local_image_paths(
                        markdown_text=read_markdown(path=_file_path),
                        image_base_path=BASE_IMAGE_PATH,
                    )
                )
            return rx.markdown("")
        except Exception as e:
            rx.markdown(str(e))

    return dynamic_component
