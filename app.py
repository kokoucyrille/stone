"""TOGO DIGITAL INTELLIGENCE — plateforme d'intelligence territoriale.

Lancement :  streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Togo Digital Intelligence",
    page_icon=":material/hub:",
    layout="wide",
    initial_sidebar_state="auto",
)

from components import layout  # noqa: E402  (après set_page_config)
from utils.data_loader import load_datasets  # noqa: E402
from utils.filters import render_sidebar  # noqa: E402
from views import dashboard, ecosysteme, infrastructures, secteurs, territoires  # noqa: E402

VIEWS = {
    "dashboard": dashboard.render,
    "territoires": territoires.render,
    "secteurs": secteurs.render,
    "infrastructures": infrastructures.render,
    "ecosysteme": ecosysteme.render,
}


def main() -> None:
    layout.inject_css()
    page = layout.topbar()
    datasets = load_datasets()
    filters = render_sidebar(datasets)
    VIEWS.get(page, dashboard.render)(datasets, filters)


main()
