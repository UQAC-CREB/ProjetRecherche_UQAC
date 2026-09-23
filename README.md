# Hub des projets de recherche — UQAC

Application web statique (HTML + MapLibre GL JS, sans backend) permettant de
présenter les projets de recherche d'importance à l'UQAC sur une carte du
Québec. Pensée pour être **légère, déployée directement depuis GitHub
(GitHub Pages)** et **intégrée dans une StoryMap ArcGIS** via `<iframe>`.

Ceci est une **ébauche / preuve de concept**, construite à partir de deux
projets d'exemple (Abir Arbi, Gabriel Davidson) pour démontrer le
fonctionnement aux chercheur(-euse)s qui seront sollicité(e)s.

## Fonctionnement

- La carte (fond de carte [OpenFreeMap Positron](https://openfreemap.org/))
  affiche un point pour chaque projet, positionné à ses coordonnées centrales.
- Un clic sur un point (ou sur la liste dans le panneau de gauche) :
  1. zoome/ajuste automatiquement la carte sur l'étendue des données
     géospatiales du projet ;
  2. affiche ces données géospatiales (polygones, placettes, etc.) sur la carte ;
  3. affiche dans le panneau de gauche la description du projet et, si
     disponibles, des photos associées.
- Le bouton « ← Retour à la liste » réinitialise la vue sur l'ensemble du Québec.

## Ajouter un nouveau projet de recherche

1. Créer un dossier `data/<NomChercheur>/` contenant :
   - `Description_projet.txt` — mêmes 2 premières lignes que les exemples :
     ```
     Coordonnées centrales projet:
     XX,XXXXXXX°W YY,YYYYYYY°N

     Description:
     <texte libre>
     ```
   - les shapefiles (`.shp` + fichiers associés) du projet
2. (Optionnel) Déposer des photos dans `photos/<NomChercheur>/` (jpg/jpeg/png/webp)
3. Ajouter une entrée dans le dictionnaire `PROJECTS` de
   [transformation_donnees.py](transformation_donnees.py) (titre, libellés des
   couches, type `fill` ou `circle`)
4. Régénérer les données :
   ```
   python transformation_donnees.py
   ```
   Ceci met à jour `data/projects.json` et `data/geo/<NomChercheur>/*.geojson`
   (géométries reprojetées en WGS84 et simplifiées pour rester légères).
5. Commiter les fichiers générés (ils sont versionnés — pas de build côté
   serveur, l'app charge directement ces fichiers statiques).

## Tester localement

Depuis ce dossier :

```
npx serve .
```

puis ouvrir l'URL affichée (ex. http://localhost:3000). `npx serve` évite les
problèmes CORS/fetch que donnerait un simple double-clic sur `index.html`.

## Déploiement (GitHub Pages)

1. Pousser ce dépôt sur `github.com/uqac-creb/<nom-du-repo>`
2. Dans **Settings → Pages**, choisir la branche `main` et le dossier `/ (root)`
3. L'app sera servie à `https://uqac-creb.github.io/<nom-du-repo>/`
4. Dans ArcGIS StoryMap, intégrer cette URL via un bloc **Embed** (iframe)

## Structure

```
index.html                   ← toute l'application (HTML+CSS+JS, aucune dépendance de build)
transformation_donnees.py    ← conversion shapefiles → GeoJSON + génération de projects.json
data/
  <NomChercheur>/             ← données sources (description + shapefiles)
  geo/<NomChercheur>/*.geojson ← données générées, utilisées par l'app
  projects.json                ← métadonnées générées, utilisées par l'app
photos/<NomChercheur>/        ← photos optionnelles associées au projet
```
