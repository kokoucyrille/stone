"""Composants d'interface : barre de navigation, bandeau, cartes, états vides."""
from __future__ import annotations

import base64
import io
import os
from functools import lru_cache
from pathlib import Path

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


def banner_path() -> Path | None:
    """Photo du bandeau : TDI_BANNER, sinon le fichier assets/banner_lome.* le plus récent."""
    override = os.environ.get("TDI_BANNER")
    if override and Path(override).is_file():
        return Path(override)
    found = [p for ext in (".jpg", ".jpeg", ".png", ".webp")
             if (p := C.ASSETS_DIR / f"{C.BANNER_STEM}{ext}").is_file()]
    return max(found, key=lambda p: p.stat().st_mtime_ns) if found else None


@lru_cache(maxsize=4)
def _banner_uri(path: str, mtime_ns: int) -> str:
    """Photo redimensionnée (largeur max) et recompressée en JPEG, prête à être intégrée en CSS."""
    from PIL import Image, ImageOps
    try:
        with Image.open(path) as raw:
            img = ImageOps.exif_transpose(raw).convert("RGB")
        if img.width > C.BANNER_MAX_WIDTH:
            ratio = C.BANNER_MAX_WIDTH / img.width
            img = img.resize((C.BANNER_MAX_WIDTH, max(1, round(img.height * ratio))), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, "JPEG", quality=86, optimize=True)
    except Exception:  # image illisible : le bandeau reste sans photo, l'application démarre
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def icon(name: str, extra_class: str = "") -> str:
    """Icône Material Symbols (police fournie avec Streamlit)."""
    return f'<span class="msr {extra_class}" aria-hidden="true">{name}</span>'


def inject_css() -> None:
    css = (C.STYLES_DIR / "main.css").read_text(encoding="utf-8")
    photo = banner_path()
    uri = _banner_uri(str(photo), photo.stat().st_mtime_ns) if photo else ""
    banner_var = f'url("{uri}")' if uri else "none"
    css = css.replace("__BANNER_VAR__", banner_var).replace("__BANNER_POS__", C.BANNER_FOCUS)
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
def context_bar(f, cmp) -> None:
    """Rappelle la vue courante : période et filtres actifs, comparaison A / B en couleurs."""
    s = st.session_state
    groups = []
    if f.start is not None and s.get("f_periode") != s.get("_period_default"):
        label = str(f.start) if f.single_year else f"{f.start} – {f.end}"
        groups.append(("Période", f'<span class="ctx__chip">{html_escape(label)}</span>'))
    for dim, values in f.dims().items():
        name = C.DIM_LABELS[dim]
        if cmp.active and dim == cmp.dim:
            chips = '<span class="ctx__vs">contre</span>'.join(
                f'<span class="ctx__chip"><i style="background:{cmp.color(i)}"></i>{html_escape(v)}</span>'
                for i, v in enumerate(cmp.values)
            )
            groups.append((f"Comparaison · {name}", chips))
        else:
            chips = "".join(f'<span class="ctx__chip">{html_escape(v)}</span>' for v in values)
            groups.append((name + (" (cumul)" if len(values) > 1 else ""), chips))
    if not groups:
        return
    body = "".join(
        f'<span class="ctx__group"><span class="ctx__label">{html_escape(label)}</span>{chips}</span>'
        for label, chips in groups
    )
    st.markdown(
        f'<div class="ctx" role="status">{icon("tune")}<span class="ctx__title">Vue active</span>{body}</div>',
        unsafe_allow_html=True,
    )


def source_note(ds, f) -> None:
    """Ligne de sources en bas de page : fichiers utilisés, référence temporelle, mise à jour."""
    from datetime import datetime
    used = [fi for fi in ds.files if fi.dataset]
    if not used:
        return
    names = sorted({Path(fi.name).name for fi in used})
    shown = ", ".join(names[:4]) + (" …" if len(names) > 4 else "")
    parts = [f"Sources : {shown}"]
    if f.end:
        parts.append(f"Année de référence {f.end}"
                     + ("" if C.STOCK_MODE == "instantane" else " (valeurs cumulées)"))
    parts.append("Fichiers mis à jour le " + datetime.fromtimestamp(max(fi.modified for fi in used)).strftime("%d/%m/%Y"))
    st.markdown(
        f'<div class="srcnote">{icon("info")}<span>{html_escape(" · ".join(parts))}</span></div>',
        unsafe_allow_html=True,
    )


def card_title(mat_icon: str, title: str, note: str | None = None,
               link: str | None = None, key: str | None = None) -> None:
    """Titre de carte ; `link` = vue détaillée ouverte par le bouton « Détail »."""
    right = f'<span class="ct__note">{html_escape(note)}</span>' if note else ""
    head = (f'<div class="ct">{icon(mat_icon)}<span title="{html_escape(title)}">{html_escape(title)}</span>'
            f'{right}</div>')
    if not link:
        st.markdown(head, unsafe_allow_html=True)
        return
    label = {k: lab for k, lab, _ in C.PAGES}[link]
    with st.container(key=f"hdr_{key or link}"):
        st.markdown(head, unsafe_allow_html=True)
        st.button("Détail", icon=":material/arrow_forward:", key=f"go_{key or link}_{link}",
                  type="tertiary", on_click=_go, args=(link,), help=f"Ouvrir la vue « {label} »")


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
