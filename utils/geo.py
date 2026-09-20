"""Ressources cartographiques (limites administratives du Togo)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import config as C

# Fichier optionnel : remplace la carte fournie par défaut (même structure,
# propriété `region` = nom canonique de la région, `cx`/`cy` = point d'étiquette).
CUSTOM_GEOJSON = C.DATA_DIR / "geo" / "regions.geojson"
DEFAULT_GEOJSON = C.ASSETS_DIR / "geo" / "togo_regions.geojson"


@lru_cache(maxsize=1)
def load_regions_geojson() -> dict:
    path: Path = CUSTOM_GEOJSON if CUSTOM_GEOJSON.exists() else DEFAULT_GEOJSON
    return json.loads(path.read_text(encoding="utf-8"))
