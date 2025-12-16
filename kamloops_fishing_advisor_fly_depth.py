#!/usr/bin/env python3
"""
Kamloops Fishing Advisor – Fly + Depth Recommendation Focus

This version:
- Ranks top lakes by stocking score
- Recommends TOP FLY TYPES + DEPTH guidance based on:
  species + season (stillwater trout defaults)
- DOES NOT use weather or Open-Meteo

Usage:
python3 kamloops_fishing_advisor_fly_depth.py --xlsx kamloops_stocking_solunar_test_with_coords.xlsx --date 2025-06-15
python3 kamloops_fishing_advisor_fly_depth.py --xlsx kamloops_stocking_solunar_test_with_coords.xlsx --lake "Tunkwa" --date 2025-06-15
"""

import argparse
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
import pandas as pd
import difflib

DEFAULT_SHEET = "Lakes_2025_near_Kamloops"


def season_from_date(date_str: str) -> str:
    m = datetime.strptime(date_str, "%Y-%m-%d").month
    if m in (12, 1, 2):
        return "winter"
    if m in (3, 4):
        return "spring"
    if m in (5, 6):
        return "late_spring"
    if m in (7, 8):
        return "summer"
    return "fall"


def normalize(name: str) -> str:
    return "".join(c for c in str(name).lower() if c.isalnum())


def match_lake(name: str, lakes: List["Lake"]) -> Optional["Lake"]:
    lookup = {normalize(l.name): l for l in lakes}
    key = normalize(name)
    if key in lookup:
        return lookup[key]
    close = difflib.get_close_matches(key, lookup.keys(), n=3, cutoff=0.55)
    return lookup[close[0]] if close else None


def recommend_flies_with_depth(species: str, season: str) -> List[Tuple[str, str]]:
    """Return list of (fly_type, depth_guidance). Depths are typical stillwater starting points."""
    s = (species or "").lower()

    # Kokanee behave differently; depth is often very lake-specific. Provide safe starting guidance.
    if "kokanee" in s:
        return [
            ("Tiny chironomid (size 14–18)", "10–25 ft (start at 15–20 ft; adjust until you mark/find fish)"),
            ("Small pink/white micro-leech", "8–18 ft along drop-offs; slow troll/strip"),
            ("Small flashy trolling fly", "15–35 ft (trolling depth depends on season and lake temp)"),
        ]

    # Trout defaults
    if season in ("spring", "late_spring"):
        return [
            ("Chironomid (black/red) size 12–16", "8–20 ft (start 12–15 ft; tune depth in 1–2 ft steps)"),
            ("Callibaetis nymph", "4–12 ft over shoals/weed edges; intermediate line or long leader"),
            ("Leech (olive/black)", "3–10 ft early/late; 6–15 ft if bright mid-day"),
        ]

    if season == "summer":
        return [
            ("Damsel nymph", "2–8 ft along weed edges and cruising lanes"),
            ("Leech (early/late)", "3–10 ft at dawn/dusk; suspend deeper (10–18 ft) mid-day"),
            ("Small chironomid (deeper)", "12–30 ft (start 18–22 ft during bright mid-day)"),
        ]

    # fall / winter open water
    if season == "winter":
        return [
            ("Chironomid (small 14–18)", "10–25 ft (mid-day best; very slow)"),
            ("Leech (black)", "8–18 ft (slow strips/pause)"),
            ("Scud / shrimp", "6–14 ft near weeds/soft bottom"),
        ]

    return [
        ("Leech (black)", "6–18 ft (windward shore or drop-offs; slow/steady)"),
        ("Chironomid", "10–25 ft (start 14–18 ft; adjust)"),
        ("Scud / shrimp", "4–12 ft near weeds/soft bottom"),
    ]


@dataclass
class Lake:
    name: str
    score: float
    species: str


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--lake")
    args = ap.parse_args()

    df = pd.read_excel(args.xlsx, sheet_name=DEFAULT_SHEET, engine="openpyxl")

    lakes: List[Lake] = []
    # Try to find likely columns
    cols = list(df.columns)
    name_col = cols[0]
    score_col = "EffectiveQty" if "EffectiveQty" in df.columns else None
    species_col = "Species" if "Species" in df.columns else None

    for _, r in df.iterrows():
        nm = r.get(name_col)
        if pd.isna(nm):
            continue
        name = str(nm).strip()
        if not name:
            continue
        score = float(r.get(score_col, 0)) if score_col else 0.0
        sp = str(r.get(species_col, "Rainbow Trout")) if species_col else "Rainbow Trout"
        lakes.append(Lake(name=name, score=score, species=sp))

    season = season_from_date(args.date)

    if args.lake:
        lake = match_lake(args.lake, lakes)
        if not lake:
            print("Lake not found. Tip: check spelling or run without --lake to see top lakes.")
            return
        print(f"LAKE: {lake.name}")
        print(f"DATE: {args.date}")
        print(f"SEASON: {season}")
        recs = recommend_flies_with_depth(lake.species, season)
        print("\nTOP FLIES + DEPTH:")
        for i, (fly, depth) in enumerate(recs, 1):
            print(f" {i}) {fly}\n     Depth: {depth}")
        return

    top = sorted(lakes, key=lambda x: x.score, reverse=True)[:3]
    print(f"TOP {len(top)} LAKES – {args.date}")
    for i, l in enumerate(top, 1):
        print(f"{i}) {l.name} (stocking score {l.score:.0f})")
        recs = recommend_flies_with_depth(l.species, season)
        print("   Recommended flies + starting depth:")
        for fly, depth in recs:
            print(f"    - {fly} | {depth}")
        print()

    print('Tip: run again with --lake "<lake name>" for the same fly+depth advice focused on one lake.')


if __name__ == "__main__":
    main()
