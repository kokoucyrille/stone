"""Composants d'interface : barre de navigation, bandeau, cartes, états vides."""
from __future__ import annotations

import base64
from functools import lru_cache

import streamlit as st

from utils import config as C
from utils.formatting import html_escape


# --------------------------------------------------------------------------- #
# Ressources
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def _data_uri(filename: str, mime: str) -> str:
    raw = (C.ASSETS_DIR / filename).read_bytes()
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


@lru_cache(maxsize=None)
def _inline_svg(filename: str) -> str:
    return (C.ASSETS_DIR / filename).read_text(encoding="utf-8")


def icon(name: str, extra_class: str = "") -> str:
    """Icône Material Symbols (police fournie avec Streamlit)."""
    return f'<span class="msr {extra_class}" aria-hidden="true">{name}</span>'


def inject_css() -> None:
    css = (C.STYLES_DIR / "main.css").read_text(encoding="utf-8")
    css = css.replace("__BANNER__", _data_uri("banner_lome.jpg", "image/jpeg"))
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def plot(fig, key: str) -> None:
    """Affiche une figure Plotly sans barre d'outils, compatible multi-versions."""
    config = {"displayModeBar": False, "scrollZoom": False, "responsive": True}
    try:
        st.plotly_chart(fig, width="stretch", config=config, key=key)
    except TypeError:  # anciennes versions de Streamlit
        st.plotly_chart(fig, use_container_width=True, config=config, key=key)


# --------------------------------------------------------------------------- #
# Barre de navigation
# --------------------------------------------------------------------------- #
def _go(page: str) -> None:
    st.session_state["page"] = page


def topbar() -> str:
    page = st.session_state.setdefault("page", C.PAGES[0][0])
    brand = (
        '<div class="brand">'
        f'<span class="brand__logo">{_inline_svg("logo.svg")}</span>'
        '<div class="brand__text">'
        f'<div class="brand__title">{html_escape(C.APP_TITLE)}</div>'
        f'<div class="brand__sub">{html_escape(C.APP_SUBTITLE)}</div>'
        "</div></div>"
    )
    flag = (
        '<div class="flag">'
        f'<img src="{_data_uri("flag_togo.svg", "image/svg+xml")}" alt="Drapeau du Togo"/>'
        f'<span>{html_escape(C.MOTTO)}</span></div>'
    )
    with st.container(key="topbar"):
        widths = [31, 13.5, 9.5, 9.5, 11.5, 10.5, 14.5]
        cols = st.columns(widths, vertical_alignment="center")
        cols[0].markdown(brand, unsafe_allow_html=True)
        for col, (key, label, mat) in zip(cols[1:6], C.PAGES):
            col.button(
                label, icon=f":material/{mat}:", key=f"nav_{key}",
                type="primary" if key == page else "tertiary",
                on_click=_go, args=(key,),
            )
        cols[6].markdown(flag, unsafe_allow_html=True)
    return st.session_state["page"]


# --------------------------------------------------------------------------- #
# Bandeau
# --------------------------------------------------------------------------- #
def hero() -> None:
    l1, l2, l3 = C.SLOGAN_LINES
    stripes = (
        '<svg class="hero__stripes" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">'
        '<polygon points="34.6,100 41.6,0 44.2,0 37.2,100" fill="#2E9B57" opacity=".9"/>'
        '<polygon points="37.2,100 44.2,0 47.4,0 40.4,100" fill="#FFCE00"/>'
        '<polygon points="40.4,100 47.4,0 49,0 42,100" fill="#D21034"/>'
        "</svg>"
    )
    st.markdown(
        '<div class="hero"><div class="hero__circuit"></div><div class="hero__photo"></div>'
        f"{stripes}"
        f'<div class="hero__text"><span>{html_escape(l1)}</span><span>{html_escape(l2)}</span>'
        f'<span class="y">{html_escape(l3)}</span></div></div>',
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="page-head"><h1>{html_escape(title)}</h1>'
        f"<p>{html_escape(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Cartes et états vides
# --------------------------------------------------------------------------- #
def compare_bar(cmp) -> None:
    """Bandeau discret rappelant les deux valeurs comparées et leurs couleurs."""
    if not cmp.active:
        return
    chips = "".join(
        f'<span class="cmp__chip"><i style="background:{cmp.color(i)}"></i>{html_escape(v)}</span>'
        for i, v in enumerate(cmp.values)
    )
    extra = ""
    if cmp.extra:
        extra = ('<span class="cmp__note">Autres champs à 2 valeurs, cumulés : '
                 f'{html_escape(", ".join(cmp.extra))}</span>')
    st.markdown(
        f'<div class="cmp">{icon("compare_arrows")}<span class="cmp__title">Comparaison · '
        f'{html_escape(cmp.label)}</span>{chips}{extra}</div>',
        unsafe_allow_html=True,
    )


def card_title(mat_icon: str, title: str, note: str | None = None) -> None:
    right = f'<span class="ct__note">{html_escape(note)}</span>' if note else ""
    st.markdown(
        f'<div class="ct">{icon(mat_icon)}<span>{html_escape(title)}</span>{right}</div>',
        unsafe_allow_html=True,
    )


def empty_state(height: int, title: str = "Données non disponibles", hint: str = "") -> None:
    hint_html = f"<small>{html_escape(hint)}</small>" if hint else ""
    st.markdown(
        f'<div class="empty" style="min-height:{height}px">{icon("insert_chart")}'
        f"<b>{html_escape(title)}</b>{hint_html}</div>",
        unsafe_allow_html=True,
    )


def missing_hint(dataset: str, *columns: str) -> str:
    cols = ", ".join(columns)
    return f"Requis : data/{dataset} › {cols}"


def notice(message: str) -> None:
    st.markdown(f'<div class="notice">{icon("info")}<span>{message}</span></div>',
                unsafe_allow_html=True)


def legend(rows: list[tuple[str, str, str, str]], cls: str = "") -> str:
    """Légende HTML : (couleur, libellé, valeur, part)."""
    items = []
    for color, label, value, part in rows:
        items.append(
            f'<div class="lg__row"><i style="background:{color}"></i>'
            f'<span class="lg__name">{html_escape(label)}</span>'
            f'<span class="lg__val">{value}</span><span class="lg__part">{part}</span></div>'
        )
    return f'<div class="lg {cls}">{"".join(items)}</div>'


def show_table(df, height: int | None = None) -> None:
    """Tableau interactif sans index, pleine largeur, compatible multi-versions."""
    kwargs = {"hide_index": True}
    if height:  # hauteur plafonnée, ajustée au nombre de lignes
        kwargs["height"] = min(height, 42 + 36 * len(df))
    try:
        st.dataframe(df, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kwargs)
