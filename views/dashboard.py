"""Vue « Tableau de bord » : bandeau, 5 KPI, grille de visualisations (avec comparaison A / B)."""
from __future__ import annotations

import streamlit as st

from components import charts
from components.kpi import indicators_strip, infra_strip, kpi_row
from components.layout import card_title, compare_bar, empty_state, hero, plot
from utils import metrics as M
from utils.compare import get_comparison
from utils.data_loader import Datasets
from utils.filters import Filters

from .common import (ENTREPRISES_REGION_HINT, NO_RESULT, chart_block, compare_data, donut_block,
                     grouped_block, infra_compare, missing, page_intro, region_colors,
                     region_legend)

# Hauteurs (px) réglées pour reproduire les proportions de la maquette.
H_MAP, H_EVO, H_TOP, H_DONUT, H_NET = 416, 200, 148, 200, 148


def _region_card(ds: Datasets, f: Filters, cmp) -> None:
    regions = M.by_region(ds, f)
    with st.container(key="card_map"):
        card_title("location_on", "Répartition des entreprises numériques par région")
        legend_col, map_col = st.columns([46, 54], vertical_alignment="center")
        with legend_col:
            if regions is None:
                empty_state(H_MAP - 40, hint=ENTREPRISES_REGION_HINT)
            elif regions.empty:
                empty_state(H_MAP - 40, NO_RESULT)
            else:
                st.markdown(region_legend(regions, colors=region_colors(cmp)), unsafe_allow_html=True)
        with map_col:
            usable = regions if (regions is not None and not regions.empty) else None
            plot(charts.region_map(usable, H_MAP, highlight=f.region, colors=region_colors(cmp)),
                 "dash_map")


def _evolution_card(ds: Datasets, f: Filters, cmp) -> None:
    hint = missing("entreprises", "annee", "nombre")
    with st.container(key="card_evo"):
        card_title("show_chart", "Évolution du nombre d'entreprises numériques")
        if cmp.active:
            parts = compare_data(ds, f, cmp, M.evolution, "entreprises", H_EVO, hint)
            if parts is not None:
                usable = {k: v for k, v in parts.items() if v is not None and len(v)}
                plot(charts.compare_lines(usable, cmp.color_map(), H_EVO), "dash_evo_cmp")
        else:
            chart_block(M.evolution(ds, f), H_EVO, lambda s: charts.evolution_chart(s, H_EVO),
                        "dash_evo", hint)


def _sector_card(ds: Datasets, f: Filters, cmp) -> None:
    hint = missing("entreprises", "secteur", "nombre")
    with st.container(key="card_sector"):
        card_title("donut_large", "Répartition par secteur d'activité")
        if cmp.is_split("secteur"):
            grouped_block(ds, f, cmp, "secteur", H_DONUT, "dash_sector_cmp", hint, top=5)
        else:
            donut_block(M.by_sector(ds, f, top=5), "dash_sector", hint, H_DONUT)


def _top_card(ds: Datasets, f: Filters, cmp) -> None:
    hint = missing("entreprises", "prefecture", "nombre")
    with st.container(key="card_top"):
        card_title("account_balance", "Top 5 des préfectures par nombre d'entreprises")
        if cmp.is_split("prefecture"):
            stack = cmp.dim == "region"   # une préfecture n'appartient qu'à une région
            grouped_block(ds, f, cmp, "prefecture", H_TOP + (0 if stack else 36), "dash_top_cmp",
                          hint, top=5, others=False, stack=stack)
        else:
            chart_block(M.top_prefectures(ds, f, 5), H_TOP, lambda d: charts.top_bars(d, H_TOP),
                        "dash_top", hint)


def _net_card(ds: Datasets, f: Filters, cmp) -> None:
    with st.container(key="card_net"):
        card_title("signal_cellular_alt", "Accès à Internet par région")
        override = region_colors(cmp)
        chart_block(M.internet_by_region(ds, f), H_NET,
                    lambda d: charts.vertical_bars(
                        d, H_NET, colors=[override[l] for l in d["label"]] if override and
                        all(l in override for l in d["label"]) else None),
                    "dash_net",
                    missing("connectivite", "region", "couverture_internet_pct"))


def render(ds: Datasets, f: Filters) -> None:
    hero()
    page_intro(ds)
    cmp = get_comparison(f)
    compare_bar(cmp)
    kpi_row(M.compute_kpis(ds, f), M.compare_kpis(ds, f, cmp) if cmp.active else None, cmp)

    col_left, col_mid, col_right = st.columns([385, 310, 305], gap="small")
    with col_left:
        _region_card(ds, f, cmp)
    with col_mid:
        _evolution_card(ds, f, cmp)
        _top_card(ds, f, cmp)
    with col_right:
        _sector_card(ds, f, cmp)
        _net_card(ds, f, cmp)

    col_a, col_b = st.columns([54, 46], gap="small")
    with col_a:
        with st.container(key="card_infra"):
            note = None
            compare = infra_compare(ds, f, cmp)
            if cmp.active and compare is None:
                note = "Comparaison non applicable"
            card_title("dns", "Répartition des infrastructures numériques", note)
            infra_strip(M.infra_tiles(ds, f), compare, cmp)
    with col_b:
        with st.container(key="card_ind"):
            card_title("insights", "Indicateurs clés")
            tiles = M.key_indicators(ds, f)
            if tiles:
                indicators_strip(tiles)
            else:
                empty_state(74, hint="Requis : data/indicateurs › indicateur, valeur, annee")
