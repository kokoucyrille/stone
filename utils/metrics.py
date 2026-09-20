"""Indicateurs (KPI) et agrégations alimentant les visualisations.

Règles de calcul
----------------
* Année de référence = fin de la période sélectionnée.
* Entreprises, emplois, investissements et infrastructures : stock à l'année de
  référence (cf. ``config.STOCK_MODE``), variation en % par rapport à l'année
  précédente lorsque les données la contiennent.
* Couverture Internet : dernière photographie disponible à ou avant l'année de
  référence, moyenne pondérée par la population si elle est fournie ; variation
  exprimée en points.
* Aucune valeur n'est estimée : sans donnée, la fonction renvoie ``None``.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config as C
from .data_loader import Datasets
from .filters import Filters, apply_dims, latest_snapshot, upto_year
from .formatting import fmt_dec, fmt_int, fmt_pct, norm_key


# --------------------------------------------------------------------------- #
# KPI
# --------------------------------------------------------------------------- #
@dataclass
class Kpi:
    key: str
    label: str
    icon: str
    tone: str                    # green | blue | yellow | purple | teal
    value: float | None
    kind: str                    # int | pct | dec
    delta: float | None = None
    delta_unit: str = "%"
    delta_label: str | None = None   # « vs. 2024 »


def format_kpi_value(kpi: Kpi) -> str:
    if kpi.value is None:
        return "—"
    if kpi.kind == "pct":
        return fmt_pct(kpi.value, 1)
    if kpi.kind == "dec":
        return fmt_dec(kpi.value, 0 if float(kpi.value).is_integer() else 1)
    return fmt_int(kpi.value)


def _column_sum(df: pd.DataFrame | None, column: str) -> pd.Series | None:
    if df is None or column not in df.columns or df[column].notna().sum() == 0:
        return None
    return df[column]


def _stock_kpi(df: pd.DataFrame | None, column: str, f: Filters, years_min: int | None):
    """(valeur, variation %, libellé) d'une mesure cumulée."""
    if df is None or _column_sum(df, column) is None:
        return None, None, None
    df = apply_dims(df, f)
    current = float(upto_year(df, f.end)[column].sum())
    if f.end is None or "annee" not in df.columns or years_min is None or f.end - 1 < years_min:
        return current, None, None
    previous = float(upto_year(df, f.end - 1)[column].sum())
    if previous <= 0:
        return current, None, None
    return current, (current / previous - 1) * 100, f"vs. {f.end - 1}"


def _weighted_mean(df: pd.DataFrame) -> float | None:
    values = df["couverture_internet_pct"]
    mask = values.notna()
    if not mask.any():
        return None
    if "population" in df.columns and df.loc[mask, "population"].fillna(0).sum() > 0:
        weights = df.loc[mask, "population"].fillna(0).to_numpy(dtype=float)
        return float(np.average(values[mask].to_numpy(dtype=float), weights=weights))
    return float(values[mask].mean())


def compute_kpis(ds: Datasets, f: Filters) -> list[Kpi]:
    years = ds.years()
    y_min = years[0] if years else None
    ent, infra, conn = ds.get("entreprises"), ds.get("infrastructures"), ds.get("connectivite")

    kpis: list[Kpi] = []

    v, d, lab = _stock_kpi(ent, "nombre", f, y_min)
    kpis.append(Kpi("entreprises", "Entreprises numériques", "apartment", "green", v, "int", d,
                    delta_label=lab))
    v, d, lab = _stock_kpi(ent, "emplois", f, y_min)
    kpis.append(Kpi("emplois", "Emplois créés", "groups", "blue", v, "int", d, delta_label=lab))

    # Couverture Internet
    value = delta = label = None
    if conn is not None and "couverture_internet_pct" in conn.columns:
        conn_f = apply_dims(conn, f)
        snap = latest_snapshot(conn_f, f.end)
        value = _weighted_mean(snap) if len(snap) else None
        if value is not None and "annee" in snap.columns and snap["annee"].notna().any():
            snap_year = int(snap["annee"].max())
            prev = latest_snapshot(conn_f, snap_year - 1)
            prev_value = _weighted_mean(prev) if len(prev) else None
            if prev_value is not None:
                delta, label = value - prev_value, f"vs. {int(prev['annee'].max())}"
    kpis.append(Kpi("couverture", "Couverture Internet", "wifi", "yellow", value, "pct", delta,
                    "pts", label))

    v, d, lab = _stock_kpi(infra, "nombre", f, y_min)
    kpis.append(Kpi("infrastructures", "Infrastructures digitales", "cloud_upload", "purple", v,
                    "int", d, delta_label=lab))
    v, d, lab = _stock_kpi(ent, "investissement_mds_fcfa", f, y_min)
    kpis.append(Kpi("investissements", "Investissements (Mds F CFA)", "database", "teal", v, "dec",
                    d, delta_label=lab))
    return kpis


