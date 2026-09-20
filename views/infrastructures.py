"""Vue « Infrastructures » : parc numérique par type et par territoire."""
from __future__ import annotations

import streamlit as st

from components import charts
from components.kpi import infra_strip
from components.layout import card_title, context_bar, empty_state, page_header, show_table
from utils import metrics as M
from utils.compare import get_comparison
from utils.data_loader import Datasets
from utils.filters import Filters

from .common import NO_RESULT, chart_block, grouped_block, infra_compare, missing, page_intro

HINT = missing("infrastructures", "type_infrastructure", "nombre")


def render(ds: Datasets, f: Filters) -> None:
    page_header("Infrastructures", "Parc d'infrastructures numériques par type et par territoire.")
    page_intro(ds)
    cmp = get_comparison(f)
    context_bar(f, cmp)

    with st.container(key="card_inf_strip"):
        compare = infra_compare(ds, f, cmp)
        note = "Comparaison non applicable" if (cmp.active and compare is None) else None
        card_title("dns", "Répartition des infrastructures numériques", note)
        infra_strip(M.infra_tiles(ds, f, max_tiles=None), compare, cmp)

    a, b = st.columns([42, 58], gap="small")
    with a:
        with st.container(key="card_inf_type"):
            card_title("bar_chart", "Infrastructures par type")
            if cmp.is_split("type_infrastructure"):
                grouped_block(ds, f, cmp, "type_infrastructure", 300, "inf_type_cmp", HINT,
                              dataset="infrastructures", top=8, others=False,
                              fn=lambda d, fi: M.infra_by(d, fi, "type_infrastructure"))
            else:
                chart_block(M.infra_by(ds, f, "type_infrastructure"), 300,
                            lambda d: charts.top_bars(d, 300), "inf_type", HINT)
    with b:
        with st.container(key="card_inf_region"):
            card_title("location_on", "Infrastructures par région")
            table = M.infra_cross(ds, f, "region", "type_infrastructure")
            chart_block(table, 300, lambda t: charts.stacked_bars(t, 300), "inf_region",
                        missing("infrastructures", "region", "type_infrastructure", "nombre"))

    with st.container(key="card_inf_table"):
        card_title("table_chart", "Détail par préfecture")
        table = M.infra_cross(ds, f, "prefecture", "type_infrastructure")
        if table is None:
            empty_state(140, hint=missing("infrastructures", "prefecture", "type_infrastructure", "nombre"))
        elif table.empty:
            empty_state(140, NO_RESULT)
        else:
            table = table.assign(Total=table.sum(axis=1)).sort_values("Total", ascending=False)
            show_table(table.reset_index().rename(columns={"prefecture": "Préfecture"}), height=320)
