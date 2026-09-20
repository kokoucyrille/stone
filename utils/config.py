"""Configuration centrale de TOGO DIGITAL INTELLIGENCE.

Tout ce qui relève de la charte graphique, du schéma de données attendu et
des libellés se règle ici, sans toucher au reste du code.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"
STYLES_DIR = ROOT / "styles"

# Dossier des données : surchargeable via la variable d'environnement TDI_DATA_DIR.
DATA_DIR = Path(os.environ.get("TDI_DATA_DIR", ROOT / "data"))

APP_TITLE = "TOGO DIGITAL INTELLIGENCE"
APP_SUBTITLE = (
    "Plateforme d'intelligence territoriale pour le pilotage de l'économie "
    "numérique du Togo."
)
MOTTO = "Travail • Liberté • Patrie"
SLOGAN_LINES = ("Le Togo,", "plus connecté,", "plus fort !")

# --------------------------------------------------------------------------- #
# Palette
# --------------------------------------------------------------------------- #
COLORS = {
    "green": "#006A4E",          # vert institutionnel (drapeau)
    "green_dark": "#02403A",     # sidebar
    "emerald": "#0E9F6E",        # variations positives
    "yellow": "#FFCE00",
    "red": "#D21034",
    "navy": "#0B1F33",           # titres, chiffres
    "slate": "#334155",          # texte secondaire
    "muted": "#64748B",
    "grid": "#E6EBF1",
    "bg": "#F5F7FA",
    "card": "#FFFFFF",
    "empty": "#E9EEF3",
}

# Une couleur stable par région : le même vert/jaune/orange se retrouve
# dans la carte, la légende et le graphique d'accès à Internet.
REGION_ORDER = ["Grand Lomé", "Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
REGION_COLORS = {
    "Grand Lomé": "#064E3B",
    "Maritime": "#0F8F5F",
    "Plateaux": "#5FAF3D",
    "Centrale": "#B5CC3A",
    "Kara": "#F2B01E",
    "Savanes": "#F28C28",
}
FALLBACK_COLORS = ["#0F8F5F", "#5FAF3D", "#B5CC3A", "#F2B01E", "#F28C28", "#2F80ED"]

SECTOR_COLORS = ["#0B6B4F", "#FFCE00", "#2F80ED", "#7B3FBF", "#F2542D"]
EXTRA_COLORS = ["#0F8F5F", "#F28C28", "#5FAF3D", "#06B6D4", "#E11D48", "#8E9AAF"]
OTHER_COLOR = "#A0A7B0"
BAR_GRADIENT = ["#0B6B4F", "#4DA35A", "#9BC53D", "#D4D23A", "#FFCE00"]

# Normalisation des noms de régions (clé normalisée -> libellé canonique).
REGION_ALIASES = {
    "maritime": "Maritime",
    "plateaux": "Plateaux",
    "plateau": "Plateaux",
    "centrale": "Centrale",
    "centre": "Centrale",
    "kara": "Kara",
    "savanes": "Savanes",
    "savane": "Savanes",
    "grand_lome": "Grand Lomé",
    "lome": "Grand Lomé",
    "golfe": "Grand Lomé",
}

# Régions absentes du GeoJSON (ex. « Grand Lomé », incluse dans le polygone
# Maritime) mais localisables par un point : elles sont tracées en pastille.
GEO_POINTS = {"Grand Lomé": (6.1725, 1.2314)}  # (latitude, longitude) de Lomé

# --------------------------------------------------------------------------- #
# Schéma de données attendu (voir data/README.md)
# --------------------------------------------------------------------------- #
# Interprétation de la colonne `annee` des entreprises / infrastructures :
#   "cumul"      -> année de création / mise en service : le stock à l'année N
#                   est la somme de toutes les lignes dont annee <= N ;
#   "instantane" -> chaque année est une photographie complète du parc.
STOCK_MODE = os.environ.get("TDI_STOCK_MODE", "cumul")

# Noms de fichiers reconnus (sans extension, insensible à la casse et aux
# accents) pour chaque jeu de données. Extensions : csv, xlsx, xls, parquet.
DATASET_FILES = {
    "entreprises": ["entreprises", "entreprises_numeriques", "acteurs", "ecosysteme"],
    "infrastructures": ["infrastructures", "infrastructures_numeriques", "infra"],
    "connectivite": ["connectivite", "couverture_internet", "acces_internet"],
    "indicateurs": ["indicateurs", "indicateurs_cles"],
}

# Colonne canonique -> noms acceptés dans les fichiers (avant normalisation).
COLUMN_ALIASES = {
    "region": ["region", "regions", "nom_region", "admin1"],
    "prefecture": ["prefecture", "prefectures", "nom_prefecture", "admin2"],
    "secteur": ["secteur", "secteur_activite", "secteur_d_activite", "domaine"],
    "annee": ["annee", "year", "exercice", "annee_creation", "annee_de_creation"],
    "type_acteur": ["type_acteur", "type_d_acteur", "acteur", "categorie_acteur"],
    "statut": ["statut", "status", "etat"],
    "taille": ["taille", "taille_entreprise", "taille_de_l_entreprise"],
    "niveau_connexion": [
        "niveau_connexion", "niveau_de_connexion", "niveau_connexion_internet",
        "niveau_de_connexion_internet",
    ],
    "nombre": [
        "nombre", "nb", "quantite", "nb_entreprises", "effectif_entreprises", "count",
    ],
    "emplois": ["emplois", "emplois_crees", "nb_emplois", "effectifs"],
    "investissement_mds_fcfa": [
        "investissement_mds_fcfa", "investissements_mds_fcfa", "investissement_mds",
    ],
    "investissement_fcfa": ["investissement_fcfa", "investissements_fcfa", "investissement"],
    "type_infrastructure": [
        "type_infrastructure", "type_d_infrastructure", "infrastructure", "type_infra",
    ],
    "couverture_internet_pct": [
        "couverture_internet_pct", "couverture_internet", "taux_couverture",
        "taux_couverture_internet", "taux_acces_internet", "acces_internet_pct",
    ],
    "population": ["population", "pop"],
    "indicateur": ["indicateur", "nom_indicateur", "libelle"],
    "valeur": ["valeur", "value"],
    "unite": ["unite", "unit"],
}

# Colonnes numériques à forcer.
NUMERIC_COLUMNS = [
    "nombre", "emplois", "investissement_mds_fcfa", "investissement_fcfa",
    "couverture_internet_pct", "population", "valeur",
]
TEXT_COLUMNS = [
    "region", "prefecture", "secteur", "type_acteur", "statut", "taille",
    "niveau_connexion", "type_infrastructure", "indicateur", "unite",
]

# Infrastructures mises en avant dans le bloc de synthèse (ordre de la maquette).
# (libellé affiché, mots-clés de reconnaissance dans `type_infrastructure`, icône)
INFRA_TILES = [
    ("Fibre optique", ("fibre",), "cable"),
    ("Points d'accès Wi-Fi", ("wifi", "wi_fi", "hotspot"), "wifi"),
    ("Data centers", ("data_center", "datacenter", "centre_de_donnees"), "database"),
    ("Cloud & hébergement", ("cloud", "hebergement"), "cloud"),
]
INFRA_DEFAULT_ICON = "router"
INFRA_MAX_TILES = 4

# Indicateurs clés du bloc inférieur droit (ordre de la maquette).
# (libellé, mots-clés, icône, décimales)
KEY_INDICATORS = [
    ("Croissance annuelle", ("croissance",), "trending_up"),
    ("Taux d'emploi numérique", ("emploi",), "groups"),
    ("Contribution au PIB", ("pib",), "public"),
    ("Objectif 2025", ("objectif",), "track_changes"),
]

ALL_LABELS = {
    "region": "Toutes les régions",
    "prefecture": "Toutes les préfectures",
    "secteur": "Tous les secteurs",
    "type_acteur": "Tous les types",
    "statut": "Tous les statuts",
    "taille": "Toutes",
    "niveau_connexion": "Tous",
    "type_infrastructure": "Tous",
}

PAGES = [
    ("dashboard", "Tableau de bord", "home"),
    ("territoires", "Territoires", "location_on"),
    ("secteurs", "Secteurs", "bar_chart"),
    ("infrastructures", "Infrastructures", "dns"),
    ("ecosysteme", "Écosystème", "hub"),
]
