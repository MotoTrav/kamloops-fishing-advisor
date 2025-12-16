import streamlit as st
import pandas as pd
from datetime import date

from kamloops_fishing_advisor_fly_depth import season_from_date, recommend_flies_with_depth

SHEET = "Lakes_2025_near_Kamloops"

st.set_page_config(page_title="Kamloops Fishing Advisor", layout="centered")

st.title("Kamloops Fishing Advisor")
st.write("Select a lake and a date to get fly types and starting depths.")

@st.cache_data
def load_lakes(path: str):
    df = pd.read_excel(path, sheet_name=SHEET, engine="openpyxl")

    name_col = df.columns[0]
    species_col = "Species" if "Species" in df.columns else None

    lakes = []
    for _, r in df.iterrows():
        nm = r.get(name_col)
        if pd.isna(nm):
            continue
        name = str(nm).strip()
        if not name:
            continue
        species = str(r.get(species_col, "Rainbow Trout")) if species_col else "Rainbow Trout"
        lakes.append((name, species))

    lakes.sort(key=lambda x: x[0].lower())
    return lakes

XLSX_PATH = "kamloops_stocking_solunar_test_with_coords.xlsx"

try:
    lakes = load_lakes(XLSX_PATH)
except Exception as e:
    st.error(f"Could not open workbook '{XLSX_PATH}': {e}")
    st.stop()

lake_names = [l[0] for l in lakes]
selected_lake = st.selectbox("Lake", lake_names)

selected_date = st.date_input("Date", value=date.today())
date_str = selected_date.strftime("%Y-%m-%d")

species = next((l[1] for l in lakes if l[0] == selected_lake), "Rainbow Trout")
season = season_from_date(date_str)

if st.button("Get recommendation", use_container_width=True):
    recs = recommend_flies_with_depth(species, season)

    st.subheader(selected_lake)
    st.write(f"**Date:** {date_str}  |  **Season:** {season}  |  **Stocked/target:** {species}")

    st.subheader("Top flies + starting depth")
    for i, (fly, depth) in enumerate(recs, 1):
        st.markdown(f"### {i}. {fly}")
        st.write(f"Depth: {depth}")

    st.caption("Depths are starting points. Adjust depth in small steps until you find fish.")
