import streamlit as st
import pandas as pd
from datetime import date

from kamloops_fishing_advisor_fly_depth import season_from_date, recommend_flies_with_depth

SHEET = "Lakes_2025_near_Kamloops"
XLSX_PATH = "kamloops_stocking_solunar_test_with_coords.xlsx"

st.set_page_config(page_title="Kamloops Fishing Advisor", layout="centered")

st.title("Kamloops Fishing Advisor")
st.write("Choose a lake, or let the app suggest the best stocked lakes for your date.")

@st.cache_data
def load_lakes(path: str):
    df = pd.read_excel(path, sheet_name=SHEET, engine="openpyxl")

    name_col = df.columns[0]
    species_col = "Species" if "Species" in df.columns else None
    score_col = "EffectiveQty" if "EffectiveQty" in df.columns else None

    lakes = []
    for _, r in df.iterrows():
        nm = r.get(name_col)
        if pd.isna(nm):
            continue
        name = str(nm).strip()
        if not name:
            continue

        species = str(r.get(species_col, "Rainbow Trout")).strip() if species_col else "Rainbow Trout"

        try:
            score = float(r.get(score_col, 0)) if score_col else 0.0
        except Exception:
            score = 0.0

        lakes.append({"name": name, "species": species, "score": score})

    # For dropdown (alphabetical)
    lakes_alpha = sorted(lakes, key=lambda x: x["name"].lower())

    # For suggestions (highest stocking score first)
    lakes_ranked = sorted(lakes, key=lambda x: x["score"], reverse=True)

    return lakes_alpha, lakes_ranked

try:
    lakes_alpha, lakes_ranked = load_lakes(XLSX_PATH)
except Exception as e:
    st.error(f"Could not open workbook '{XLSX_PATH}': {e}")
    st.stop()

# ---- Mode selector ----
mode = st.radio(
    "Mode",
    ["I know my lake", "Suggest lakes for me"],
    horizontal=True
)

selected_date = st.date_input("Date", value=date.today())
date_str = selected_date.strftime("%Y-%m-%d")
season = season_from_date(date_str)

# Keep a selected lake in session state so “Use this lake” works cleanly
if "selected_lake" not in st.session_state:
    st.session_state.selected_lake = lakes_alpha[0]["name"] if lakes_alpha else ""

# ---- Suggest mode ----
if mode == "Suggest lakes for me":
    st.subheader("Top suggested lakes (based on stocking score)")
    st.caption("This ranking uses the stocking score from the spreadsheet. It does not use weather or moon phases.")

    top_n = 3
    top = lakes_ranked[:top_n]

    if not top:
        st.warning("No lakes found in the spreadsheet.")
    else:
        for i, l in enumerate(top, 1):
            with st.container(border=True):
                st.markdown(f"### {i}. {l['name']}")
                st.write(f"**Season:** {season}")
                st.write(f"**Stocked/target species:** {l['species']}")
                st.write(f"**Stocking score:** {l['score']:.0f}")

                if st.button(f"Use {l['name']}", key=f"use_{i}", use_container_width=True):
                    st.session_state.selected_lake = l["name"]

    st.divider()

# ---- Lake dropdown (always available) ----
lake_names = [l["name"] for l in lakes_alpha]
default_index = 0
if st.session_state.selected_lake in lake_names:
    default_index = lake_names.index(st.session_state.selected_lake)

selected_lake = st.selectbox("Lake", lake_names, index=default_index)
st.session_state.selected_lake = selected_lake

# Find species for chosen lake
species = next((l["species"] for l in lakes_alpha if l["name"] == selected_lake), "Rainbow Trout")

if st.button("Get recommendation", use_container_width=True):
    recs = recommend_flies_with_depth(species, season)

    st.subheader(selected_lake)
    st.write(f"**Date:** {date_str}  |  **Season:** {season}  |  **Stocked/target:** {species}")

    st.subheader("Top flies + starting depth")
    for i, (fly, depth) in enumerate(recs, 1):
        st.markdown(f"### {i}. {fly}")
        st.write(f"Depth: {depth}")

    st.caption("Depths are starting points. Adjust depth in small steps until you find fish.")
