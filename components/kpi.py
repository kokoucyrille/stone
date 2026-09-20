"""Cartes KPI épurées (style Power BI) et blocs de synthèse compacts.

Chaque carte contient uniquement : icône, libellé, valeur, variation.
Aucune courbe, sparkline ni mini-graphique.
"""
from __future__ import annotations

import streamlit as st

from utils import config as C
from utils.formatting import fmt_int, fmt_signed, html_escape
from utils.metrics import Kpi, format_kpi_value

from .layout import icon


def kpi_row(kpis: list[Kpi]) -> None:
    cards = []
    for k in kpis:
        if k.value is None:
            delta = '<div class="kpi__delta kpi__delta--na">Donnée non disponible</div>'
        elif k.delta is not None:
            direction = "up" if k.delta >= 0 else "down"
            arrow = "trending_up" if k.delta >= 0 else "trending_down"
            delta = (
                f'<div class="kpi__delta kpi__delta--{direction}">{icon(arrow)}'
                f"<b>{fmt_signed(k.delta, 1, k.delta_unit)}</b></div>"
                f'<div class="kpi__ref">{html_escape(k.delta_label or "")}</div>'
            )
        else:
            delta = ""
        cards.append(
            f'<div class="kpi kpi--{k.tone}">'
            f'<div class="kpi__icon">{icon(k.icon)}</div>'
            '<div class="kpi__body">'
            f'<div class="kpi__label">{html_escape(k.label)}</div>'
            f'<div class="kpi__value">{format_kpi_value(k)}</div>'
            f"{delta}</div></div>"
        )
    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def infra_strip(tiles: list[tuple[str, float, str]] | None) -> None:
    """Bloc « Répartition des infrastructures numériques » : icône, libellé, valeur."""
    if tiles is None:
        tiles = [(label, None, icon_name) for label, _, icon_name in C.INFRA_TILES]
    items = []
    for label, value, mat in tiles:
        shown = "—" if value is None else fmt_int(value)
        items.append(
            '<div class="tile">'
            f'<span class="tile__icon">{icon(mat)}</span>'
            f'<div class="tile__text"><div class="tile__label">{html_escape(label)}</div>'
            f'<div class="tile__value">{shown}</div></div></div>'
        )
    cols = max(1, min(len(tiles), 5))
    st.markdown(f'<div class="strip" style="--cols:{cols}">{"".join(items)}</div>',
                unsafe_allow_html=True)


def indicators_strip(tiles: list[tuple[str, str, str]]) -> None:
    """Bloc « Indicateurs clés » : uniquement les indicateurs disponibles."""
    items = []
    for label, text, mat in tiles:
        items.append(
            '<div class="tile tile--ind">'
            f'<div class="tile__head"><span class="tile__icon">{icon(mat)}</span>'
            f'<span class="tile__label">{html_escape(label)}</span></div>'
            f'<div class="tile__value tile__value--green">{html_escape(text)}</div></div>'
        )
    st.markdown(f'<div class="strip strip--ind" style="--cols:{len(items)}">{"".join(items)}</div>',
                unsafe_allow_html=True)
