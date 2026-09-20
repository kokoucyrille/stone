# TOGO DIGITAL INTELLIGENCE

Plateforme d'intelligence territoriale pour le pilotage de l'économie numérique du Togo,
application **Streamlit** reproduisant la maquette de référence (barre de navigation,
sidebar de filtres, bandeau, 5 KPI épurés, grille de visualisations).

> **Aucune donnée n'est simulée.** Sans fichier dans `data/`, chaque carte affiche
> « Donnée non disponible » et indique le fichier et les colonnes attendus.

## Installation et lancement

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501.
Pour lire un autre dossier de données : `TDI_DATA_DIR=/chemin/vers/donnees streamlit run app.py`.

## Structure

```
app.py                  point d'entrée (config, CSS, navigation, filtres, vue active)
views/                  une vue par menu : dashboard, territoires, secteurs, infrastructures, ecosysteme
components/             layout.py (barre, bandeau, cartes, états vides), kpi.py, charts.py (Plotly)
utils/                  config.py (palette, schéma, alias), data_loader.py, filters.py, metrics.py, geo.py
styles/main.css         charte graphique complète
assets/                 logo, drapeau, photo du bandeau, géojson des régions
data/                   VOS fichiers de données (voir data/README.md)
tests/test_app.py       tests de fumée (pytest)
```

## Données et filtres

Déposez vos fichiers (CSV, Excel ou Parquet) dans `data/`, **ou** utilisez le bouton
« Charger des fichiers de données » affiché sous le bandeau tant que des jeux manquent
(les fichiers sont enregistrés dans `data/`). Les fichiers sont rechargés dès qu'ils changent.

- **Classement automatique** : chaque fichier est rangé selon son nom (`entreprises`,
  `infrastructures`, `connectivite`, `indicateurs`), sinon selon ses colonnes, sinon selon des
  mots de son nom (agence, antenne, fibre, data center… → infrastructures ; le libellé du type
  est alors tiré du nom du fichier). Sous-dossiers acceptés ; plusieurs fichiers d'un même
  jeu sont concaténés. Un fichier non reconnu est signalé avec les colonnes lues.
- **Colonnes** : reconnues avec ou sans accents et via des synonymes (`data/README.md`,
  `utils/config.py` › `COLUMN_ALIASES`).
- **Filtres** : les choix viennent exclusivement de vos données. Un filtre dont la colonne
  n'existe pas est grisé avec une infobulle qui explique pourquoi. Avant tout chargement,
  Période, Région et Secteur restent utilisables à partir de listes de référence
  (`PERIOD_FALLBACK`, `REFERENCE_OPTIONS` dans `utils/config.py`) et la région choisie
  s'illumine sur la carte ; aucune valeur n'est simulée.

## Règles de calcul

- **Année de référence** = fin de la période choisie dans la sidebar.
- **Entreprises, emplois, investissements, infrastructures** : stock à l'année de référence,
  variation en % par rapport à l'année précédente, affichée uniquement si les données la permettent.
  Par défaut `annee` est lue comme une **année de création / mise en service** (cumul). Si chaque
  année est une photographie complète du parc : `TDI_STOCK_MODE=instantane`.
- **Couverture Internet** : dernière photographie disponible à ou avant l'année de référence,
  moyenne pondérée par `population` si la colonne existe ; variation en **points**.
- **Croissance annuelle** (indicateurs clés) : reprise de `indicateurs` si présente, sinon
  calculée à partir de l'évolution du nombre d'entreprises. Les autres indicateurs ne s'affichent
  que s'ils sont fournis.
- **Filtres** : chacun s'applique aux jeux de données qui possèdent la colonne correspondante
  (ex. le secteur filtre les entreprises, pas les infrastructures). Région et préfecture
  s'appliquent à tous.

## Personnalisation

Tout se règle dans `utils/config.py` : palette, couleurs par région, synonymes de colonnes,
types d'infrastructure mis en avant, indicateurs clés, libellés. La carte utilise
`assets/geo/togo_regions.geojson` (5 régions officielles, Natural Earth, domaine public) ;
déposez `data/geo/regions.geojson` (propriétés `region`, `cx`, `cy`) pour la remplacer.

## Limites connues

- La photo du bandeau (`assets/banner_lome.jpg`) est recadrée dans la maquette : basse
  résolution. Remplacez-la par une photographie de Lomé (mêmes proportions, ~1200 × 250 px).
- « Grand Lomé » (6e région de la maquette) n'existe pas dans le géojson officiel à 5 régions :
  si vos données l'utilisent, elle est tracée en pastille sur Lomé.
- La police Inter est chargée depuis Google Fonts ; hors connexion, une police système est utilisée.
- Le texte au bas de la sidebar était illisible sur la maquette : « Économie numérique /
  Territoire du Togo / plus compétitif » (modifiable dans `utils/filters.py`).

## Tests

```bash
pip install pytest
pytest -q
```
Les tests utilisent de petites fixtures générées dans un dossier temporaire, jamais lues par l'application.
