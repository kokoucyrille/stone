# Dossier des données

Déposez ici vos fichiers **réels** (CSV, `.xlsx`, `.xls` ou `.parquet`). Aucun jeu de données
n'est fourni : l'application n'invente aucune valeur.

Les fichiers peuvent aussi être envoyés depuis l'application (bouton « Charger des fichiers de
données »). Les sous-dossiers sont lus, sauf `geo/`.

**Classement automatique.** Un fichier est rangé d'après son nom (tableau ci-dessous) ; sinon
d'après ses colonnes (`indicateur` + `valeur` → indicateurs ; `type_infrastructure` →
infrastructures ; `couverture_internet_pct` → connectivité ; `region`, `secteur`, `statut`,
`emplois`… → entreprises) ; sinon d'après des mots de son nom (agence, agent, antenne, fibre,
wifi, data center, cloud… → infrastructures, avec le nom du fichier comme type). Plusieurs
fichiers du même jeu sont concaténés.

Les noms de fichiers reconnus (sans extension) :

| Jeu de données | Noms acceptés |
|---|---|
| Entreprises / acteurs | `entreprises`, `entreprises_numeriques`, `acteurs`, `ecosysteme` |
| Infrastructures | `infrastructures`, `infrastructures_numeriques`, `infra` |
| Connectivité | `connectivite`, `couverture_internet`, `acces_internet` |
| Indicateurs clés | `indicateurs`, `indicateurs_cles` |

Les en-têtes sont normalisés (accents, majuscules, espaces et apostrophes ignorés) :
« Année de création », `annee_creation` et `Annee` désignent la même colonne.
Toutes les colonnes sont facultatives : une visualisation dont la colonne manque affiche
un état vide qui nomme cette colonne.

## `entreprises` — une ligne par entreprise (ou par groupe si `nombre` est fourni)

| Colonne canonique | Synonymes reconnus | Usage |
|---|---|---|
| `region` | region, nom_region, admin1 | filtre, carte, tableaux |
| `prefecture` | prefecture, nom_prefecture, admin2 | filtre, Top 5 |
| `secteur` | secteur, secteur_activite, secteur_d_activite, domaine | filtre, anneau |
| `annee` | annee, year, exercice, annee_creation | période, évolution |
| `type_acteur` | type_acteur, acteur, categorie_acteur | filtre, Écosystème |
| `statut` | statut, status, etat | filtre, Écosystème |
| `taille` | taille, taille_entreprise | filtre avancé |
| `niveau_connexion` | niveau_connexion, niveau_de_connexion_internet | filtre avancé |
| `nombre` | nombre, nb, quantite, count | pondération (1 par défaut) |
| `emplois` | emplois, emplois_crees, nb_emplois | KPI Emplois créés |
| `investissement_mds_fcfa` | investissement_mds_fcfa | KPI Investissements |
| `investissement_fcfa` | investissement_fcfa | converti en Mds F CFA |

## `infrastructures`

`type_infrastructure` (ex. Fibre optique, Points d'accès Wi-Fi, Data center, Cloud & hébergement),
`region`, `prefecture`, `annee` (optionnelle), `nombre` (ou `quantite`, 1 par défaut).
Les 4 types de la maquette sont reconnus par mots-clés (fibre, wifi, data center, cloud) ;
les autres types remplissent les places libres du bloc de synthèse.

## `connectivite`

`region`, `prefecture`, `annee`, `couverture_internet_pct` (0–100 ou 0–1, converti
automatiquement), `population` (optionnelle, pour la moyenne pondérée).

## `indicateurs`

`indicateur`, `valeur`, `annee` (optionnelle), `unite` (`%` pour un pourcentage).
Libellés reconnus par mot-clé : croissance, emploi, PIB, objectif.
Seuls les indicateurs présents sont affichés.

## Régions

Les noms sont normalisés : « Région Maritime » → Maritime, « Centre » → Centrale,
« Lomé » ou « Golfe » → Grand Lomé.
