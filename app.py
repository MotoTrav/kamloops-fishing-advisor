import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from kamloops_fishing_advisor_fly_depth import season_from_date, recommend_flies_with_depth

# Solunar (Skyfield)
from zoneinfo import ZoneInfo
from skyfield.api import load, wgs84
from skyfield import almanac

SHEET = "Lakes_2025_near_Kamloops"
XLSX_PATH = "kamloops_stocking_solunar_test_with_coords.xlsx"
TZ_NAME = "America/Vancouver"

st.set_page_config(page_title="Kamloops Fishing Advisor", layout="centered")

st.title("Kamloops Fishing Advisor")
st.write("Choose a lake, or let the app suggest the best stocked lakes for your date.")


@st.cache_data
def load_lakes(path: str):
    df = pd.read_excel(path, sheet_name=SHEET, engine="openpyxl")

    name_col = df.columns[0]
    species_col = "Species" if "Species" in df.columns else None
    score_col = "EffectiveQty" if "EffectiveQty" in df.columns else None

    lat_col = "Lat" if "Lat" in df.columns else ("Latitude" if "Latitude" in df.columns else None)
    lon_col = "Lon" if "Lon" in df.columns else ("Longitude" if "Longitude" in df.columns else None)

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

        lat = None
        lon = None
        try:
            if lat_col and not pd.isna(r.get(lat_col)):
                lat = float(r.get(lat_col))
            if lon_col and not pd.isna(r.get(lon_col)):
                lon = float(r.get(lon_col))
        except Exception:
            lat, lon = None, None

        lakes.append({"name": name, "species": species, "score": score, "lat": lat, "lon": lon})

    lakes_alpha = sorted(lakes, key=lambda x: x["name"].lower())
    lakes_ranked = sorted(lakes, key=lambda x: x["score"], reverse=True)
    return lakes_alpha, lakes_ranked


@st.cache_resource
def _skyfield_context():
    # de421.bsp will download on first run (cached after)
    ts = load.timescale()
    eph = load("de421.bsp")
    return ts, eph


def _fmt_time(dt: datetime) -> str:
    # Cross-platform friendly 12-hour formatting without %-I
    s = dt.strftime("%I:%M %p")
    return s.lstrip("0")


def solunar_windows(lat: float, lon: float, date_str: str, tz_name: str = TZ_NAME):
    ts, eph = _skyfield_context()
    tz = ZoneInfo(tz_name)

    y, m, d = map(int, date_str.split("-"))
    t0 = ts.utc(y, m, d, 0, 0, 0)
    t1 = ts.utc(y, m, d, 23, 59, 59)

    loc = wgs84.latlon(lat, lon)
    moon = eph["moon"]

    # Major: moon overhead/underfoot (meridian transits)
    f_major = almanac.meridian_transits(eph, moon, loc)
    t_major, y_major = almanac.find_discrete(t0, t1, f_major)

    # Minor: moonrise/moonset
    f_minor = almanac.risings_and_settings(eph, moon, loc)
    t_minor, y_minor = almanac.find_discrete(t0, t1, f_minor)

    def to_local(sf_time):
        return sf_time.utc_datetime().replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)

    majors = []
    for t, ev in zip(t_major, y_major):
        center = to_local(t)
        label = "Overhead" if int(ev) == 1 else "Underfoot"
        majors.append((label, center))

    minors = []
    for t, ev in zip(t_minor, y_minor):
        center = to_local(t)
        label = "Moonrise" if int(ev) == 1 else "Moonset"
        minors.append((label, center))

    # Window widths
    major_half = timedelta(minutes=60)   # +/- 60 minutes
    minor_half = timedelta(minutes=30)   # +/- 30 minutes

    def window(center: datetime, half: timedelta) -> str:
        start = center - half
        end = center + half
        return f"{_fmt_time(start)}–{_fmt_time(end)}"

    major_windows = [(lab, window(c, major_half)) for lab, c in majors]
    minor_windows = [(lab, window(c, minor_half)) for lab, c in minors]

    return major_windows, minor_windows


try:
    lakes_alpha, lakes_ranked = load_lakes(XLSX_PATH)
except Exception as e:
    st.error(f"Could not open workbook '{XLSX_PATH}': {e}")
    st.stop()

# ---- Mode selector ----
mode = st.radio("Mode", ["I know my lake", "Suggest lakes for me"], horizontal=True)

selected_date = st.date_input("Date", value=date.today())
date_str = selected_date.strftime("%Y-%m-%d")
season = season_from_date(date_str)

# Session state for selected lake
if "selected_lake" not in st.session_state:
    st.session_state.selected_lake = lakes_alpha[0]["name"] if lakes_alpha else ""

# ---- Suggest mode ----
if mode == "Suggest lakes for me":
    st.subheader("Top suggested lakes (based on stocking score)")
    st.caption("This ranking uses the stocking score from the spreadsheet. Solunar is shown per-lake, but not used to rank lakes.")

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

# Find lake row for selected lake
lake_row = next((l for l in lakes_alpha if l["name"] == selected_lake), None)
species = lake_row["species"] if lake_row else "Rainbow Trout"
lat = lake_row.get("lat") if lake_row else None
lon = lake_row.get("lon") if lake_row else None

# ---- Solunar display (windows only) ----
with st.expander("Solunar bite windows (optional)", expanded=False):
    if lat is None or lon is None:
        st.write("Solunar windows unavailable (Lat/Lon missing for this lake in the spreadsheet).")
    else:
        try:
            majors, minors = solunar_windows(lat, lon, date_str, TZ_NAME)

            st.markdown("**Major periods (strongest):**")
            if majors:
                for lab, win in majors:
                    st.write(f"- {lab}: {win}")
            else:
                st.write("- None found for this date")

            st.markdown("**Minor periods (secondary):**")
            if minors:
                for lab, win in minors:
                    st.write(f"- {lab}: {win}")
            else:
                st.write("- None found for this date")

            st.caption("Major = moon overhead/underfoot. Minor = moonrise/moonset. Use as timing guidance, not fly selection.")
        except Exception as e:
            st.write(f"Solunar calculation failed: {e}")

# ---- Recommendation output ----
if st.button("Get recommendation", use_container_width=True):
    recs = recommend_flies_with_depth(species, season)

    st.subheader(selected_lake)
    st.write(f"**Date:** {date_str}  |  **Season:** {season}  |  **Stocked/target:** {species}")

    st.subheader("Top flies + starting depth")
    for i, (fly, depth) in enumerate(recs, 1):
        st.markdown(f"### {i}. {fly}")
        st.write(f"Depth: {depth}")

    st.caption("Depths are starting points. Adjust depth in small steps until you find fish.")
