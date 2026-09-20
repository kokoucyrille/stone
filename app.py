"""TOGO DIGITAL INTELLIGENCE — plateforme d'intelligence territoriale.

Lancement :  streamlit run app.py
"""
import streamlit as st
from PIL import Image

from utils import config as C

def _page_icon():
    """Icône d'onglet : drapeau du Togo ou logo (TDI_FAVICON=flag|logo)."""
    path = C.ASSETS_DIR / C.FAVICON_FILES.get(C.FAVICON, C.FAVICON_FILES["flag"])
    return Image.open(path) if path.is_file() else ":material/hub:"


st.set_page_config(
    page_title="Togo Digital Intelligence",
    page_icon=_page_icon(),
    layout="wide",
    initial_sidebar_state="auto",
)

from components import layout  # noqa: E402  (après set_page_config)
from utils.data_loader import load_datasets  # noqa: E402
from utils import state  # noqa: E402
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
    state.restore(set(VIEWS))            # lien partagé ou rafraîchissement : vue restituée
    page = layout.topbar()
    datasets = load_datasets()
    filters = render_sidebar(datasets)
    VIEWS.get(page, dashboard.render)(datasets, filters)
    layout.source_note(datasets, filters)
    state.sync(page)                     # l'adresse du navigateur reflète la vue


main()
