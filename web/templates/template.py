"""Common templates used between pages in the app."""

from typing import Callable, List, Optional, Union

import reflex as rx

from .. import styles
from ..components.navbar import navbar
from ..components.sidebar import sidebar

# Meta tags for the app.
default_meta = [
    {
        "name": "viewport",
        "content": "width=device-width, shrink-to-fit=no, initial-scale=1",
    },
]


class ThemeState(rx.State):
    accent_color: str = "purple"
    gray_color: str = "gray"
    radius: str = "large"
    scaling: str = "100%"


def template(
    route: Optional[str] = None,
    title: str = "Cookbook",
    description: Optional[str] = None,
    meta: Optional[str] = None,
    script_tags: Optional[list[rx.Component]] = None,
    on_load: Optional[Union[rx.event.EventHandler, List[rx.event.EventHandler]]] = None,
) -> Callable[[Callable[[], rx.Component]], rx.Component]:
    if route.lstrip("/"):
        title = f"{title} | {route.lstrip("/")}"

    def decorator(page_content: Callable[[], rx.Component]) -> rx.Component:
        all_meta = [*default_meta, *(meta or [])]

        def templated_page():
            return rx.flex(
                navbar(),
                sidebar(),
                rx.flex(
                    rx.vstack(
                        page_content(),
                        width="100%",
                        **styles.template_content_style,
                    ),
                    width="100%",
                    **styles.template_page_style,
                    max_width=[
                        "100%",
                        "100%",
                        "100%",
                        "100%",
                        "100%",
                        styles.max_width,
                    ],
                ),
                flex_direction=[
                    "column",
                    "column",
                    "column",
                    "column",
                    "column",
                    "row",
                ],
                width="100%",
                margin="auto",
                position="relative",
            )

        @rx.page(
            route=route,
            title=title,
            description=description,
            meta=all_meta,
            script_tags=script_tags,
            on_load=on_load,
        )
        def theme_wrap():
            return rx.theme(
                templated_page(),
                has_background=True,
                accent_color=ThemeState.accent_color,
                gray_color=ThemeState.gray_color,
                radius=ThemeState.radius,
                scaling=ThemeState.scaling,
            )

        return theme_wrap

    return decorator