# --------------------------------------------------------------------------- #
# Entreprises
# --------------------------------------------------------------------------- #
def _entreprises_at_year(ds: Datasets, f: Filters, skip: tuple[str, ...] = ()) -> pd.DataFrame | None:
    df = ds.get("entreprises")
    if df is None or "nombre" not in df.columns:
        return None
    return upto_year(apply_dims(df, f, skip=skip), f.end)


def group_count(ds: Datasets, f: Filters, column: str, *, value: str = "nombre",
                skip: tuple[str, ...] = ()) -> pd.DataFrame | None:
    """Somme de `value` par `column` (entreprises, à l'année de référence)."""
    df = _entreprises_at_year(ds, f, skip=skip)
    if df is None or column not in df.columns or value not in df.columns:
        return None
    grouped = (
        df.dropna(subset=[column]).groupby(column, observed=True)[value].sum().reset_index()
    )
    grouped.columns = ["label", "valeur"]
    total = grouped["valeur"].sum()
    grouped["part"] = grouped["valeur"] / total * 100 if total else 0.0
    return grouped.sort_values("valeur", ascending=False).reset_index(drop=True)


def by_region(ds: Datasets, f: Filters) -> pd.DataFrame | None:
    grouped = group_count(ds, f, "region")
    if grouped is None or grouped.empty:
        return grouped
    order = {r: i for i, r in enumerate(C.REGION_ORDER)}
    grouped["_o"] = grouped["label"].map(lambda r: order.get(r, 99))
    grouped = grouped.sort_values(["_o", "valeur"], ascending=[True, False]).drop(columns="_o")
    return grouped.reset_index(drop=True)


def by_sector(ds: Datasets, f: Filters, top: int | None = 5) -> pd.DataFrame | None:
    grouped = group_count(ds, f, "secteur")
    if grouped is None or grouped.empty:
        return grouped
    grouped = grouped.sort_values("valeur", ascending=False).reset_index(drop=True)
    if top and len(grouped) > top:
        rest = grouped.iloc[top:]
        grouped = pd.concat(
            [grouped.iloc[:top],
             pd.DataFrame([{"label": "Autres", "valeur": rest["valeur"].sum(),
                            "part": rest["part"].sum()}])],
            ignore_index=True,
        )
    return grouped


def top_prefectures(ds: Datasets, f: Filters, n: int = 5) -> pd.DataFrame | None:
    grouped = group_count(ds, f, "prefecture")
    if grouped is None or grouped.empty:
        return grouped
    return grouped.sort_values("valeur", ascending=False).head(n).reset_index(drop=True)


def stock_by_year(ds: Datasets, f: Filters, group: str | None = None) -> pd.DataFrame | None:
    """Stock d'entreprises par année (colonnes = catégories si `group`)."""
    df = ds.get("entreprises")
    years = ds.years()
    if df is None or not {"annee", "nombre"} <= set(df.columns) or not years:
        return None
    if group and group not in df.columns:
        return None
    df = apply_dims(df, f).dropna(subset=["annee"])
    if df.empty:
        return pd.DataFrame()
    end = f.end or years[-1]
    start = years[0] if (f.start is None or f.single_year) else f.start
    df = df.assign(annee=df["annee"].astype(int))
    first = int(df["annee"].min())
    span = range(min(first, start), end + 1)
    if group:
        table = df.pivot_table(index="annee", columns=group, values="nombre", aggfunc="sum")
    else:
        table = df.groupby("annee")[["nombre"]].sum()
    table = table.reindex(span)
    table = table.fillna(0).cumsum() if C.STOCK_MODE != "instantane" else table
    table = table.loc[start:end]
    return table.dropna(how="all")


