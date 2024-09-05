from typing import Dict, List

import reflex as rx

from ..backend.notebook_state import NotebookState


def document_link(info: List[str]) -> rx.Component:
    return rx.link(
        rx.text(info[0], size="2"),
        href=info[1],
        underline="none",
        weight="medium",
        width="100%",
    )


def accordian_item(
    text: str,
    state: Dict[str, str],
) -> rx.Component:
    return rx.accordion.item(
        header=rx.hstack(rx.icon("folder", size=20), rx.text(text, size="2")),
        content=rx.vstack(
            rx.foreach(
                state,
                document_link,
            )
        ),
    )


def accordian_items(texts: List[str], states: List[Dict[str, str]]):
    _items = []
    for text, state in zip(texts, states):
        _items.append(accordian_item(text=text, state=state))
    return rx.accordion.root(
        *_items,
        collapsible=True,
        type="multiple",
        variant="ghost",
    )


def render_accordian_items() -> rx.Component:
    return rx.vstack(
        accordian_items(
            texts=NotebookState.get_keys(),
            states=NotebookState.get_values(),
        ),
        spacing="1",
        width="100%",
        align="left",
    )


def footer() -> rx.Component:
    return rx.hstack(
        rx.link(
            rx.text("GitHub", size="3"),
            href="https://github.com/UpstageAI/cookbook",
            color_scheme="gray",
            underline="none",
        ),
        rx.link(
            rx.text("Discord", size="3"),
            href="https://discord.gg/BYtHbQpk",
            color_scheme="gray",
            underline="none",
        ),
        rx.spacer(),
        rx.color_mode.button(style={"opacity": "0.8", "scale": "0.95"}),
        justify="start",
        align="center",
        width="100%",
        padding="0.35em",
    )
