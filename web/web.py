import reflex as rx

from . import styles
from .pages import *

app = rx.App(
    style=styles.base_style,
    stylesheets=styles.base_stylesheets,
)
