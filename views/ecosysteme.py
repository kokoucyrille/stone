"""Vue « Écosystème » : acteurs, statuts, tailles et croisements avec les secteurs."""
from __future__ import annotations

import streamlit as st

from components import charts
from components.layout import card_title, page_header
from utils import metrics as M
from utils.data_loader import Datasets
from utils.filters import Filters

from .common import chart_block, donut_block, missing, page_intro


def render(ds: Datasets, f: Filters) -> None:
    page_header("Écosystème", "Acteurs du numérique : types, statuts et tailles.")
    page_intro(ds)

    a, b, c = st.columns(3, gap="small")
    with a:
        with st.container(key="card_eco_type"):
            card_title("hub", "Répartition par type d'acteur")
            donut_block(M.group_count(ds, f, "type_acteur"), "eco_type",
                        missing("entreprises", "type_acteur", "nombre"), 210, "acteurs")
    with b:
        with st.container(key="card_eco_statut"):
            card_title("verified", "Répartition par statut")
            donut_block(M.group_count(ds, f, "statut"), "eco_statut",
                        missing("entreprises", "statut", "nombre"), 210, "acteurs")
    with c:
        with st.container(key="card_eco_taille"):
            card_title("apartment", "Répartition par taille")
            chart_block(M.group_count(ds, f, "taille"), 210, lambda d: charts.top_bars(d, 210),
                        "eco_taille", missing("entreprises", "taille", "nombre"))

    with st.container(key="card_eco_cross"):
        card_title("grid_on", "Types d'acteurs par secteur d'activité")
        chart_block(M.cross_table(ds, f, "type_acteur", "secteur"), 320,
                    lambda t: charts.heatmap(t, 320), "eco_cross",
                    missing("entreprises", "type_acteur", "secteur", "nombre"))
