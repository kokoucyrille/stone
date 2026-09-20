"""Filtres : état, sidebar et application aux jeux de données."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from . import config as C
from .data_loader import Datasets

DIMENSIONS = (
    "region", "prefecture", "secteur", "type_acteur", "statut",
    "taille", "niveau_connexion", "type_infrastructure",
)


@dataclass(frozen=True)
class Filters:
    start: int | None = None
    end: int | None = None
    region: str | None = None
    prefecture: str | None = None
    secteur: str | None = None
    type_acteur: str | None = None
    statut: str | None = None
    taille: str | None = None
    niveau_connexion: str | None = None
    type_infrastructure: str | None = None

    def dims(self) -> dict[str, str]:
        return {d: getattr(self, d) for d in DIMENSIONS if getattr(self, d)}

    @property
    def single_year(self) -> bool:
        return self.start is not None and self.start == self.end


# --------------------------------------------------------------------------- #
# Application aux données
# --------------------------------------------------------------------------- #
def apply_dims(df: pd.DataFrame, f: Filters, skip: tuple[str, ...] = ()) -> pd.DataFrame:
    """Applique les filtres dimensionnels dont la colonne existe dans `df`."""
    for column, value in f.dims().items():
        if column in skip or column not in df.columns:
            continue
        df = df[df[column] == value]
    return df


def upto_year(df: pd.DataFrame, year: int | None) -> pd.DataFrame:
    """Situation à l'année `year` selon le mode de stock configuré."""
    if year is None or "annee" not in df.columns:
        return df
    if C.STOCK_MODE == "instantane":
        return df[df["annee"] == year]
    return df[df["annee"] <= year]


def latest_snapshot(df: pd.DataFrame, year: int | None) -> pd.DataFrame:
    """Dernière photographie disponible à ou avant `year` (données d'état)."""
    if year is None or "annee" not in df.columns:
        return df
    eligible = df[df["annee"] <= year]
    if eligible.empty:
        return eligible
    return eligible[eligible["annee"] == eligible["annee"].max()]


# --------------------------------------------------------------------------- #
# Période
# --------------------------------------------------------------------------- #
def period_options(years: list[int]) -> list[str]:
    if not years:
        return ["Toutes les années"]
    lo, hi = years[0], years[-1]
    options = [f"{lo} - {hi}"] if lo != hi else [str(lo)]
    options += [f"{y} - {hi}" for y in years[1:-1]]
    options += [str(y) for y in reversed(years)] if lo != hi else []
    return options


def parse_period(label: str, years: list[int]) -> tuple[int | None, int | None]:
    if not years:
        return None, None
    parts = [p.strip() for p in label.split("-")]
    try:
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        return int(parts[0]), int(parts[0])
    except ValueError:
        return years[0], years[-1]


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
_SIMPLE = [
    # (dimension, clé de session, libellé, icône Material)
    ("region", "f_region", "Région", "location_on"),
    ("prefecture", "f_prefecture", "Préfecture", "account_balance"),
    ("secteur", "f_secteur", "Secteur d'activité", "grid_view"),
    ("type_acteur", "f_type_acteur", "Type d'acteur", "person"),
    ("statut", "f_statut", "Statut", "settings"),
]
_ADVANCED = [
    ("taille", "f_taille", "Taille de l'entreprise"),
    ("niveau_connexion", "f_conn", "Niveau de connexion Internet"),
    ("type_infrastructure", "f_infra", "Type d'infrastructure"),
]
_STATE_KEYS = (
    ["f_periode"] + [k for _, k, _, _ in _SIMPLE]
    + [k for _, k, _ in _ADVANCED] + [k + "_on" for _, k, _ in _ADVANCED]
)


def _reset() -> None:
    for key in _STATE_KEYS:
        st.session_state.pop(key, None)


def _select(key: str, label: str, options: list[str], *, icon: str | None = None,
            disabled: bool = False, collapsed: bool = False) -> str:
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    shown = f":material/{icon}: {label}" if icon else label
    return st.selectbox(
        shown, options, key=key, disabled=disabled,
        label_visibility="collapsed" if collapsed else "visible",
    )


def render_sidebar(ds: Datasets) -> Filters:
    years = ds.years()
    with st.sidebar:
        with st.container(key="sb_head"):
            st.markdown(
                '<div class="sb-title"><span class="msr">filter_alt</span>Filtres</div>',
                unsafe_allow_html=True,
            )
            st.button("Réinitialiser", icon=":material/restart_alt:", key="btn_reset",
                      on_click=_reset, type="tertiary")

        # Période
        periods = period_options(years)
        period = _select("f_periode", "Période", periods, icon="calendar_month",
                         disabled=not years)

        chosen: dict[str, str | None] = {}
        prefectures = ds.prefectures_by_region()
        for dim, key, label, icon in _SIMPLE:
            options = ds.values(dim)
            if dim == "prefecture":
                region = st.session_state.get("f_region")
                if region in prefectures:
                    options = prefectures[region]
            all_label = C.ALL_LABELS[dim]
            value = _select(key, label, [all_label] + options, icon=icon,
                            disabled=not options)
            chosen[dim] = None if value == all_label else value

        with st.expander("Filtres avancés", icon=":material/filter_alt:", expanded=False):
            for dim, key, label in _ADVANCED:
                options = ds.values(dim)
                on = st.checkbox(label, key=key + "_on", disabled=not options)
                all_label = C.ALL_LABELS[dim]
                value = _select(key, label, [all_label] + options,
                                disabled=not (on and options), collapsed=True)
                chosen[dim] = value if (on and value != all_label) else None

        st.markdown(_sidebar_decoration(), unsafe_allow_html=True)

    start, end = parse_period(period, years)
    return Filters(start=start, end=end, **chosen)


def _sidebar_decoration() -> str:
    return (
        '<div class="sb-deco" aria-hidden="true">'
        '<svg viewBox="0 0 248 90" preserveAspectRatio="none">'
        '<path d="M0 54 C70 44 150 26 248 0 L248 12 C150 38 70 58 0 66 Z" fill="#0E9F6E"/>'
        '<path d="M0 64 C70 56 150 38 248 10 L248 22 C150 48 70 68 0 76 Z" fill="#FFCE00"/>'
        '<path d="M0 74 C70 68 150 50 248 20 L248 28 C150 58 70 78 0 84 Z" fill="#D21034"/>'
        "</svg>"
        '<div class="sb-tag"><span>Économie numérique</span>'
        "<span>Territoire du Togo</span><b>plus compétitif</b></div></div>"
    )
