"""Comparaison de deux valeurs d'un même champ de filtre (A / B).

Principe : chaque calcul existant est relancé une fois par valeur comparée
(``Filters.with_dim``) puis les résultats sont juxtaposés. Rien n'est estimé :
si le jeu de données ne contient pas le champ comparé, la série vaut ``None``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from . import config as C
from .data_loader import Datasets
from .filters import Filters


@dataclass(frozen=True)
class Comparison:
    dim: str | None = None
    values: tuple[str, ...] = ()
    extra: tuple[str, ...] = ()     # autres champs à 2 valeurs : traités comme un cumul

    @property
    def active(self) -> bool:
        return self.dim is not None

    @property
    def label(self) -> str:
        return C.DIM_LABELS.get(self.dim, "") if self.dim else ""

    def color(self, index: int) -> str:
        return C.COMPARE_COLORS[index % len(C.COMPARE_COLORS)]

    def color_map(self) -> dict[str, str]:
        return {v: self.color(i) for i, v in enumerate(self.values)}

    def series(self, f: Filters) -> list[tuple[str, Filters]]:
        return [(v, f.with_dim(self.dim, (v,))) for v in self.values]

    def is_split(self, breakdown: str | None = None) -> bool:
        """Faut-il scinder le graphique en A / B ? Non si la répartition affichée est
        déjà celle du champ comparé (les deux valeurs y figurent naturellement)."""
        return self.active and self.dim != breakdown


def get_comparison(f: Filters) -> Comparison:
    pairs = [(d, v) for d, v in f.dims().items() if len(v) == 2]
    if not pairs:
        return Comparison()
    dim, values = pairs[0]
    return Comparison(dim, tuple(values), tuple(C.DIM_LABELS[d] for d, _ in pairs[1:]))


def supports(ds: Datasets, dataset: str, dim: str | None) -> bool:
    df = ds.get(dataset)
    return df is not None and dim is not None and dim in df.columns


def by_series(ds: Datasets, f: Filters, cmp: Comparison, fn: Callable, dataset: str) -> dict:
    """{valeur comparée: fn(ds, filtres restreints à cette valeur)} ; None si le champ manque."""
    ok = supports(ds, dataset, cmp.dim)
    return {label: (fn(ds, fi) if ok else None) for label, fi in cmp.series(f)}


def wide(parts: dict[str, pd.DataFrame | None], label: str = "label",
         value: str = "valeur") -> pd.DataFrame | None:
    """Juxtapose des tables (label, valeur) : index = libellés, colonnes = valeurs comparées."""
    if all(v is None for v in parts.values()):
        return None
    columns = {}
    for name, df in parts.items():
        ok = df is not None and len(df) > 0
        columns[name] = df.set_index(label)[value].astype(float) if ok else pd.Series(dtype=float)
    table = pd.concat(columns, axis=1).fillna(0.0)
    return table[list(parts.keys())] if len(table.columns) else table


def top_rows(table: pd.DataFrame, n: int, others: bool = True) -> pd.DataFrame:
    """Garde les n premiers libellés (somme des séries) ; le reste devient « Autres »."""
    order = table.sum(axis=1).sort_values(ascending=False)
    keep = list(order.index[:n])
    out = table.loc[keep]
    if others and len(order) > n:
        out = pd.concat([out, table.drop(index=keep).sum().to_frame("Autres").T])
    return out


def relative(table: pd.DataFrame) -> pd.DataFrame:
    totals = table.sum().replace(0, float("nan"))
    return (table / totals * 100).fillna(0.0)


def stack_tables(parts: dict[str, pd.DataFrame | None]) -> pd.DataFrame | None:
    """Tableaux superposés avec une première colonne « Sélection »."""
    frames = [df.assign(Sélection=name) for name, df in parts.items() if df is not None and len(df)]
    if all(v is None for v in parts.values()):
        return None
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    cols = ["Sélection"] + [c for c in out.columns if c != "Sélection"]
    return out[cols]
