"""Vue « Tableau de bord » : bandeau, 5 KPI, grille de visualisations."""
from __future__ import annotations

import streamlit as st

from components import charts
from components.kpi import indicators_strip, infra_strip, kpi_row
from components.layout import card_title, empty_state, hero, plot
from utils import metrics as M
from utils.data_loader import Datasets
from utils.filters import Filters

from .common import (ENTREPRISES_REGION_HINT, NO_RESULT, chart_block, donut_block,
                     missing, page_intro, region_legend)

# Hauteurs (px) réglées pour reproduire les proportions de la maquette.
H_MAP, H_EVO, H_TOP, H_DONUT, H_NET = 416, 200, 148, 200, 148


def _region_card(ds: Datasets, f: Filters) -> None:
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
                st.markdown(region_legend(regions), unsafe_allow_html=True)
        with map_col:
            usable = regions if (regions is not None and not regions.empty) else None
            plot(charts.region_map(usable, H_MAP), "dash_map")


def _evolution_card(ds: Datasets, f: Filters) -> None:
    with st.container(key="card_evo"):
        card_title("show_chart", "Évolution du nombre d'entreprises numériques")
        chart_block(M.evolution(ds, f), H_EVO, lambda s: charts.evolution_chart(s, H_EVO),
                    "dash_evo", missing("entreprises", "annee", "nombre"))


def _sector_card(ds: Datasets, f: Filters) -> None:
    with st.container(key="card_sector"):
        card_title("donut_large", "Répartition par secteur d'activité")
        donut_block(M.by_sector(ds, f, top=5), "dash_sector",
                    missing("entreprises", "secteur", "nombre"), H_DONUT)


def _top_card(ds: Datasets, f: Filters) -> None:
    with st.container(key="card_top"):
        card_title("account_balance", "Top 5 des préfectures par nombre d'entreprises")
        chart_block(M.top_prefectures(ds, f, 5), H_TOP, lambda d: charts.top_bars(d, H_TOP),
                    "dash_top", missing("entreprises", "prefecture", "nombre"))


def _net_card(ds: Datasets, f: Filters) -> None:
    with st.container(key="card_net"):
        card_title("signal_cellular_alt", "Accès à Internet par région")
        chart_block(M.internet_by_region(ds, f), H_NET,
                    lambda d: charts.vertical_bars(d, H_NET), "dash_net",
                    missing("connectivite", "region", "couverture_internet_pct"))


def render(ds: Datasets, f: Filters) -> None:
    hero()
    page_intro(ds)
    kpi_row(M.compute_kpis(ds, f))

    col_left, col_mid, col_right = st.columns([385, 310, 305], gap="small")
    with col_left:
        _region_card(ds, f)
    with col_mid:
        _evolution_card(ds, f)
        _top_card(ds, f)
    with col_right:
        _sector_card(ds, f)
        _net_card(ds, f)

    col_a, col_b = st.columns([54, 46], gap="small")
    with col_a:
        with st.container(key="card_infra"):
            card_title("dns", "Répartition des infrastructures numériques")
            infra_strip(M.infra_tiles(ds, f))
    with col_b:
        with st.container(key="card_ind"):
            card_title("insights", "Indicateurs clés")
            tiles = M.key_indicators(ds, f)
            if tiles:
                indicators_strip(tiles)
            else:
                empty_state(74, hint="Requis : data/indicateurs › indicateur, valeur, annee")
