"""Blocs réutilisables par toutes les vues."""
from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st

from components import charts
from components.layout import empty_state, legend, plot
from utils import config as C
from utils.formatting import fmt_int, fmt_pct

NO_RESULT = "Aucun résultat pour ces filtres"


def is_missing(data) -> bool:
    return data is None


def is_empty(data) -> bool:
    return data is not None and len(data) == 0


def chart_block(data, height: int, builder: Callable, key: str, hint: str) -> None:
    """Affiche le graphique, ou un état vide de même hauteur."""
    if is_missing(data):
        empty_state(height, hint=hint)
    elif is_empty(data):
        empty_state(height, NO_RESULT)
    else:
        plot(builder(data), key)


def donut_block(data: pd.DataFrame | None, key: str, hint: str, height: int = 200,
                center_label: str = "entreprises") -> None:
    """Anneau + légende (libellé, part) côte à côte."""
    if data is None or len(data) == 0:
        empty_state(height, hint=hint if data is None else "", **({} if data is None else {"title": NO_RESULT}))
        return
    left, right = st.columns([50, 50], vertical_alignment="center")
    with left:
        chart_block(data, height, lambda d: charts.donut(d, center_label, height), key, hint)
    with right:
        if data is not None and len(data):
            colors = charts.sector_colors(list(data["label"]))
            rows = [(c, r.label, "", fmt_pct(r.part)) for c, r in zip(colors, data.itertuples())]
            st.markdown(legend(rows, "lg--donut"), unsafe_allow_html=True)


def region_legend(regions: pd.DataFrame, value_format=fmt_int) -> str:
    rows = []
    for i, r in enumerate(regions.itertuples()):
        part = f"({fmt_pct(r.part)})" if hasattr(r, "part") else ""
        rows.append((charts.region_color(r.label, i), r.label, value_format(r.valeur), part))
    return legend(rows, "lg--region")


def page_intro(ds) -> None:
    """Message discret lorsque aucun fichier de données n'est détecté."""
    from components.layout import notice
    if ds.empty:
        notice(
            "Aucune donnée détectée. Déposez vos fichiers dans "
            "<b>data/</b> (voir <b>data/README.md</b>) : les indicateurs et graphiques "
            "se remplissent automatiquement, sans valeur simulée."
        )


def missing(dataset: str, *columns: str) -> str:
    return f"Requis : data/{dataset} › {', '.join(columns)}"


ENTREPRISES_REGION_HINT = missing("entreprises", "region", "nombre")
