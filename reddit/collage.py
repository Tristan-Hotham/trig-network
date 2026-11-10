"""Reddit collage (r/dataisbeautiful style), light background, 2700 x 2025 px: the primary triangulation with its lines of
sight, the share of lines clear against placebos, the build by year and what survives. Run after code/05_results.py:
python3 reddit/collage.py"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection
import numpy as np, pandas as pd
import geopandas as gpd, shapely
from scipy.spatial import Delaunay
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
plt.rcParams.update({"font.family": "Source Serif 4", "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#6E604E", "xtick.color": "#6E604E", "ytick.color": "#6E604E"})
PAPER, INK, MUT, RED, BLUE, GREY, GOLD, LAND = "#FAF6EC", "#2B2119", "#6E604E", "#B4442E", "#2F6A9E", "#9C9384", "#C98A2B", "#EADFC2"
HALO = [pe.withStroke(linewidth=4, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
S = pd.read_csv(f"{DATA}/stations.csv"); Si = S.set_index("sid")
P = pd.read_csv(f"{DATA}/pairs.csv")
rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True)
GB = shapely.make_valid(rg[rg.areanm != "Northern Ireland"].to_crs(27700).geometry.make_valid().buffer(0).union_all()).simplify(300)


def segs(df):
    a = Si.loc[df.sid_a]; b = Si.loc[df.sid_b]
    return np.stack([np.c_[a.easting.values, a.northing.values], np.c_[b.easting.values, b.northing.values]], axis=1) / 1000


fig = plt.figure(figsize=(13.5, 10.125), dpi=200)
fig.patch.set_facecolor(PAPER)
fig.text(0.035, 0.958, "Can Britain's trig pillars still see each other?", family=DISP, fontsize=30, fontweight="bold", color=INK, va="top")
fig.text(0.035, 0.9, f"Ordnance Survey triangulation stations, built from 1936 so that each could see its neighbours. Lines from each of the\n"
         f"{R['counts']['orders']['1']} primary stations to its nearest primary neighbour, tested over a modern terrain model with the curve of the Earth",
         fontsize=13, color=MUT, va="top")
# map
ax = fig.add_axes([0.0, 0.07, 0.5, 0.78]); ax.set_facecolor(PAPER)
for g in (GB.geoms if hasattr(GB, "geoms") else [GB]):
    x, y = g.exterior.xy
    ax.fill(np.array(x) / 1000, np.array(y) / 1000, fc=LAND, ec="#BFAE86", lw=0.4, zorder=1)
P1 = S[S["order"] == 1]
pil = S[(S.kind == "pillar") & (S["order"].isin([2, 3]))]
ax.scatter(pil.easting / 1000, pil.northing / 1000, s=0.6, c="#B9A57E", lw=0, zorder=2, rasterized=True)
nn = P[(P.order == 1) & (P.set == "nn1")]
ax.add_collection(LineCollection(segs(nn[nn.visible == 1]), colors=BLUE, lw=1.4, zorder=3))
ax.add_collection(LineCollection(segs(nn[nn.visible == 0]), colors=RED, lw=2.6, zorder=4))
ax.scatter(P1.easting / 1000, P1.northing / 1000, s=7, c=INK, zorder=5, lw=0)
ax.set_xlim(-90, 680); ax.set_ylim(-5, 1230); ax.set_aspect("equal"); ax.axis("off")
# legend on the sea, top left
lx, ly = -85, 400
ax.plot([lx, lx + 32], [ly, ly], color=BLUE, lw=2.2); ax.text(lx + 42, ly, "clear line of sight", va="center", fontsize=11.5, color=INK)
ax.plot([lx, lx + 32], [ly - 32, ly - 32], color=RED, lw=2.8); ax.text(lx + 42, ly - 32, "blocked in the model", va="center", fontsize=11.5, color=INK)
ax.scatter([lx + 16], [ly - 64], s=14, c=INK); ax.text(lx + 42, ly - 64, "primary station", va="center", fontsize=11.5, color=INK)
ax.scatter([lx + 16], [ly - 96], s=8, c="#B9A57E"); ax.text(lx + 42, ly - 96, "other pillars", va="center", fontsize=11.5, color=INK)
# callouts on the sea (east), no leader lines
ax.text(470, 860, "Red lines in flat Norfolk,\nSuffolk and Lincolnshire:\nblocked by a few metres.\nSurveyors used steel\ntowers (often 30 m) there", fontsize=11, color=RED, va="top", path_effects=HALO)
ax.text(-80, 235, "Lundy lighthouses:\nno height recorded", fontsize=11, color=RED, va="top", path_effects=HALO)
# right column: headline numbers
fig.text(0.52, 0.80, f"{R['vis']['o1']['pc']:.0f}%", family=DISP, fontsize=52, fontweight="bold", color=BLUE, va="top")
fig.text(0.665, 0.795, f"of {R['vis']['o1']['n']} lines from a primary station to its nearest\nprimary neighbour are clear, using surveyed heights\n(95% CI {R['vis']['o1']['lo']:.0f} to {R['vis']['o1']['hi']:.0f}%; with terrain-model heights, {R['rob']['demonly']['pc']:.0f}%)",
         fontsize=13, color=INK, va="top")
# bars: clear share
ax2 = fig.add_axes([0.6, 0.47, 0.36, 0.22]); ax2.set_facecolor(PAPER)
rows = [("Primary stations", R["vis"]["o1"], RED), ("Secondary pillars", R["vis"]["o2"], GOLD), ("Third-order pillars", R["vis"]["o3"], BLUE),
        ("Same lines, ends\nmoved 1 km", R["plc"]["shift1km"], GREY), ("Random land pairs,\nsame lengths", R["plc"]["random"], GREY)]
for j, (lab, v, c) in enumerate(rows[::-1]):
    ax2.barh(j, v["pc"], color=c, height=0.62)
    ax2.text(v["pc"] + 1.5, j, f"{v['pc']:.0f}%", va="center", fontsize=12, color=INK)
ax2.set_yticks(range(len(rows))); ax2.set_yticklabels([r[0] for r in rows[::-1]], fontsize=11.5, color=INK)
ax2.set_xlim(0, 112); ax2.set_xticks([]); ax2.spines["bottom"].set_visible(False)
ax2.set_title("Share of lines with a clear line of sight", loc="left", fontsize=13, color=INK)
# build histogram
ax3 = fig.add_axes([0.6, 0.255, 0.36, 0.15]); ax3.set_facecolor(PAPER)
pp = S[S.kind == "pillar"]
yrs = np.arange(1936, 1971)
ax3.bar(yrs, pp.com_year.value_counts().reindex(yrs, fill_value=0).values, color=INK, width=0.8)
ax3.set_xticks([1936, 1940, 1945, 1950, 1955, 1960, 1965, 1970]); ax3.tick_params(labelsize=10)
ax3.set_title(f"Pillars by commissioning year: {R['build']['pc']:.0f}% from 1936 to 1962", loc="left", fontsize=13, color=INK)
ax3.set_yticks([])
ax3.text(1964, ax3.get_ylim()[1] * 0.55, "none dated\n1940 or 1941", fontsize=10, color=MUT)
# survival line
fig.text(0.6, 0.165, "Recorded destroyed", fontsize=13, color=INK)
fig.text(0.6, 0.128, f"pillars {R['surv']['kind']['pillar']['pc']:.0f}%   ·   spires, towers {R['surv']['kind']['intersected']['pc']:.0f}%   ·   ground marks {R['surv']['kind']['surface']['pc']:.0f}%",
         fontsize=11.5, color=INK)
fig.text(0.035, 0.022, "Data: Ordnance Survey legacy triangulation stations (Contains OS data © Crown copyright and database right 2018, OGL v3.0, via the trigpoints R package);\n"
         "Terrain Tiles on AWS (Mapzen; SRTM, EU-DEM, GMTED2010). Ends 1.5 m above surveyed heights, refraction k = 0.13.   maps.tristanhotham.com/trig-network",
         fontsize=9.5, family="IBM Plex Mono", color=MUT, va="bottom")
out = os.path.join(HERE, "trig_network_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER)
print(out)
