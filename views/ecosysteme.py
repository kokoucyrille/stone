"""Vue « Écosystème » : acteurs, statuts, tailles et croisements avec les secteurs."""
from __future__ import annotations

import streamlit as st

from components import charts
from components.layout import card_title, compare_bar, page_header
from utils import metrics as M
from utils.compare import get_comparison
from utils.data_loader import Datasets
from utils.filters import Filters

from .common import chart_block, donut_block, grouped_block, missing, page_intro


def render(ds: Datasets, f: Filters) -> None:
    page_header("Écosystème", "Acteurs du numérique : types, statuts et tailles.")
    page_intro(ds)
    cmp = get_comparison(f)
    compare_bar(cmp)

    a, b, c = st.columns(3, gap="small")
    with a:
        with st.container(key="card_eco_type"):
            card_title("hub", "Répartition par type d'acteur")
            hint = missing("entreprises", "type_acteur", "nombre")
            if cmp.is_split("type_acteur"):
                grouped_block(ds, f, cmp, "type_acteur", 224, "eco_type_cmp", hint, top=6)
            else:
                donut_block(M.group_count(ds, f, "type_acteur"), "eco_type", hint, 210, "acteurs")
    with b:
        with st.container(key="card_eco_statut"):
            card_title("verified", "Répartition par statut")
            hint = missing("entreprises", "statut", "nombre")
            if cmp.is_split("statut"):
                grouped_block(ds, f, cmp, "statut", 224, "eco_statut_cmp", hint, top=6)
            else:
                donut_block(M.group_count(ds, f, "statut"), "eco_statut", hint, 210, "acteurs")
    with c:
        with st.container(key="card_eco_taille"):
            card_title("apartment", "Répartition par taille")
            hint = missing("entreprises", "taille", "nombre")
            if cmp.is_split("taille"):
                grouped_block(ds, f, cmp, "taille", 224, "eco_taille_cmp", hint, top=6)
            else:
                chart_block(M.group_count(ds, f, "taille"), 210,
                            lambda d: charts.top_bars(d, 210), "eco_taille", hint)

    with st.container(key="card_eco_cross"):
        card_title("grid_on", "Types d'acteurs par secteur d'activité",
                   "Sélections cumulées" if cmp.active else None)
        chart_block(M.cross_table(ds, f, "type_acteur", "secteur"), 320,
                    lambda t: charts.heatmap(t, 320), "eco_cross",
                    missing("entreprises", "type_acteur", "secteur", "nombre"))
