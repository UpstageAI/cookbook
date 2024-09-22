import reflex as rx

from .. import styles
from .utils import footer, render_accordian_items


def sidebar_header() -> rx.Component:
    return rx.hstack(
        rx.link(
            rx.color_mode_cond(
                rx.image(src="/upstage_black.png", height="2.5em"),
                rx.image(src="/upstage_white.png", height="2.5em"),
            ),
            href="/",
        ),
        rx.spacer(),
        align="center",
        width="100%",
        padding="0.35em",
        margin_bottom="1em",
    )


def sidebar() -> rx.Component:
    return rx.flex(
        rx.vstack(
            sidebar_header(),
            rx.vstack(
                render_accordian_items(),
                spacing="1",
                width="100%",
            ),
            rx.spacer(),
            footer(),
            justify="end",
            align="end",
            width=styles.sidebar_content_width,
            height="100dvh",
            padding="1em",
        ),
        display=["none", "none", "none", "none", "none", "flex"],
        max_width=styles.sidebar_width,
        width="auto",
        height="100%",
        position="sticky",
        justify="end",
        top="0px",
        left="0px",
        flex="1",
        bg=rx.color("gray", 2),
    )
