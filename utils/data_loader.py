"""Chargement des données réelles du projet.

Le module scanne ``data/`` (sous-dossiers compris ; CSV, Excel, Parquet), renomme
les colonnes vers le schéma canonique, nettoie les types et **classe chaque
fichier** dans un jeu de données (entreprises, infrastructures, connectivité,
indicateurs) d'après son nom, sinon d'après ses colonnes. Plusieurs fichiers d'un
même jeu sont concaténés.

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
IGNORED_DIRS = {"geo"}

_ALIAS_LOOKUP = {
    norm_key(alias): canon
    for canon, aliases in C.COLUMN_ALIASES.items()
    for alias in aliases
}
_ENTREPRISE_COLUMNS = {
    "region", "prefecture", "secteur", "type_acteur", "statut", "taille",
    "niveau_connexion", "emplois", "investissement_mds_fcfa", "investissement_fcfa",
}
_GENERIC_INFRA_STEMS = {norm_key(s) for s in C.DATASET_FILES["infrastructures"]}


@dataclass
class FileInfo:
    """Diagnostic d'un fichier lu (affiché si un fichier n'est pas reconnu)."""
    name: str
    dataset: str | None
    rows: int = 0
    columns: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Datasets:
    frames: dict[str, pd.DataFrame] = field(default_factory=dict)
    files: list[FileInfo] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not self.frames

    @property
    def unrecognized(self) -> list[FileInfo]:
        return [f for f in self.files if f.dataset is None]

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


def candidate_files(data_dir: Path) -> list[Path]:
    """Fichiers de données du dossier (sous-dossiers inclus), hors `geo/` et fichiers cachés."""
    if not data_dir.exists():
        return []
    found = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        parts = path.relative_to(data_dir).parts
        if any(p.startswith((".", "~$", "_")) or p.lower() in IGNORED_DIRS for p in parts):
            continue
        found.append(path)
    return found


def _signature(data_dir: Path) -> tuple:
    return tuple(
        (str(p.relative_to(data_dir)), p.stat().st_mtime_ns, p.stat().st_size)
        for p in candidate_files(data_dir)
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


def _canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme les colonnes reconnues vers le schéma canonique (les autres sont écartées)."""
    rename: dict[str, str] = {}
    taken: set[str] = set()
    for col in df.columns:
        canon = _ALIAS_LOOKUP.get(norm_key(col))
        if canon and canon not in taken:
            rename[col] = canon
            taken.add(canon)
    return df.rename(columns=rename)[list(rename.values())].copy()


def _pretty_stem(stem: str) -> str:
    text = stem.replace("_", " ").replace("-", " ").strip()
    return text[:1].upper() + text[1:]


def classify(path: Path, df: pd.DataFrame) -> str | None:
    """Jeu de données d'un fichier : nom reconnu, sinon colonnes, sinon mots-clés du nom."""
    stem = norm_key(path.stem)
    for dataset, stems in C.DATASET_FILES.items():
        if stem in {norm_key(s) for s in stems}:
            return dataset
    cols = set(df.columns)
    if {"indicateur", "valeur"} <= cols:
        return "indicateurs"
    if "type_infrastructure" in cols:
        return "infrastructures"
    if "couverture_internet_pct" in cols and not cols & {
        "secteur", "emplois", "type_acteur", "statut", "taille"
    }:
        return "connectivite"
    if any(word in stem for word in C.INFRA_STEM_WORDS):
        return "infrastructures"
    if cols & _ENTREPRISE_COLUMNS:
        return "entreprises"
    return None


def _clean(df: pd.DataFrame, dataset: str, path: Path) -> pd.DataFrame:
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

    if dataset == "infrastructures" and "type_infrastructure" not in df.columns \
            and norm_key(path.stem) not in _GENERIC_INFRA_STEMS:
        df["type_infrastructure"] = _pretty_stem(path.stem)  # libellé tiré du nom du fichier
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
def _load(signature: tuple, data_dir: str) -> tuple[dict[str, pd.DataFrame], list[FileInfo]]:
    root = Path(data_dir)
    parts: dict[str, list[pd.DataFrame]] = {}
    files: list[FileInfo] = []
    for path in candidate_files(root):
        rel = str(path.relative_to(root))
        try:
            raw = _read_file(path)
        except Exception as exc:  # fichier illisible : on le signale sans planter
            files.append(FileInfo(rel, None, note=f"lecture impossible ({exc})"))
            continue
        df = _canonicalize(raw)
        dataset = classify(path, df) if len(df.columns) else None
        if dataset is None:
            files.append(FileInfo(rel, None, len(raw), [str(c) for c in raw.columns],
                                  "aucune colonne reconnue"))
            continue
        df = _clean(df, dataset, path)
        parts.setdefault(dataset, []).append(df)
        files.append(FileInfo(rel, dataset, len(df), list(df.columns)))
    frames = {name: pd.concat(dfs, ignore_index=True, sort=False) for name, dfs in parts.items()}
    return frames, files


def load_datasets() -> Datasets:
    data_dir = Path(C.DATA_DIR)
    frames, files = _load(_signature(data_dir), str(data_dir))
    return Datasets(frames=frames, files=files)


def save_uploads(uploads, dest: Path) -> list[str]:
    """Enregistre des fichiers téléversés dans `dest` (nom de base uniquement)."""
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for upload in uploads:
        name = Path(str(upload.name)).name
        if Path(name).suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        (dest / name).write_bytes(upload.getvalue())
        saved.append(name)
    return saved
