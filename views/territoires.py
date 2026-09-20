"""Vue « Territoires » : carte pilotée par indicateur, synthèses régionales."""
from __future__ import annotations

import streamlit as st

from components import charts
from components.layout import card_title, compare_bar, empty_state, page_header, plot, show_table
from utils import metrics as M
from utils.compare import by_series, get_comparison, stack_tables, supports
from utils.data_loader import Datasets
from utils.filters import Filters
from utils.formatting import fmt_int, fmt_pct

from .common import (NO_RESULT, chart_block, grouped_block, missing, page_intro, region_colors,
                     region_legend)


def _metric_options(ds: Datasets, f: Filters) -> dict[str, tuple]:
    """Indicateurs cartographiables selon les données réellement disponibles."""
    options: dict[str, tuple] = {}
    ent = M.by_region(ds, f)
    if ent is not None:
        options["Entreprises"] = (ent, "entreprises", fmt_int)
    jobs = M.group_count(ds, f, "region", value="emplois")
    if jobs is not None:
        options["Emplois"] = (jobs, "emplois", fmt_int)
    infra = M.infra_by(ds, f, "region")
    if infra is not None:
        options["Infrastructures"] = (infra, "infrastructures", fmt_int)
    net = M.internet_by_region(ds, f)
    if net is not None:
        options["Couverture Internet"] = (net, "de couverture", lambda v: fmt_pct(v, 1))
    return options


def render(ds: Datasets, f: Filters) -> None:
    page_header("Territoires", "Répartition territoriale de l'économie numérique.")
    page_intro(ds)
    cmp = get_comparison(f)
    compare_bar(cmp)

    left, right = st.columns([55, 45], gap="small")
    with left:
        with st.container(key="card_terr_map"):
            card_title("location_on", "Carte des régions")
            options = _metric_options(ds, f)
            if options:
                choice = st.radio("Indicateur", list(options), horizontal=True,
                                  key="terr_metric", label_visibility="collapsed")
                data, unit, fmt = options[choice]
            else:
                data, unit, fmt = None, "entreprises", fmt_int
            usable = data if (data is not None and len(data)) else None
            legend_col, map_col = st.columns([38, 62], vertical_alignment="center")
            with legend_col:
                if usable is not None:
                    st.markdown(region_legend(usable, fmt, region_colors(cmp)), unsafe_allow_html=True)
                else:
                    empty_state(300, hint=missing("entreprises", "region", "nombre"))
            with map_col:
                plot(charts.region_map(usable, 470, unit, fmt, highlight=f.region,
                                       colors=region_colors(cmp)), "terr_map")
    with right:
        with st.container(key="card_terr_table"):
            card_title("table_chart", "Synthèse par territoire")
            tab_region, tab_pref = st.tabs(["Par région", "Par préfecture"])
            for tab, column in ((tab_region, "region"), (tab_pref, "prefecture")):
                with tab:
                    if cmp.is_split(column):
                        if not supports(ds, "entreprises", cmp.dim):
                            empty_state(300, "Comparaison non applicable",
                                        hint=f"Le champ « {cmp.label} » est absent de data/entreprises")
                            continue
                        table = stack_tables(by_series(
                            ds, f, cmp, lambda d, fi, c=column: M.summary_table(d, fi, c),
                            "entreprises"))
                    else:
                        table = M.summary_table(ds, f, column)
                    if table is None:
                        empty_state(300, hint=missing("entreprises", column, "nombre"))
                    elif table.empty:
                        empty_state(300, NO_RESULT)
                    else:
                        table = table.rename(columns={column: column.capitalize()})
                        show_table(table, height=390)

    a, b = st.columns([50, 50], gap="small")
    with a:
        with st.container(key="card_terr_top"):
            card_title("account_balance", "Top 10 des préfectures par nombre d'entreprises")
            if cmp.is_split("prefecture"):
                grouped_block(ds, f, cmp, "prefecture", 300, "terr_top_cmp",
                              missing("entreprises", "prefecture", "nombre"), top=10,
                              others=False, stack=cmp.dim == "region")
            else:
                chart_block(M.top_prefectures(ds, f, 10), 300,
                            lambda d: charts.top_bars(d, 300), "terr_top",
                            missing("entreprises", "prefecture", "nombre"))
    with b:
        with st.container(key="card_terr_net"):
            card_title("signal_cellular_alt", "Accès à Internet par région")
            chart_block(M.internet_by_region(ds, f), 300,
                        lambda d: charts.vertical_bars(d, 300), "terr_net",
                        missing("connectivite", "region", "couverture_internet_pct"))
