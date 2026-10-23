"""
MomentumStudio AI — Autonomous Asset Procurement & Ingestion Pipeline
Downloads CC0 3D game asset kits, PBR textures, and HDRIs from Kenney, Poly Haven, and ambientCG.
Indexes all downloaded modular models and materials into asset_catalog.json for spatial agent access.
"""

import os
import sys
import json
import shutil
import zipfile
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
KENNEY_DIR = ASSETS_DIR / "kenney"
POLYHAVEN_DIR = ASSETS_DIR / "polyhaven"
AMBIENTCG_DIR = ASSETS_DIR / "ambientcg"
CATALOG_PATH = ASSETS_DIR / "asset_catalog.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

KENNEY_KITS = {
    "city_roads": "https://kenney.nl/media/pages/assets/city-kit-roads/74288c9459-1791628607/kenney_city-kit-roads.zip",
    "city_industrial": "https://kenney.nl/media/pages/assets/city-kit-industrial/0ec35b139d-1788171848/kenney_city-kit-industrial_2.0.zip",
    "car_kit": "https://kenney.nl/media/pages/assets/car-kit/1a312ec241-1775131960/kenney_car-kit.zip",
    "modular_space": "https://kenney.nl/media/pages/assets/modular-space-kit/8261428a47-1771146076/kenney_modular-space-kit_1.0.zip",
}

POLYHAVEN_TEXTURES = {
    "aerial_asphalt_01": [
        "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/aerial_asphalt_01/aerial_asphalt_01_diff_1k.jpg",
        "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/aerial_asphalt_01/aerial_asphalt_01_rough_1k.jpg",
        "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/aerial_asphalt_01/aerial_asphalt_01_nor_gl_1k.jpg",
    ],
    "asphalt_02": [
        "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/asphalt_02/asphalt_02_diff_1k.jpg",
        "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/asphalt_02/asphalt_02_rough_1k.jpg",
        "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/asphalt_02/asphalt_02_nor_gl_1k.jpg",
    ],
}

AMBIENTCG_MATERIALS = {
    "Asphalt012": "https://ambientcg.com/get?file=Asphalt012_1K-JPG.zip",
    "Metal032": "https://ambientcg.com/get?file=Metal032_1K-JPG.zip",
}


def download_file(url: str, dest_path: Path) -> bool:
    print(f"  📥 Downloading: {url} -> {dest_path.name}")
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        return True
    except Exception as e:
        print(f"  ⚠️ Error downloading {url}: {e}")
        return False


def ingest_kenney_kits():
    print("\n--- [1/3] Ingesting Kenney CC0 3D Kits ---")
    KENNEY_DIR.mkdir(parents=True, exist_ok=True)
    
    for name, url in KENNEY_KITS.items():
        zip_path = KENNEY_DIR / f"{name}.zip"
        extract_folder = KENNEY_DIR / name
        
        if not extract_folder.exists() or len(list(extract_folder.glob("*"))) == 0:
            if not zip_path.exists() or zip_path.stat().st_size == 0:
                success = download_file(url, zip_path)
                if not success:
                    continue
            
            print(f"  📦 Extracting {zip_path.name}...")
            extract_folder.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(extract_folder)
                print(f"  ✅ Extracted {name} ({len(list(extract_folder.rglob('*')))} files)")
            except Exception as e:
                print(f"  ⚠️ Failed to extract {name}: {e}")


def ingest_polyhaven_textures():
    print("\n--- [2/3] Ingesting Poly Haven CC0 PBR Textures ---")
    POLYHAVEN_DIR.mkdir(parents=True, exist_ok=True)
    
    for tex_name, urls in POLYHAVEN_TEXTURES.items():
        tex_folder = POLYHAVEN_DIR / tex_name
        tex_folder.mkdir(parents=True, exist_ok=True)
        
        for u in urls:
            filename = u.split("/")[-1]
            dest = tex_folder / filename
            if not dest.exists() or dest.stat().st_size == 0:
                download_file(u, dest)
        print(f"  ✅ Poly Haven texture pack ready: {tex_name}")


def ingest_ambientcg_materials():
    print("\n--- [3/3] Ingesting ambientCG CC0 PBR Materials ---")
    AMBIENTCG_DIR.mkdir(parents=True, exist_ok=True)
    
    for mat_id, url in AMBIENTCG_MATERIALS.items():
        zip_path = AMBIENTCG_DIR / f"{mat_id}.zip"
        mat_folder = AMBIENTCG_DIR / mat_id
        
        if not mat_folder.exists() or len(list(mat_folder.glob("*"))) == 0:
            if not zip_path.exists() or zip_path.stat().st_size == 0:
                success = download_file(url, zip_path)
                if not success:
                    continue
            
            print(f"  📦 Extracting {mat_id}...")
            mat_folder.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(mat_folder)
                print(f"  ✅ Extracted ambientCG material: {mat_id}")
            except Exception as e:
                print(f"  ⚠️ Failed to extract {mat_id}: {e}")


def build_unified_asset_catalog():
    print("\n--- Generating Unified Asset Catalog ---")
    catalog = {
        "version": "1.0.0",
        "total_3d_models": 0,
        "total_pbr_materials": 0,
        "categories": {
            "roads": [],
            "industrial_megatowers": [],
            "vehicles": [],
            "space_structures": [],
            "pbr_textures": [],
        }
    }

    # Index Kenney models (glb/gltf/fbx/obj)
    for model_path in KENNEY_DIR.rglob("*.*"):
        ext = model_path.suffix.lower()
        if ext in [".glb", ".gltf", ".fbx", ".obj"]:
            rel_path = str(model_path.relative_to(BASE_DIR))
            item = {
                "name": model_path.stem,
                "format": ext.replace(".", "").upper(),
                "relative_path": rel_path,
                "size_bytes": model_path.stat().st_size,
            }
            if "road" in rel_path.lower():
                catalog["categories"]["roads"].append(item)
            elif "industrial" in rel_path.lower():
                catalog["categories"]["industrial_megatowers"].append(item)
            elif "car" in rel_path.lower():
                catalog["categories"]["vehicles"].append(item)
            elif "space" in rel_path.lower():
                catalog["categories"]["space_structures"].append(item)
            catalog["total_3d_models"] += 1

    # Index PBR textures
    for tex_path in POLYHAVEN_DIR.rglob("*.jpg"):
        catalog["categories"]["pbr_textures"].append({
            "name": tex_path.stem,
            "source": "PolyHaven",
            "relative_path": str(tex_path.relative_to(BASE_DIR)),
        })
        catalog["total_pbr_materials"] += 1

    for mat_path in AMBIENTCG_DIR.rglob("*.jpg"):
        catalog["categories"]["pbr_textures"].append({
            "name": mat_path.stem,
            "source": "ambientCG",
            "relative_path": str(mat_path.relative_to(BASE_DIR)),
        })
        catalog["total_pbr_materials"] += 1

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"🎉 Asset Catalog Complete: {catalog['total_3d_models']} 3D models and {catalog['total_pbr_materials']} PBR textures indexed at {CATALOG_PATH.name}")
    return catalog


if __name__ == "__main__":
    ingest_kenney_kits()
    ingest_polyhaven_textures()
    ingest_ambientcg_materials()
    build_unified_asset_catalog()
