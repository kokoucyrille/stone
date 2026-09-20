# Audit « Ergonomie, clarté visuelle et facilité de navigation »

Grille de contrôle appliquée au tableau de bord, mesures faites dans un vrai navigateur
(Chromium, jeu de test synthétique, police de secours sans Inter).

| Sous-critère | Constat initial | Amélioration | Contrôle |
|---|---|---|---|
| **Navigation** – retrouver sa vue | Un rafraîchissement ramenait au tableau de bord, filtres perdus ; aucun lien partageable | La page, la période et les filtres sont écrits dans l'adresse du navigateur (`?page=…&region=Kara\|Maritime`) et restitués à l'ouverture | Testé : rafraîchissement et lien partagé restituent page + filtres + comparaison |
| **Navigation** – passer du synthétique au détail | Il fallait deviner quelle vue détaille quelle carte | Flèche « Détail » dans l'en-tête des cartes carte / évolution / secteurs / Top 5 / accès Internet / infrastructures | Testé au clic (URL mise à jour) |
| **Navigation** – onglets réduits à des icônes (< 1100 px) | Libellé absent pour les lecteurs d'écran | Libellé masqué visuellement mais conservé pour l'accessibilité (le nom lu inclut le nom de l'icône, ex. « location_on Territoires » : limite de Streamlit) | Vérifié dans l'arbre d'accessibilité |
| **Ergonomie** – savoir ce qui est affiché | Filtres visibles seulement dans la sidebar | Barre « Vue active » (période, filtres, comparaison A / B) au-dessus des KPI, absente quand aucun filtre n'est actif | Testé |
| **Ergonomie** – tenir sur l'écran | 86 px de défilement à 1536 × 900 | Bandeau, KPI et cartes resserrés : tout le tableau de bord + la ligne de sources tient à 1536 × 900 | Mesuré : 0 px de défilement |
| **Ergonomie** – clavier | Aucun contour de focus | Contour de 2 px sur boutons, listes et cases (jaune sur fond vert) | Mesuré (`outline: 2px`) |
| **Ergonomie** – place pour présenter | Sidebar impossible à replier | Chevron de repli toujours visible ; bouton de réouverture sous la barre | Testé (248 px → 0 → 248 px) |
| **Clarté** – contrastes (WCAG AA ≥ 4,5:1) | Variation verte 3,4:1 ; parts en légende 4,3:1 ; étiquettes orange 2,5:1 | Vert `#0A7A50` (5,4:1), bleu `#3D6A9C` (5,6:1), étiquettes de courbes en bleu nuit | Calculé |
| **Clarté** – lisibilité | 55 textes sous 11,5 px ; axe de l'évolution sans unité | Libellés KPI, astuce et graphiques à 11 px minimum ; axe « Entreprises » ; titres tronqués complétés par une info-bulle | Mesuré : un seul texte sous 11 px hors graphiques (la devise, 9,5 px, décorative) |
| **Clarté** – définitions et provenance | Aucune définition des KPI ni source | Info-bulle de définition sur chaque KPI ; ligne « Sources · année de référence · date de mise à jour » | Testé |

## Points restant à traiter

- Défilement inévitable sous ~800 px de hauteur (portables 1366 × 768) : le tableau de bord passe en une
  colonne sous 1100 px de large mais n'est pas conçu pour tenir sans défilement à cette taille.
- Le message « You can only select up to 2 options » de Streamlit reste en anglais.
- La police Inter n'a pas pu être testée hors ligne ; les largeurs de titres peuvent varier légèrement.
