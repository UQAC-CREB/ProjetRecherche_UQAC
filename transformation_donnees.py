"""
Convertit les données brutes (data/<Chercheur>/Description_projet.txt + shapefiles)
en fichiers légers utilisés par l'app web statique (index.html) :

  - data/projects.json         -> métadonnées + description + point central + liste des couches
  - data/geo/<Chercheur>/*.geojson -> couches géospatiales reprojetées en WGS84 (EPSG:4326)

Pour ajouter un(e) nouveau/nouvelle chercheur(-euse) :
  1. Créer data/<NomChercheur>/Description_projet.txt avec la structure :
       Coordonnées centrales projet:
       XX,XXXXXXX°W YY,YYYYYYY°N

       Résumé:
       <texte court affiché dans le panneau — c'est celui-ci qui est utilisé
       par l'app ; s'il est absent, la "Description" complète sert de repli>

       Description:
       <texte complet, conservé comme référence>
  2. Déposer ses shapefiles (.shp + fichiers associés) dans le même dossier
  3. Ajouter une entrée dans PROJECTS ci-dessous (titre + libellés des couches)
  4. Relancer : python transformation_donnees.py
  5. (Optionnel) déposer 2-3 photos du site dans photos/<NomChercheur>/

Nécessite geopandas (déjà présent dans l'environnement conda utilisé pour ce projet).
"""

import json
import re
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
GEO_OUT_DIR = DATA_DIR / "geo"
PHOTOS_DIR = ROOT / "photos"

# Avatar générique (silhouette) réutilisé pour tous les profils tant qu'une
# vraie photo n'a pas été fournie.
DEFAULT_AVATAR = "assets/avatar-placeholder.svg"

# ── Config par chercheur ──────────────────────────────────────────────────
# key = nom du dossier dans data/
# layers = liste des shapefiles à publier sur la carte, avec un libellé FR et
#          un type ('fill' pour polygones, 'circle' pour points)
PROJECTS = {
    "AbirArbi": {
        "titre": "Régénération après coupe de récupération post-feu",
        "chercheur": "Abir Arbi",
        "layers": [
            {"file": "FEU_395", "label": "Zone brûlée (feu 395)", "type": "fill"},
            {"file": "XY_site", "label": "Placettes d'échantillonnage", "type": "circle"},
        ],
    },
    "GabrielDavidson": {
        "titre": "Ensemencement aérien post-feu en forêt boréale",
        "chercheur": "Gabriel Davidson",
        "layers": [
            {"file": "Reserve_assinica", "label": "Réserve Assinica (secteur d'étude)", "type": "fill"},
        ],
    },
}

COORD_RE = re.compile(
    r"([\d,]+)\s*°?\s*W\s+([\d,]+)\s*°?\s*N", re.IGNORECASE
)


def parse_description(path: Path):
    text = path.read_text(encoding="utf-8")
    m = COORD_RE.search(text)
    if not m:
        raise ValueError(f"Coordonnées introuvables dans {path}")
    lon = -float(m.group(1).replace(",", "."))
    lat = float(m.group(2).replace(",", "."))

    # Le panneau de gauche affiche le "Résumé" (texte court) s'il existe ;
    # sinon on retombe sur la "Description" complète.
    resume_match = re.search(
        r"Résumé\s*:\s*\n(.*?)(?=\n\s*Description\s*:|\Z)", text, re.DOTALL
    )
    if resume_match:
        description = resume_match.group(1).strip()
    else:
        parts = re.split(r"Description\s*:\s*\n", text, maxsplit=1)
        description = parts[1].strip() if len(parts) > 1 else text.strip()

    return lon, lat, description


# Tolérance de simplification (degrés) — ~10-15 m à cette latitude.
# Les shapefiles sources sont souvent très détaillés (dizaines de milliers de
# sommets) alors que l'app n'en a pas besoin pour un usage de type "hub".
SIMPLIFY_TOLERANCE = 0.00015


def convert_layer(researcher_dir: Path, out_dir: Path, layer_file: str):
    shp_path = researcher_dir / f"{layer_file}.shp"
    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        raise ValueError(f"CRS manquant pour {shp_path}")
    gdf = gdf.to_crs(4326)
    if gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        gdf["geometry"] = gdf.geometry.simplify(
            SIMPLIFY_TOLERANCE, preserve_topology=True
        )
    out_path = out_dir / f"{layer_file}.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    return out_path.relative_to(ROOT).as_posix()


def list_photos(researcher_key: str):
    folder = PHOTOS_DIR / researcher_key
    if not folder.exists():
        return []
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return [
        f"photos/{researcher_key}/{p.name}"
        for p in sorted(folder.iterdir())
        if p.suffix.lower() in exts
    ]


def main():
    GEO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    projects_out = []

    for key, cfg in PROJECTS.items():
        researcher_dir = DATA_DIR / key
        desc_path = researcher_dir / "Description_projet.txt"
        lon, lat, description = parse_description(desc_path)

        out_dir = GEO_OUT_DIR / key
        out_dir.mkdir(parents=True, exist_ok=True)

        layers_out = []
        for layer in cfg["layers"]:
            geojson_path = convert_layer(researcher_dir, out_dir, layer["file"])
            layers_out.append(
                {"label": layer["label"], "type": layer["type"], "file": geojson_path}
            )
            print(f"  {geojson_path}")

        projects_out.append(
            {
                "id": key,
                "titre": cfg["titre"],
                "chercheur": cfg["chercheur"],
                "lon": lon,
                "lat": lat,
                "description": description,
                "layers": layers_out,
                "avatar": cfg.get("avatar", DEFAULT_AVATAR),
                "photos": list_photos(key),
            }
        )
        print(f"✓ {key} — centre ({lon:.5f}, {lat:.5f})")

    out_path = DATA_DIR / "projects.json"
    out_path.write_text(
        json.dumps(projects_out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✓ {out_path.relative_to(ROOT).as_posix()} ({len(projects_out)} projets)")


if __name__ == "__main__":
    main()
