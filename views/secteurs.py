"""Vue « Secteurs » : poids, dynamique et détail par secteur d'activité."""
from __future__ import annotations

import streamlit as st

from components import charts
from components.layout import card_title, compare_bar, empty_state, page_header, plot, show_table
from utils import metrics as M
from utils.compare import by_series, get_comparison, stack_tables, supports
from utils.data_loader import Datasets
from utils.filters import Filters

from .common import (NO_RESULT, chart_block, compare_data, donut_block, grouped_block, missing,
                     page_intro)

HINT = missing("entreprises", "secteur", "nombre")


def render(ds: Datasets, f: Filters) -> None:
    page_header("Secteurs", "Poids et dynamique des secteurs d'activité du numérique.")
    page_intro(ds)
    cmp = get_comparison(f)
    compare_bar(cmp)
    split = cmp.is_split("secteur")

    a, b = st.columns([45, 55], gap="small")
    with a:
        with st.container(key="card_sec_donut"):
            card_title("donut_large", "Répartition par secteur d'activité")
            if split:
                grouped_block(ds, f, cmp, "secteur", 250, "sec_abs", HINT, top=7)
            else:
                donut_block(M.by_sector(ds, f, top=7), "sec_donut", HINT, 250)
    with b:
        with st.container(key="card_sec_bars"):
            card_title("bar_chart", "Poids relatif par secteur (%)" if split else "Entreprises par secteur")
            if split:
                grouped_block(ds, f, cmp, "secteur", 250, "sec_rel", HINT, top=7, percent=True)
            else:
                data = M.group_count(ds, f, "secteur")
                if data is not None:
                    data = data.sort_values("valeur", ascending=False).head(8).reset_index(drop=True)
                chart_block(data, 250, lambda d: charts.top_bars(d, 250), "sec_bars", HINT)

    c, d = st.columns([55, 45], gap="small")
    with c:
        with st.container(key="card_sec_evo"):
            card_title("show_chart", "Évolution par sélection" if split else "Évolution par secteur")
            evo_hint = missing("entreprises", "secteur", "annee", "nombre")
            if split:
                parts = compare_data(ds, f, cmp, M.evolution, "entreprises", 300, evo_hint)
                if parts is not None:
                    usable = {k: v for k, v in parts.items() if v is not None and len(v)}
                    plot(charts.compare_lines(usable, cmp.color_map(), 300), "sec_evo_cmp")
            else:
                table = M.stock_by_year(ds, f, "secteur")
                if table is not None and not table.empty:
                    top = table.iloc[-1].sort_values(ascending=False).head(5).index
                    table = table[list(top)]
                chart_block(table, 300, lambda t: charts.multi_line(t, 300), "sec_evo", evo_hint)
    with d:
        with st.container(key="card_sec_table"):
            card_title("table_chart", "Détail par secteur")
            if split:
                if not supports(ds, "entreprises", cmp.dim):
                    empty_state(300, "Comparaison non applicable",
                                hint=f"Le champ « {cmp.label} » est absent de data/entreprises")
                    return
                summary = stack_tables(by_series(
                    ds, f, cmp, lambda d_, fi: M.summary_table(d_, fi, "secteur"), "entreprises"))
            else:
                summary = M.summary_table(ds, f, "secteur")
            if summary is None:
                empty_state(300, hint=HINT)
            elif summary.empty:
                empty_state(300, NO_RESULT)
            else:
                show_table(summary.rename(columns={"secteur": "Secteur"}), height=320)
