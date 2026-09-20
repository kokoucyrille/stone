"""Chargement des données réelles du projet.

Le module détecte les fichiers présents dans ``data/`` (CSV, Excel, Parquet),
renomme leurs colonnes vers le schéma canonique et nettoie les types.
Aucune valeur n'est jamais inventée : si un fichier ou une colonne manque, la
visualisation concernée affiche un état vide explicite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import streamlit as st

from . import config as C
from .formatting import norm_key

SUPPORTED_SUFFIXES = (".csv", ".xlsx", ".xls", ".parquet")

_ALIAS_LOOKUP = {
    norm_key(alias): canon
    for canon, aliases in C.COLUMN_ALIASES.items()
    for alias in aliases
}


@dataclass
class Datasets:
    frames: dict[str, pd.DataFrame] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not self.frames

    def get(self, name: str) -> pd.DataFrame | None:
        return self.frames.get(name)

    def has(self, name: str, *columns: str) -> bool:
        df = self.frames.get(name)
        return df is not None and len(df) > 0 and all(c in df.columns for c in columns)

    def years(self) -> list[int]:
        found: set[int] = set()
        for name in ("entreprises", "infrastructures", "connectivite"):
            df = self.frames.get(name)
            if df is not None and "annee" in df.columns:
                found.update(int(y) for y in df["annee"].dropna().unique())
        return sorted(found)

    def values(self, column: str) -> list[str]:
        found: set[str] = set()
        for df in self.frames.values():
            if column in df.columns:
                found.update(str(v) for v in df[column].dropna().unique())
        return _sort_values(column, found)

    def prefectures_by_region(self) -> dict[str, list[str]]:
        mapping: dict[str, set[str]] = {}
        for df in self.frames.values():
            if {"region", "prefecture"} <= set(df.columns):
                pairs = df[["region", "prefecture"]].dropna().drop_duplicates()
                for region, prefecture in pairs.itertuples(index=False):
                    mapping.setdefault(str(region), set()).add(str(prefecture))
        return {k: sorted(v) for k, v in mapping.items()}


def _sort_values(column: str, values: set[str]) -> list[str]:
    if column == "region":
        known = [r for r in C.REGION_ORDER if r in values]
        return known + sorted(values - set(known))
    return sorted(values, key=lambda v: norm_key(v))


# --------------------------------------------------------------------------- #
# Lecture
# --------------------------------------------------------------------------- #
def _read_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                return pd.read_csv(path, sep=None, engine="python", encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("encodage illisible")
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"format non pris en charge : {suffix}")


def _discover(data_dir: Path) -> dict[str, Path]:
    """Associe chaque jeu de données au premier fichier reconnu."""
    if not data_dir.exists():
        return {}
    files = sorted(
        p for p in data_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
        and not p.name.startswith((".", "~$"))
    )
    by_stem = {}
    for path in files:
        by_stem.setdefault(norm_key(path.stem), path)
    found: dict[str, Path] = {}
    for dataset, stems in C.DATASET_FILES.items():
        for stem in stems:
            if norm_key(stem) in by_stem:
                found[dataset] = by_stem[norm_key(stem)]
                break
    return found


def _signature(data_dir: Path) -> tuple:
    return tuple(
        (name, path.stat().st_mtime_ns, path.stat().st_size)
        for name, path in sorted(_discover(data_dir).items())
    )


# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #
def canonical_region(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    key = norm_key(value)
    for prefix in ("region_des_", "region_de_la_", "region_du_", "region_de_", "region_"):
        if key.startswith(prefix):
            key = key[len(prefix):]
            break
    return C.REGION_ALIASES.get(key, str(value).strip())


def _to_number(series: pd.Series) -> pd.Series:
    if series.dtype == object or str(series.dtype) in ("string", "str"):
        cleaned = (
            series.astype("string")
            .str.replace("\u202f", "", regex=False)
            .str.replace("\u00a0", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        return pd.to_numeric(cleaned, errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def _normalize(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    # 1. Colonnes -> schéma canonique (premier alias rencontré l'emporte).
    rename: dict[str, str] = {}
    taken: set[str] = set()
    for col in df.columns:
        canon = _ALIAS_LOOKUP.get(norm_key(col))
        if canon and canon not in taken:
            rename[col] = canon
            taken.add(canon)
    df = df.rename(columns=rename)[list(rename.values())].copy()

    # 2. Types.
    for col in C.TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip().replace("", pd.NA)
    if "region" in df.columns:
        df["region"] = df["region"].map(canonical_region).astype("string")
    if "annee" in df.columns:
        year = df["annee"].astype("string").str.extract(r"(\d{4})")[0]
        df["annee"] = pd.to_numeric(year, errors="coerce").astype("Int64")
    for col in C.NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = _to_number(df[col])

    # 3. Mesures dérivées.
    if dataset in ("entreprises", "infrastructures") and "nombre" not in df.columns:
        df["nombre"] = 1.0
    if "investissement_mds_fcfa" not in df.columns and "investissement_fcfa" in df.columns:
        df["investissement_mds_fcfa"] = df["investissement_fcfa"] / 1e9
    if "couverture_internet_pct" in df.columns:
        col = df["couverture_internet_pct"]
        if col.notna().any() and col.max() <= 1.0:
            df["couverture_internet_pct"] = col * 100
    return df


# --------------------------------------------------------------------------- #
# API publique
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def _load(signature: tuple, data_dir: str) -> tuple[dict[str, pd.DataFrame], list[str]]:
    frames: dict[str, pd.DataFrame] = {}
    notes: list[str] = []
    for dataset, path in _discover(Path(data_dir)).items():
        try:
            df = _normalize(_read_file(path), dataset)
        except Exception as exc:  # fichier illisible : on le signale sans planter
            notes.append(f"{path.name} : lecture impossible ({exc}).")
            continue
        if df.empty or not len(df.columns):
            notes.append(f"{path.name} : aucune colonne reconnue.")
            continue
        frames[dataset] = df
        notes.append(f"{path.name} : {len(df):,} lignes, colonnes {', '.join(df.columns)}.")
    return frames, notes


def load_datasets() -> Datasets:
    data_dir = Path(C.DATA_DIR)
    frames, notes = _load(_signature(data_dir), str(data_dir))
    return Datasets(frames=frames, notes=notes)
