"""Tests de fumée : l'application démarre, navigue et filtre sans erreur.

Le jeu de données ci-dessous est une *fixture de test* générée dans un dossier
temporaire ; il n'est jamais lu par l'application en dehors de ces tests.
Lancer :  pytest -q
"""
import importlib
import os
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app.py")
PAGES = ["dashboard", "territoires", "secteurs", "infrastructures", "ecosysteme"]


def _fresh_app(data_dir: Path) -> AppTest:
    os.environ["TDI_DATA_DIR"] = str(data_dir)
    for name in [m for m in sys.modules if m.split(".")[0] in ("utils", "components", "views")]:
        del sys.modules[name]
    importlib.invalidate_caches()
    sys.path.insert(0, str(ROOT))
    return AppTest.from_file(APP, default_timeout=60)


@pytest.fixture
def empty_dir(tmp_path):
    return tmp_path


@pytest.fixture
def sample_dir(tmp_path):
    pd.DataFrame({
        "Région": ["Kara", "Kara", "Maritime", "Région Maritime", "Savanes"],
        "Préfecture": ["Kozah", "Bassar", "Zio", "Vo", "Oti"],
        "Secteur d'activité": ["Fintech", "Télécoms", "Fintech", "EdTech", "Télécoms"],
        "Année": [2023, 2024, 2024, 2025, 2025],
        "Emplois": [10, 5, 8, 12, 3],
    }).to_csv(tmp_path / "entreprises.csv", index=False)
    pd.DataFrame({
        "region": ["Kara", "Maritime"], "annee": [2025, 2025],
        "type_infrastructure": ["Fibre optique", "Data center"], "quantite": [4, 1],
    }).to_csv(tmp_path / "infrastructures.csv", index=False)
    return tmp_path


def _click(at: AppTest, page: str) -> AppTest:
    return at.button(key=f"nav_{page}").click().run()


@pytest.mark.parametrize("page", PAGES)
def test_pages_without_data(empty_dir, page):
    at = _fresh_app(empty_dir).run()
    at = _click(at, page) if page != "dashboard" else at
    assert not at.exception, at.exception


@pytest.mark.parametrize("page", PAGES)
def test_pages_with_data(sample_dir, page):
    at = _fresh_app(sample_dir).run()
    at = _click(at, page) if page != "dashboard" else at
    assert not at.exception, at.exception


def test_region_names_are_normalised(sample_dir):
    at = _fresh_app(sample_dir).run()
    options = at.selectbox(key="f_region").options
    assert "Maritime" in options and "Région Maritime" not in options


def test_filters_drive_kpis(sample_dir):
    at = _fresh_app(sample_dir).run()
    html = " ".join(m.value for m in at.markdown)
    assert ">5<" in html  # 5 entreprises au total, aucune valeur inventée

    at.selectbox(key="f_region").select("Kara").run()
    assert not at.exception
    html = " ".join(m.value for m in at.markdown)
    assert ">2<" in html  # 2 entreprises à Kara
    assert at.selectbox(key="f_prefecture").options == ["Toutes les préfectures", "Bassar", "Kozah"]

    at.button(key="btn_reset").click().run()
    assert at.selectbox(key="f_region").value == "Toutes les régions"


def test_missing_data_never_shows_numbers(empty_dir):
    at = _fresh_app(empty_dir).run()
    html = " ".join(m.value for m in at.markdown)
    assert "Donnée non disponible" in html


def test_filters_are_active_without_data(empty_dir):
    at = _fresh_app(empty_dir).run()
    assert not at.exception
    region = at.selectbox(key="f_region")
    assert "Kara" in region.options and not region.disabled
    assert at.selectbox(key="f_periode").options[0] == "2020 - 2025"
    region.select("Kara").run()
    assert not at.exception  # le filtre est appliqué sans planter, aucune valeur inventée
    assert "Donnée non disponible" in " ".join(m.value for m in at.markdown)


def test_reference_lists_are_dropped_once_data_is_loaded(sample_dir):
    at = _fresh_app(sample_dir).run()
    # « Télécoms » vient de la liste de référence : absent des données de la fixture.
    assert "Télécoms" in at.selectbox(key="f_secteur").options  # présent dans la fixture
    assert "Services IT" not in at.selectbox(key="f_secteur").options


def test_files_are_classified_by_columns(tmp_path):
    (tmp_path / "sous_dossier").mkdir()
    pd.DataFrame({"Région": ["Kara"], "Type d'infrastructure": ["Fibre optique"], "Nombre": [3]}
                 ).to_csv(tmp_path / "sous_dossier" / "mes_sites.csv", index=False)
    pd.DataFrame({"region": ["Kara", "Maritime"], "prefecture": ["Kozah", "Zio"]}
                 ).to_csv(tmp_path / "agences_moov.csv", index=False)
    pd.DataFrame({"region": ["Kara"], "prefecture": ["Bassar"]}
                 ).to_csv(tmp_path / "agences_togocom.csv", index=False)
    pd.DataFrame({"colonne_inconnue": [1]}).to_csv(tmp_path / "inconnu.csv", index=False)
    _fresh_app(tmp_path)
    from utils.data_loader import load_datasets
    ds = load_datasets()
    assert set(ds.frames) == {"infrastructures"}
    infra = ds.frames["infrastructures"]
    assert len(infra) == 4 and infra["nombre"].sum() == 6
    assert set(infra["type_infrastructure"]) == {"Fibre optique", "Agences moov", "Agences togocom"}
    assert [f.name for f in ds.unrecognized] == ["inconnu.csv"]


def test_save_uploads_keeps_only_base_name(tmp_path):
    _fresh_app(tmp_path)
    from utils.data_loader import save_uploads

    class Upload:
        name = "../evil.csv"

        def getvalue(self):
            return b"region\nKara\n"

    class Refused(Upload):
        name = "script.py"

    assert save_uploads([Upload(), Refused()], tmp_path / "data") == ["evil.csv"]
    assert (tmp_path / "data" / "evil.csv").exists() and not (tmp_path / "evil.csv").exists()
