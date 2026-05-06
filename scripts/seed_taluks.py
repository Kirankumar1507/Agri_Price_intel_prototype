"""Seed data/ka_taluks.geojson from GADM India level-3 shapefile.

GADM level-3 ≈ taluk/tehsil. Download the India shapefile once, filter to
Karnataka, normalize columns to {district, taluk}, write GeoJSON.

Manual step: download https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_IND_shp.zip
            unzip into data/_gadm/ (gitignored)
Then run:   python scripts/seed_taluks.py
"""
import sys
from pathlib import Path

import geopandas as gpd
from dotenv import load_dotenv

load_dotenv()

GADM_SHP = Path("data/_gadm/gadm41_IND_3.shp")
OUT = Path("data/ka_taluks.geojson")


def main() -> int:
    if not GADM_SHP.exists():
        print(f"ERROR: {GADM_SHP} missing.", file=sys.stderr)
        print("Download gadm41_IND_shp.zip from geodata.ucdavis.edu, unzip to data/_gadm/", file=sys.stderr)
        return 1

    print(f"Reading {GADM_SHP}...")
    gdf = gpd.read_file(GADM_SHP)
    ka = gdf[gdf["NAME_1"] == "Karnataka"].copy()
    print(f"  -> {len(ka)} taluks in Karnataka")

    # GADM uses NAME_2 (district) and NAME_3 (taluk/tehsil)
    ka = ka.rename(columns={"NAME_2": "district", "NAME_3": "taluk"})[["district", "taluk", "geometry"]]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ka.to_file(OUT, driver="GeoJSON")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
