# Kamloops Fishing Advisor 🎣

A practical, data-driven stillwater fishing advisor for lakes around Kamloops, British Columbia.

This app helps anglers make **better decisions on the water** by answering two simple questions:

1. *Which lakes are most worth fishing right now?*  
2. *What fly type and depth should I start with once I get there?*

The recommendations are based on **official BC stocking data**, **seasonal trout behaviour**, and optional **solunar bite windows**—not guesswork, social-media trends, or opaque “fish activity” scores.

---

## What the app does

### Lake suggestions
- Ranks nearby lakes by **stocking strength**
- Shows the **top suggested lakes** for a chosen date
- Keeps the logic transparent and easy to understand

### Fly & depth recommendations
- Recommends **fly categories** (chironomids, leeches, damsels, etc.)
- Provides **realistic starting depths** for stillwater fishing
- Adjusts recommendations by **season** and **stocked species**

### Solunar bite windows (optional)
- Displays **major and minor solunar periods** for each lake
- Uses accurate astronomical calculations (moon overhead, underfoot, rise, set)
- Intended as **timing guidance only**, not a replacement for good presentation

---

## What this app is (and is not)

**This app is:**
- A decision-support tool
- Designed for Interior BC stillwaters
- Friendly for beginners and experienced anglers alike
- Usable on mobile, tablet, and desktop

**This app is not:**
- A catch guarantee
- A weather-based “fish activity” predictor
- A replacement for learning depth control and presentation

Good fishing still requires adapting on the water.

---

## How to use

1. Open the app
2. Choose a date
3. Either:
   - Select **“Suggest lakes for me”** to see top options, or
   - Choose a lake you already plan to fish
4. Review:
   - Recommended fly types
   - Starting depth ranges
   - Optional solunar bite windows
5. Adjust depth and presentation until you find fish

---

## Data sources & methodology

- **BC Freshwater Fisheries stocking records**
- Established stillwater fly-fishing practices for Interior BC
- Astronomical solunar calculations using Skyfield

The logic is intentionally conservative and explainable.

---

## Technology

- Python
- Streamlit
- Pandas
- Skyfield (solunar calculations)

---

## Disclaimer

This tool provides general guidance only.  
Always follow local fishing regulations and lake-specific rules.  
Depths and fly choices are starting points, not prescriptions.

---

## Live App

If deployed on Streamlit Community Cloud, the live version can be accessed via the Streamlit app URL.

---

Built to be **useful on the water**, not impressive on a marketing page.
