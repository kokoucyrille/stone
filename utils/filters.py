"""Filtres : état, sidebar (sélection multiple, jusqu'à 2 valeurs par champ) et application."""
from __future__ import annotations

from dataclasses import dataclass, replace

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
    """Une dimension vide = aucun filtre ; 1 valeur = filtre ; 2 valeurs = comparaison."""
    start: int | None = None
    end: int | None = None
    region: tuple[str, ...] = ()
    prefecture: tuple[str, ...] = ()
    secteur: tuple[str, ...] = ()
    type_acteur: tuple[str, ...] = ()
    statut: tuple[str, ...] = ()
    taille: tuple[str, ...] = ()
    niveau_connexion: tuple[str, ...] = ()
    type_infrastructure: tuple[str, ...] = ()

    def dims(self) -> dict[str, tuple[str, ...]]:
        return {d: tuple(getattr(self, d)) for d in DIMENSIONS if getattr(self, d)}

    def with_dim(self, dim: str, values) -> "Filters":
        return replace(self, **{dim: tuple(values)})

    @property
    def single_year(self) -> bool:
        return self.start is not None and self.start == self.end


# --------------------------------------------------------------------------- #
# Application aux données
# --------------------------------------------------------------------------- #
def apply_dims(df: pd.DataFrame, f: Filters, skip: tuple[str, ...] = ()) -> pd.DataFrame:
    """Applique les filtres dimensionnels dont la colonne existe dans `df`."""
    for column, values in f.dims().items():
        if column in skip or column not in df.columns:
            continue
        df = df[df[column].isin(list(values))]
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
            disabled: bool = False, help: str | None = None) -> str:
    """Sélection unique (période)."""
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    shown = f":material/{icon}: {label}" if icon else label
    return st.selectbox(shown, options, key=key, disabled=disabled, help=help)


def _multi(key: str, label: str, options: list[str], placeholder: str, *,
           icon: str | None = None, disabled: bool = False, collapsed: bool = False,
           help: str | None = None) -> tuple[str, ...]:
    """Sélection multiple limitée à MAX_COMPARE valeurs ; vide = « tout »."""
    current = st.session_state.get(key)
    if current is not None:
        valid = [v for v in current if v in options][: C.MAX_COMPARE]
        if valid != list(current):
            st.session_state[key] = valid
    shown = f":material/{icon}: {label}" if icon else label
    picked = st.multiselect(
        shown, options, key=key, max_selections=C.MAX_COMPARE, placeholder=placeholder,
        disabled=disabled, help=help,
        label_visibility="collapsed" if collapsed else "visible",
    )
    return tuple(picked)


def _dim_options(ds: Datasets, dim: str) -> tuple[list[str], str | None]:
    """(choix, aide si le filtre est inactif). Les listes de référence ne servent
    qu'avant le chargement des données."""
    values = ds.values(dim)
    if values:
        return values, None
    if ds.empty:
        reference = C.REFERENCE_OPTIONS.get(dim)
        if dim == "type_infrastructure":
            reference = [label for label, _, _ in C.INFRA_TILES]
        if reference:
            return list(reference), None
        return [], "Ce filtre s'activera dès que vos données seront chargées."
    return [], "Aucune colonne correspondante dans les données chargées."


def render_sidebar(ds: Datasets) -> Filters:
    years = ds.years()
    period_help = None
    if not years:
        if ds.empty:  # aperçu avant chargement : bornes issues de la configuration
            years = list(range(C.PERIOD_FALLBACK[0], C.PERIOD_FALLBACK[1] + 1))
        else:
            period_help = "Aucune colonne « annee » dans les données chargées."
    with st.sidebar:
        with st.container(key="sb_head"):
            st.markdown(
                '<div class="sb-title"><span class="msr">filter_alt</span>Filtres</div>',
                unsafe_allow_html=True,
            )
            st.button("Réinitialiser", icon=":material/restart_alt:", key="btn_reset",
                      on_click=_reset, type="tertiary")

        # Période (sélection unique)
        periods = period_options(years)
        period = _select("f_periode", "Période", periods, icon="calendar_month",
                         disabled=not years, help=period_help)

        chosen: dict[str, tuple[str, ...]] = {}
        prefectures = ds.prefectures_by_region()
        for dim, key, label, icon in _SIMPLE:
            options, hint = _dim_options(ds, dim)
            if dim == "prefecture":
                regions = st.session_state.get("f_region") or []
                scoped = sorted({p for r in regions for p in prefectures.get(r, [])})
                if scoped:
                    options = scoped
            chosen[dim] = _multi(key, label, options, C.ALL_LABELS[dim], icon=icon,
                                 disabled=not options, help=hint)

        with st.expander("Filtres avancés", icon=":material/filter_alt:", expanded=False):
            for dim, key, label in _ADVANCED:
                options, hint = _dim_options(ds, dim)
                on = st.checkbox(label, key=key + "_on", disabled=not options, help=hint)
                picked = _multi(key, label, options, C.ALL_LABELS[dim],
                                disabled=not (on and options), collapsed=True)
                chosen[dim] = picked if on else ()

        st.markdown(
            '<div class="sb-hint">Astuce : choisissez 2 valeurs dans un même champ '
            "pour les comparer.</div>",
            unsafe_allow_html=True,
        )
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
