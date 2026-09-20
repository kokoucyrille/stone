"""Blocs réutilisables par toutes les vues."""
from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st

from components import charts
from components.layout import empty_state, legend, plot
from utils import config as C
from utils import metrics as M
from utils.compare import relative, supports, top_rows, wide
from utils.formatting import fmt_int, fmt_pct

NO_RESULT = "Aucun résultat pour ces filtres"


def is_missing(data) -> bool:
    return data is None


def is_empty(data) -> bool:
    return data is not None and len(data) == 0


def chart_block(data, height: int, builder: Callable, key: str, hint: str) -> None:
    """Affiche le graphique, ou un état vide de même hauteur."""
    if is_missing(data):
        empty_state(height, hint=hint)
    elif is_empty(data):
        empty_state(height, NO_RESULT)
    else:
        plot(builder(data), key)


def donut_block(data: pd.DataFrame | None, key: str, hint: str, height: int = 200,
                center_label: str = "entreprises") -> None:
    """Anneau + légende (libellé, part) côte à côte."""
    if data is None or len(data) == 0:
        empty_state(height, hint=hint if data is None else "", **({} if data is None else {"title": NO_RESULT}))
        return
    left, right = st.columns([50, 50], vertical_alignment="center")
    with left:
        chart_block(data, height, lambda d: charts.donut(d, center_label, height), key, hint)
    with right:
        if data is not None and len(data):
            colors = charts.sector_colors(list(data["label"]))
            rows = [(c, r.label, "", fmt_pct(r.part)) for c, r in zip(colors, data.itertuples())]
            st.markdown(legend(rows, "lg--donut"), unsafe_allow_html=True)


def region_colors(cmp) -> dict[str, str] | None:
    """Couleurs A/B des régions comparées (cohérentes avec les KPI), sinon palette régionale."""
    return cmp.color_map() if (cmp.active and cmp.dim == "region") else None


def region_legend(regions: pd.DataFrame, value_format=fmt_int, colors=None) -> str:
    rows = []
    for i, r in enumerate(regions.itertuples()):
        part = f"({fmt_pct(r.part)})" if hasattr(r, "part") else ""
        color = (colors or {}).get(r.label) or charts.region_color(r.label, i)
        rows.append((color, r.label, value_format(r.valeur), part))
    return legend(rows, "lg--region")


def upload_panel(ds) -> None:
    """Envoi de fichiers dans data/ et diagnostic de reconnaissance."""
    from utils import config as C
    from utils.data_loader import SUPPORTED_SUFFIXES, save_uploads

    with st.expander("Charger des fichiers de données", icon=":material/upload_file:"):
        uploads = st.file_uploader(
            "Fichiers CSV, Excel ou Parquet", accept_multiple_files=True,
            type=[s.lstrip(".") for s in SUPPORTED_SUFFIXES], key="tdi_uploader",
            label_visibility="collapsed",
        )
        saved = st.session_state.setdefault("_tdi_saved", set())
        fresh = [u for u in uploads or [] if (u.name, u.size) not in saved]
        if fresh:
            try:
                save_uploads(fresh, C.DATA_DIR)
            except OSError as exc:
                st.error(f"Écriture impossible dans {C.DATA_DIR} : {exc}")
            else:
                saved.update((u.name, u.size) for u in fresh)
                st.rerun()
        if ds.files:
            lines = []
            for f in ds.files:
                if f.dataset:
                    lines.append(f"- **{f.name}** → jeu « {f.dataset} » ({f.rows} lignes)")
                else:
                    cols = ", ".join(f.columns[:8]) or "—"
                    lines.append(f"- **{f.name}** → non reconnu ({f.note}). Colonnes lues : {cols}")
            st.markdown("\n".join(lines))
        st.caption("Colonnes attendues : voir data/README.md. Les fichiers sont enregistrés dans data/.")


def page_intro(ds) -> None:
    """Message discret si aucun fichier n'est chargé ou si certains ne sont pas reconnus."""
    from components.layout import notice
    from utils import config as C
    if ds.empty:
        notice(
            "Aucune donnée chargée. Les filtres sont actifs et s'appliqueront dès que vos "
            "fichiers seront chargés (dossier <b>data/</b> ou bouton ci-dessous), "
            "sans valeur simulée."
        )
        upload_panel(ds)
    elif ds.unrecognized:
        names = ", ".join(f.name for f in ds.unrecognized[:3])
        notice(f"{len(ds.unrecognized)} fichier(s) non reconnu(s) : <b>{names}</b>. "
               "Ouvrez « Charger des fichiers de données » pour voir les colonnes lues.")
        upload_panel(ds)
    elif any(name not in ds.frames for name in C.DATASET_FILES):
        upload_panel(ds)  # jeux encore manquants : le panneau reste disponible, sans bandeau


def missing(dataset: str, *columns: str) -> str:
    return f"Requis : data/{dataset} › {', '.join(columns)}"


ENTREPRISES_REGION_HINT = missing("entreprises", "region", "nombre")


# --------------------------------------------------------------------------- #
# Comparaison A / B
# --------------------------------------------------------------------------- #
def compare_data(ds, f, cmp, fn, dataset: str, height: int, hint: str):
    """Séries A/B utilisables, ou None après affichage d'un état vide adapté."""
    if not supports(ds, dataset, cmp.dim):
        empty_state(height, "Comparaison non applicable",
                    hint=f"Le champ « {cmp.label} » est absent de data/{dataset}")
        return None
    parts = {label: fn(ds, fi) for label, fi in cmp.series(f)}
    if all(v is None for v in parts.values()):
        empty_state(height, hint=hint)
        return None
    if all(v is None or len(v) == 0 for v in parts.values()):
        empty_state(height, NO_RESULT)
        return None
    return parts


def grouped_block(ds, f, cmp, column: str, height: int, key: str, hint: str, *,
                  dataset: str = "entreprises", top: int = 6, others: bool = True,
                  percent: bool = False, stack: bool = False, fn=None) -> None:
    """Barres horizontales A / B pour une répartition par `column`."""
    fn = fn or (lambda d, fi: M.group_count(d, fi, column))
    parts = compare_data(ds, f, cmp, fn, dataset, height, hint)
    if parts is None:
        return
    table = wide(parts)
    if percent:
        table = relative(table)
    table = top_rows(table, top, others)
    plot(charts.grouped_hbars(table, cmp.color_map(), height, stack=stack, percent=percent), key)


def infra_compare(ds, f, cmp):
    """[{libellé: valeur}] par valeur comparée, ou None si le champ est absent des infrastructures."""
    if not cmp.active or not supports(ds, "infrastructures", cmp.dim):
        return None
    return [
        {label: value for label, value, _ in (M.infra_tiles(ds, fi, max_tiles=None) or [])}
        for _, fi in cmp.series(f)
    ]
