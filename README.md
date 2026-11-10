# The trig pillar network: how Britain was measured

Geometry, construction, survival and intervisibility of the Ordnance Survey Retriangulation of Great Britain. Every station in the OS legacy triangulation list (24,433 stations, 6,573 of them pillars), measured as a network, and a test, fixed in a written analysis plan before it was run (NOTES.md), of the network's design rule: that neighbouring stations of the same order can see each other. A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/trig-network/
Paper: https://doi.org/10.5281/zenodo.24104644
Blog post: https://blog.tristanhotham.com/2026/10/31/trig-network/
Code and data: https://github.com/Tristan-Hotham/trig-network

## Headline results

- Intervisibility: 228 of 240 nearest-neighbour primary lines are clear over Terrain Tiles (zoom 9) with curvature and refraction: 95.0% (95% CI 91.5 to 97.1). Delaunay sides up to 80 km: 95.6%. Secondary pillars 97.1%, third-order pillars 91.9%.
- Placebos: the same lines with both ends moved 1 km, 16.6% (95% CI 15.2 to 18.2); random land pairs of the same lengths, 10.9% (95% CI 9.7 to 12.2).
- Failures: all 12 failing primary lines read by eye. 8 involve a structure with no recorded height (lighthouses, a cathedral, an observatory, castles, water towers); 3 are flat-country pillar lines touching stations observed from steel towers, and all clear with a 30 m tower (exploratory); 1 (West Hills to Buddon, a ground mark with no recorded height) is unexplained.
- Robustness: refraction, end margin, profile step, two neighbours and leaving out each region give 93.2% to 96.6%. With terrain-model heights at the ends instead of surveyed heights: 67.1%, because the zoom 9 model sits a median 21.7 m below surveyed pillar heights.
- Spacing: median nearest same-order distance 19.6 km (primary), 7.1 km (secondary pillars), 4.3 km (third-order pillars). Clark and Evans ratio for primaries 1.54 against 1.02 to 1.17 for random points on the same land; 71.3% of primary triangles have every angle of 30 degrees or more (random: 48.0%).
- Construction: 6,510 of 6,573 pillars (99.0%) dated 1936 to 1962; busiest year 1948.
- Survival: 415 of 6,573 pillars recorded destroyed (6.3%), against 26.1% of intersected stations and 36.2% of ground marks. Logit with region, order, decade and lowland, clustered by 10 km square: intersected OR 3.25 (2.81 to 3.77), ground marks 5.52, lowland 1.47 (1.33 to 1.62).

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; every station by order, lines to nearest same-order neighbours coloured by line of sight, surviving/destroyed filter, era slider, search, layers, full screen. |
| `header.png` | Social card, 1200 x 630. |
| `data/stations.csv` | One row per station: code, name, order, kind, mark types, height, commissioning year, destroyed flag, notes, National Grid and WGS84 position, terrain height, region, 10 km square. |
| `data/nn_pairs.csv` | Each station's nearest same-order neighbour (primaries all kinds; other orders pillars). |
| `data/pairs.csv` | Every tested line (nearest neighbours of orders 1 to 3, primary Delaunay sides): length, clearance, worst point, clear or not. |
| `data/primary_triangles.csv` | The primary Delaunay triangles kept, with their angles. |
| `data/commissioning_by_year.csv`, `data/destroyed_by_region.csv`, `data/survival_model.csv` | Construction by year and kind; destroyed shares by region; the planned logit. |
| `data/osm_points.csv` | OpenStreetMap survey points with their nearest OS station (ODbL). |
| `data/results.json`, `data/site.json` | Every number quoted anywhere; page data. |
| `code/` | Scripts in order, templates, `steel_towers.csv`, `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | Working notes and the analysis plan, written before the outcomes were computed. |

## Method in brief

- Stations: mark rows grouped by station code within 100 m; a station is a pillar if any row is one; order is the lowest of its rows; destroyed if every row is flagged.
- Lines of sight: terrain sampled every 100 m (bilinear), lowered by d1 d2 (1 - k) / 2R with k = 0.13; ends at the surveyed height (or terrain height if none) plus 1.5 m; samples within 250 m of either end ignored.
- Placebos: ends moved 1 km at random onto land; random land pairs of the same lengths; ten draws per line.
- Spacing: nearest same-order distances with bootstrap CIs; Clark and Evans ratio against 199 CSR simulations on the GB land mask; Delaunay triangles of primaries.
- Survival: Wilson intervals; logit with standard errors clustered by 10 km square (statsmodels); OSM cross-check.

## How to rerun

Needs Python 3 with pandas, numpy, scipy, geopandas, shapely, pyproj, statsmodels, matplotlib, Pillow; xelatex; node with Playwright for QA. Raw inputs are listed in `code/common.py` (the terrain tiles are read in place, never copied).

```
python3 code/01_data.py        # mark rows -> stations; OSM points
python3 code/02_geometry.py    # spacing, regularity, triangles, construction
python3 code/03_visibility.py  # lines of sight, placebos, robustness (a few minutes)
python3 code/04_survival.py    # destroyed shares, logit, OSM check
python3 code/05_results.py     # results.json and the exploratory checks
python3 code/06_figures.py     # figures and header.png
python3 code/07_site.py        # site.json and index.html
python3 code/08_paper.py       # the paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 code/09_release.py     # blog post, meta, Zenodo files
python3 code/10_readme.py      # README and Reddit post
python3 reddit/collage.py      # Reddit collage
node code/qa.js                # screenshots
```

## Sources and licences

- Ordnance Survey legacy triangulation station list. Contains OS data (c) Crown copyright and database right 2018, used under the Open Government Licence v3.0. Packaged by Phil Mike Jones in the trigpoints R package (package code MIT licence).
- Terrain Tiles on AWS Open Data (Mapzen): SRTM and GMTED2010 courtesy of the U.S. Geological Survey; EU-DEM produced using Copernicus data and information funded by the European Union; ETOPO1 (NOAA).
- OpenStreetMap survey points (c) OpenStreetMap contributors, ODbL, retrieved 2026 through QLever.
- Region boundaries: Office for National Statistics (Open Government Licence v3.0).
- Steel tower stations: TrigpointingUK wiki, "Bilby towers" (citing the OS History of the Retriangulation, 1967).
- Base map: OpenFreeMap Positron (OpenStreetMap, ODbL); MapLibre GL JS 4.7.1 (BSD 3-Clause).
- This repository: code MIT; text and figures CC BY 4.0; derived data CC BY 4.0, except that OS station fields remain under the Open Government Licence v3.0 and data/osm_points.csv is ODbL. See LICENSE.

## Citation

Hotham, T. (2026) The trig pillar network: geometry, construction, survival and intervisibility of the Ordnance Survey Retriangulation of Great Britain. Zenodo. 10.5281/zenodo.24104644

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
