"""Vue « Secteurs » : poids, dynamique et détail par secteur d'activité."""
from __future__ import annotations

import streamlit as st

from components import charts
from components.layout import card_title, empty_state, page_header, show_table
from utils import metrics as M
from utils.data_loader import Datasets
from utils.filters import Filters

from .common import NO_RESULT, chart_block, donut_block, missing, page_intro

HINT = missing("entreprises", "secteur", "nombre")


def render(ds: Datasets, f: Filters) -> None:
    page_header("Secteurs", "Poids et dynamique des secteurs d'activité du numérique.")
    page_intro(ds)

    a, b = st.columns([45, 55], gap="small")
    with a:
        with st.container(key="card_sec_donut"):
            card_title("donut_large", "Répartition par secteur d'activité")
            donut_block(M.by_sector(ds, f, top=7), "sec_donut", HINT, 250)
    with b:
        with st.container(key="card_sec_bars"):
            card_title("bar_chart", "Entreprises par secteur")
            data = M.group_count(ds, f, "secteur")
            if data is not None:
                data = data.sort_values("valeur", ascending=False).head(8).reset_index(drop=True)
            chart_block(data, 250, lambda d: charts.top_bars(d, 250), "sec_bars", HINT)

    c, d = st.columns([55, 45], gap="small")
    with c:
        with st.container(key="card_sec_evo"):
            card_title("show_chart", "Évolution par secteur")
            table = M.stock_by_year(ds, f, "secteur")
            if table is not None and not table.empty:
                top = table.iloc[-1].sort_values(ascending=False).head(5).index
                table = table[list(top)]
            chart_block(table, 300, lambda t: charts.multi_line(t, 300), "sec_evo",
                        missing("entreprises", "secteur", "annee", "nombre"))
    with d:
        with st.container(key="card_sec_table"):
            card_title("table_chart", "Détail par secteur")
            summary = M.summary_table(ds, f, "secteur")
            if summary is None:
                empty_state(300, hint=HINT)
            elif summary.empty:
                empty_state(300, NO_RESULT)
            else:
                show_table(summary.rename(columns={"secteur": "Secteur"}), height=320)
