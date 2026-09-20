"""Persistance de l'état (page + filtres) dans l'adresse du navigateur.

Rafraîchir la page ou ouvrir un lien partagé restitue la même vue : page, période et
filtres. Séparateur des valeurs multiples : « | ».
"""
from __future__ import annotations

import streamlit as st

from . import config as C

SEP = "|"
_PERIOD = ("periode", "f_periode")
_MULTI = {
    "region": "f_region", "prefecture": "f_prefecture", "secteur": "f_secteur",
    "type_acteur": "f_type_acteur", "statut": "f_statut",
    "taille": "f_taille", "connexion": "f_conn", "infra": "f_infra",
}
_ADVANCED = {"f_taille", "f_conn", "f_infra"}


def restore(valid_pages: set[str]) -> None:
    """Recopie l'URL dans l'état de session, une seule fois, avant la création des widgets."""
    if st.session_state.get("_url_restored"):
        return
    st.session_state["_url_restored"] = True
    params = st.query_params
    if params.get("page") in valid_pages:
        st.session_state["page"] = params["page"]
    if params.get(_PERIOD[0]):
        st.session_state[_PERIOD[1]] = params[_PERIOD[0]]
    for param, key in _MULTI.items():
        raw = params.get(param)
        if not raw:
            continue
        st.session_state[key] = [v for v in raw.split(SEP) if v][: C.MAX_COMPARE]
        if key in _ADVANCED:
            st.session_state[key + "_on"] = True


def sync(page: str) -> None:
    """Écrit la vue courante dans l'URL (sans relancer le script)."""
    s = st.session_state
    params: dict[str, str] = {}
    if page != C.PAGES[0][0]:
        params["page"] = page
    period = s.get(_PERIOD[1])
    if period and period != s.get("_period_default"):
        params[_PERIOD[0]] = period
    for param, key in _MULTI.items():
        if key in _ADVANCED and not s.get(key + "_on"):
            continue
        values = s.get(key) or []
        if values:
            params[param] = SEP.join(values)
    if dict(st.query_params.items()) != params:
        st.query_params.from_dict(params)
