"""Step 10: README.md and reddit/post.md from data/results.json. 10.5281/zenodo.24104644, https://doi.org/10.5281/zenodo.24104644 and https://blog.tristanhotham.com/2026/10/31/trig-network/ stay as placeholders."""
from common import *

R = jload(f"{DATA}/results.json")
v, g, b, s, p = R["vis"], R["geom"], R["build"], R["surv"], R["plc"]
ci = lambda d: f"{d['pc']:.1f}% (95% CI {d['lo']:.1f} to {d['hi']:.1f})"
readme = f"""# The trig pillar network: how Britain was measured

Geometry, construction, survival and intervisibility of the Ordnance Survey Retriangulation of Great Britain. Every station in the OS legacy triangulation list ({R['counts']['stations']:,} stations, {R['counts']['kinds']['pillar']:,} of them pillars), measured as a network, and a test, fixed in a written analysis plan before it was run (NOTES.md), of the network's design rule: that neighbouring stations of the same order can see each other. A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/{SLUG}/
Paper: {{https://doi.org/10.5281/zenodo.24104644}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/trig-network/}}
Code and data: {REPO}

## Headline results

- Intervisibility: {v['o1']['k']} of {v['o1']['n']} nearest-neighbour primary lines are clear over Terrain Tiles (zoom 9) with curvature and refraction: {ci(v['o1'])}. Delaunay sides up to 80 km: {v['o1_delaunay']['pc']:.1f}%. Secondary pillars {v['o2']['pc']:.1f}%, third-order pillars {v['o3']['pc']:.1f}%.
- Placebos: the same lines with both ends moved 1 km, {ci(p['shift1km'])}; random land pairs of the same lengths, {ci(p['random'])}.
- Failures: all {R['fail']['n']} failing primary lines read by eye. {R['fail']['structure_named']} involve a structure with no recorded height (lighthouses, a cathedral, an observatory, castles, water towers); {R['fail']['pillar_pillar']} are flat-country pillar lines touching stations observed from steel towers, and all clear with a 30 m tower (exploratory); {R['fail']['unexplained_n']} ({R['fail']['unexplained'][0]}, a ground mark with no recorded height) is unexplained.
- Robustness: refraction, end margin, profile step, two neighbours and leaving out each region give {R['rob']['range_lo']:.1f}% to {R['rob']['range_hi']:.1f}%. With terrain-model heights at the ends instead of surveyed heights: {R['rob']['demonly']['pc']:.1f}%, because the zoom 9 model sits a median {abs(R['dem']['bias']):.1f} m below surveyed pillar heights.
- Spacing: median nearest same-order distance {g['o1_all']['nnd_med']:.1f} km (primary), {g['o2_pillar']['nnd_med']:.1f} km (secondary pillars), {g['o3_pillar']['nnd_med']:.1f} km (third-order pillars). Clark and Evans ratio for primaries {g['o1_all']['ce_R']:.2f} against {g['o1_all']['ce_csr_lo']:.2f} to {g['o1_all']['ce_csr_hi']:.2f} for random points on the same land; {R['tri']['well_pc']:.1f}% of primary triangles have every angle of 30 degrees or more (random: {R['tri']['csr_well_pc']:.1f}%).
- Construction: {b['pillars_1936_1962']:,} of {b['pillars_n']:,} pillars ({b['pc']:.1f}%) dated 1936 to 1962; busiest year {b['pillars_peak_year']}.
- Survival: {s['kind']['pillar']['k']} of {s['kind']['pillar']['n']:,} pillars recorded destroyed ({s['kind']['pillar']['pc']:.1f}%), against {s['kind']['intersected']['pc']:.1f}% of intersected stations and {s['kind']['surface']['pc']:.1f}% of ground marks. Logit with region, order, decade and lowland, clustered by 10 km square: intersected OR {s['model']['intersected']['or']:.2f} ({s['model']['intersected']['lo']:.2f} to {s['model']['intersected']['hi']:.2f}), ground marks {s['model']['surface']['or']:.2f}, lowland {s['model']['lowland']['or']:.2f} ({s['model']['lowland']['lo']:.2f} to {s['model']['lowland']['hi']:.2f}).

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

Hotham, T. (2026) The trig pillar network: geometry, construction, survival and intervisibility of the Ordnance Survey Retriangulation of Great Britain. Zenodo. {{10.5281/zenodo.24104644}}

{AI}
"""
for bad in ("—", "–", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in readme, bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

post = f"""**Title:** [OC] Britain's trig pillars were sited so each could see its neighbours. Over a modern terrain model, with the surveyed station heights, {v['o1']['pc']:.0f}% of neighbouring primary stations still can; random lines of the same length, {p['random']['pc']:.0f}%

**Body:**

I mapped every station in the Ordnance Survey's old triangulation list ({R['counts']['stations']:,} stations, {R['counts']['kinds']['pillar']:,} concrete pillars) and checked the rule they were built to: every station must see its neighbours.

- {v['o1']['k']} of {v['o1']['n']} lines from a primary station to its nearest primary neighbour are clear over the terrain, allowing for the curve of the Earth ({v['o1']['pc']:.0f}%).
- Move both ends 1 km in a random direction: {p['shift1km']['pc']:.0f}% clear. Random pairs of points on land at the same distances: {p['random']['pc']:.0f}%.
- The {R['fail']['n']} failures: {R['fail']['structure_named']} touch lighthouses, a cathedral, an observatory, castles or water towers whose heights the list leaves out; {R['fail']['pillar_pillar']} are lines in flat East Anglia and Lincolnshire at stations where the surveyors used steel towers (often about 30 m); 1 is unexplained.
- The catch: this uses the surveyed station heights. With the terrain model's own heights at the ends, only {R['rob']['demonly']['pc']:.0f}% are clear, because the model rounds off hilltops (a median {abs(R['dem']['bias']):.0f} m too low at the pillars). Still far above the random lines.
- {b['pc']:.0f}% of pillars carry a commissioning date from 1936 to 1962. {s['kind']['pillar']['pc']:.1f}% are recorded destroyed, against {s['kind']['surface']['pc']:.0f}% of bolts and ground marks.

Interactive map with every trig point, the lines of sight and an era slider: https://maps.tristanhotham.com/{SLUG}/

**Source comment:**

Data: Ordnance Survey legacy triangulation station list (Contains OS data (c) Crown copyright and database right 2018, Open Government Licence v3.0, via the trigpoints R package); Terrain Tiles on AWS (Mapzen; SRTM, EU-DEM, GMTED2010); OpenStreetMap (ODbL). Method: line of sight sampled every 100 m with Earth curvature and refraction (k = 0.13), ends 1.5 m above the surveyed station height; placebo lines; plan written before the analysis. Tools: Python (pandas, scipy, statsmodels, matplotlib), MapLibre. Paper and code: {REPO}
"""
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in post, bad
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words; post", len(post.split()), "words")