def evolution(ds: Datasets, f: Filters) -> pd.Series | None:
    table = stock_by_year(ds, f)
    if table is None or table.empty:
        return None if table is None else pd.Series(dtype=float)
    return table["nombre"].dropna()


# --------------------------------------------------------------------------- #
# Connectivité
# --------------------------------------------------------------------------- #
def internet_by_region(ds: Datasets, f: Filters) -> pd.DataFrame | None:
    df = ds.get("connectivite")
    if df is None or not {"region", "couverture_internet_pct"} <= set(df.columns):
        return None
    snap = latest_snapshot(apply_dims(df, f), f.end).dropna(subset=["region"])
    rows = [
        {"label": region, "valeur": _weighted_mean(group)}
        for region, group in snap.groupby("region")
    ]
    out = pd.DataFrame(rows, columns=["label", "valeur"]).dropna()
    return out.sort_values("valeur", ascending=False).reset_index(drop=True)


def internet_by_prefecture(ds: Datasets, f: Filters) -> pd.DataFrame | None:
    df = ds.get("connectivite")
    if df is None or not {"prefecture", "couverture_internet_pct"} <= set(df.columns):
        return None
    snap = latest_snapshot(apply_dims(df, f), f.end).dropna(subset=["prefecture"])
    rows = [
        {"label": p, "valeur": _weighted_mean(g)} for p, g in snap.groupby("prefecture")
    ]
    out = pd.DataFrame(rows, columns=["label", "valeur"]).dropna()
    return out.sort_values("valeur", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Infrastructures
# --------------------------------------------------------------------------- #
def infra_frame(ds: Datasets, f: Filters) -> pd.DataFrame | None:
    df = ds.get("infrastructures")
    if df is None or "nombre" not in df.columns:
        return None
    return upto_year(apply_dims(df, f), f.end)


def infra_by(ds: Datasets, f: Filters, column: str) -> pd.DataFrame | None:
    df = infra_frame(ds, f)
    if df is None or column not in df.columns:
        return None
    out = df.dropna(subset=[column]).groupby(column)["nombre"].sum().reset_index()
    out.columns = ["label", "valeur"]
    return out.sort_values("valeur", ascending=False).reset_index(drop=True)


def infra_tiles(ds: Datasets, f: Filters,
                max_tiles: int | None = C.INFRA_MAX_TILES) -> list[tuple[str, float, str]] | None:
    """[(libellé, valeur, icône)] — les 4 types de la maquette d'abord, puis les autres."""
    totals = infra_by(ds, f, "type_infrastructure")
    if totals is None:
        return None
    sums = dict(zip(totals["label"], totals["valeur"]))
    tiles: list[tuple[str, float, str]] = []
    used: set[str] = set()
    for label, keywords, icon in C.INFRA_TILES:
        matches = [t for t in sums if any(k in norm_key(t) for k in keywords)]
        if matches:
            tiles.append((label, float(sum(sums[t] for t in matches)), icon))
            used.update(matches)
    others = sorted((t for t in sums if t not in used), key=lambda t: -sums[t])
    for t in others:
        if max_tiles is not None and len(tiles) >= max_tiles:
            break
        tiles.append((t, float(sums[t]), C.INFRA_DEFAULT_ICON))
    return tiles


# --------------------------------------------------------------------------- #
# Indicateurs clés
# --------------------------------------------------------------------------- #
def _indicator_text(value: float, unit: str | None) -> str:
    unit_key = norm_key(unit) if unit else ""
    if unit_key in ("pct", "pourcent", "pourcentage", "percent") or (unit or "").strip() == "%":
        return fmt_pct(value, 1)
    text = fmt_dec(value, 0 if float(value).is_integer() else 1)
    return f"{text} {unit}".strip() if unit else text


def key_indicators(ds: Datasets, f: Filters) -> list[tuple[str, str, str]]:
    """[(libellé, valeur formatée, icône)] limités aux indicateurs disponibles."""
    tiles: list[tuple[str, str, str]] = []
    ind = ds.get("indicateurs")
    growth_series = None
    for label, keywords, icon in C.KEY_INDICATORS:
        text = None
        if ind is not None and {"indicateur", "valeur"} <= set(ind.columns):
            names = ind["indicateur"].map(norm_key)
            rows = ind[names.map(lambda n: any(k in n for k in keywords))].dropna(subset=["valeur"])
            if "annee" in rows.columns and rows["annee"].notna().any() and f.end \
                    and "objectif" not in keywords:
                rows = rows[rows["annee"].isna() | (rows["annee"] <= f.end)]
            if len(rows):
                if "annee" in rows.columns and rows["annee"].notna().any():
                    rows = rows.sort_values("annee", na_position="first")
                row = rows.iloc[-1]
                unit = row["unite"] if "unite" in rows.columns and pd.notna(row.get("unite")) else None
                text = _indicator_text(float(row["valeur"]), unit)
        if text is None and "croissance" in keywords:
            if growth_series is None:
                growth_series = evolution(ds, f)
            if growth_series is not None and len(growth_series) >= 2 and growth_series.iloc[-2] > 0:
                text = fmt_pct((growth_series.iloc[-1] / growth_series.iloc[-2] - 1) * 100, 1)
        if text is not None:
            tiles.append((label, text, icon))
    return tiles


# --------------------------------------------------------------------------- #
# Tableaux de synthèse (vues détaillées)
# --------------------------------------------------------------------------- #
def summary_table(ds: Datasets, f: Filters, column: str) -> pd.DataFrame | None:
    """Tableau par `column` : entreprises, part, emplois, investissements."""
    df = _entreprises_at_year(ds, f)
    if df is None or column not in df.columns:
        return None
    agg = {"Entreprises": ("nombre", "sum")}
    if "emplois" in df.columns and df["emplois"].notna().any():
        agg["Emplois"] = ("emplois", "sum")
    if "investissement_mds_fcfa" in df.columns and df["investissement_mds_fcfa"].notna().any():
        agg["Investissements (Mds F CFA)"] = ("investissement_mds_fcfa", "sum")
    out = df.dropna(subset=[column]).groupby(column).agg(**agg).reset_index()
    for col in ("Entreprises", "Emplois"):
        if col in out.columns:
            out[col] = out[col].round(0).astype("int64")
    if "Investissements (Mds F CFA)" in out.columns:
        out["Investissements (Mds F CFA)"] = out["Investissements (Mds F CFA)"].round(1)
    total = out["Entreprises"].sum()
    out.insert(2, "Part (%)", (out["Entreprises"] / total * 100).round(1) if total else 0.0)
    return out.sort_values("Entreprises", ascending=False).reset_index(drop=True)


def _order_regions(table: pd.DataFrame, axis_name: str) -> pd.DataFrame:
    """Range les lignes selon l'ordre des régions de la charte si l'axe est « region »."""
    if axis_name != "region" or table.empty:
        return table
    order = {r: i for i, r in enumerate(C.REGION_ORDER)}
    return table.loc[sorted(table.index, key=lambda r: (order.get(r, 99), str(r)))]


def cross_table(ds: Datasets, f: Filters, rows: str, cols: str) -> pd.DataFrame | None:
    """Croisement entreprises rows × cols (à l'année de référence)."""
    df = _entreprises_at_year(ds, f)
    if df is None or rows not in df.columns or cols not in df.columns:
        return None
    df = df.dropna(subset=[rows, cols])
    if df.empty:
        return pd.DataFrame()
    return _order_regions(
        df.pivot_table(index=rows, columns=cols, values="nombre", aggfunc="sum", fill_value=0), rows
    )


def infra_cross(ds: Datasets, f: Filters, rows: str, cols: str) -> pd.DataFrame | None:
    df = infra_frame(ds, f)
    if df is None or rows not in df.columns or cols not in df.columns:
        return None
    df = df.dropna(subset=[rows, cols])
    if df.empty:
        return pd.DataFrame()
    return _order_regions(
        df.pivot_table(index=rows, columns=cols, values="nombre", aggfunc="sum", fill_value=0), rows
    )
