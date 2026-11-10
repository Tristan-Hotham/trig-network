"""Step 6: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf,
vector) and header.png (1200 x 630). Light paper background; order 1 red, order 2 gold, order 3 blue, order 4 grey."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection
import pandas as pd
import geopandas as gpd
import shapely
from PIL import Image
from scipy.spatial import Delaunay
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE, LAND = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3", "#EADFC2"
RED, BLUE, GREY, GOLD, GREEN = "#B4442E", "#2F6A9E", "#9C9384", "#C98A2B", "#4F7A4A"
OC = {1: RED, 2: GOLD, 3: BLUE, 4: GREY}
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
S = pd.read_csv(f"{DATA}/stations.csv")
Si = S.set_index("sid")
P = pd.read_csv(f"{DATA}/pairs.csv")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD):
    os.makedirs(d_, exist_ok=True)
SRC = "Data: OS legacy triangulation stations (Crown copyright, via the trigpoints R package);\nTerrain Tiles (AWS Open Data, Mapzen). maps.tristanhotham.com/trig-network"
rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True)
GB = shapely.make_valid(rg[rg.areanm != "Northern Ireland"].to_crs(27700).geometry.make_valid().buffer(0).union_all()).simplify(300)


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.05, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8.3, family=MONO, color=MUT, va="bottom", linespacing=1.4)


def draw_gb(ax, fc=LAND, ec="#BFAE86"):
    geoms = GB.geoms if hasattr(GB, "geoms") else [GB]
    for g in geoms:
        x, y = g.exterior.xy
        ax.fill(np.array(x) / 1000, np.array(y) / 1000, fc=fc, ec=ec, lw=0.4, zorder=1)
    ax.set_aspect("equal"); ax.axis("off")


def segs(df):
    a = Si.loc[df.sid_a]; b = Si.loc[df.sid_b]
    return np.stack([np.c_[a.easting.values, a.northing.values], np.c_[b.easting.values, b.northing.values]], axis=1) / 1000


# ---------- 1. the primary network map ----------
fig = plt.figure(figsize=(9, 12))
ax = fig.add_axes([0.02, 0.06, 0.96, 0.82])
draw_gb(ax)
P1 = S[S["order"] == 1]
tri = Delaunay(P1[["easting", "northing"]].values).simplices
E = set()
for t in tri:
    for i_, j_ in ((0, 1), (1, 2), (0, 2)):
        u, v = P1.sid.values[t[i_]], P1.sid.values[t[j_]]
        if math.hypot(Si.loc[u].easting - Si.loc[v].easting, Si.loc[u].northing - Si.loc[v].northing) <= 80000:
            E.add((min(u, v), max(u, v)))
E = pd.DataFrame(sorted(E), columns=["sid_a", "sid_b"])
ax.add_collection(LineCollection(segs(E), colors="#B9A57E", lw=0.5, zorder=2))
nn = P[(P.order == 1) & (P.set == "nn1")]
ax.add_collection(LineCollection(segs(nn[nn.visible == 1]), colors=BLUE, lw=1.6, zorder=3))
ax.add_collection(LineCollection(segs(nn[nn.visible == 0]), colors=RED, lw=2.2, zorder=4))
ax.scatter(P1.easting / 1000, P1.northing / 1000, s=10, c=INK, zorder=5, lw=0)
ax.set_xlim(-10, 670); ax.set_ylim(0, 1230)
title(fig, "The primary triangulation, and what the terrain says",
      f"{R['counts']['orders']['1']} primary stations (dots). Blue: line to the nearest primary neighbour clear over the terrain model;\nred: blocked. Faint lines: the full triangle net (sides up to 80 km).")
ax.text(0, 1150, f"{R['vis']['o1']['k']} of {R['vis']['o1']['n']} nearest-neighbour\nlines are clear ({R['vis']['o1']['pc']:.0f}%)", fontsize=15, color=INK, family=DISP, path_effects=HALO)
ax.plot([0, 30], [1090, 1090], color=BLUE, lw=2); ax.text(38, 1090, "clear line of sight", va="center", fontsize=11, color=INK)
ax.plot([0, 30], [1065, 1065], color=RED, lw=2.2); ax.text(38, 1065, "blocked in the model", va="center", fontsize=11, color=INK)
ax.plot([0, 30], [1040, 1040], color="#B9A57E", lw=0.8); ax.text(38, 1040, "other triangle sides", va="center", fontsize=11, color=INK)
ax.scatter([15], [1015], s=12, c=INK); ax.text(38, 1015, "primary station", va="center", fontsize=11, color=INK)
foot(fig)
out(fig, "map")

# ---------- 2. spacing by order ----------
NN = pd.read_csv(f"{DATA}/nn_pairs.csv")
fig, axs = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={"width_ratios": [1.5, 1]})
fig.subplots_adjust(left=0.07, right=0.97, top=0.8, bottom=0.2, wspace=0.28)
ax = axs[0]
bins = np.logspace(np.log10(0.2), np.log10(80), 50)
for o in (1, 2, 3):
    d = NN[NN.order == o].km
    ax.hist(d, bins=bins, histtype="step", lw=2.2, color=OC[o], density=True)
    g = R["geom"][f"o{o}_{'all' if o == 1 else 'pillar'}"]
    ax.axvline(g["nnd_med"], color=OC[o], lw=1, ls=":")
    xy_ = {1: (24, 0.075), 2: (9.5, 0.165), 3: (0.75, 0.21)}[o]
    ax.text(*xy_, f"order {o}\nmedian {g['nnd_med']:.1f} km", color=OC[o], fontsize=11, fontweight="bold", path_effects=HALO)
ax.set_xscale("log"); ax.set_xticks([0.5, 1, 2, 5, 10, 20, 50]); ax.set_xticklabels(["0.5", "1", "2", "5", "10", "20", "50"])
ax.set_xlabel("distance to the nearest station of the same order (km, log scale)"); ax.set_ylabel("density")
ax.set_title("Each order is a finer mesh", loc="left", fontsize=13, color=INK)
ax = axs[1]
labs = []
for j, (k_, lab) in enumerate((("o1_all", "Primary"), ("o2_pillar", "Secondary pillars"), ("o3_pillar", "Third-order pillars"))):
    g = R["geom"][k_]
    ax.plot([g["ce_csr_lo"], g["ce_csr_hi"]], [j, j], color=GREY, lw=8, solid_capstyle="butt", alpha=0.6)
    ax.scatter([g["ce_R"]], [j], s=90, color=OC[j + 1], zorder=3, edgecolor="white")
    ax.text(g["ce_R"] + 0.03, j + 0.18, f"R = {g['ce_R']:.2f}", fontsize=11, color=INK)
    labs.append(lab)
ax.axvline(1, color=MUT, lw=0.8, ls="--")
ax.set_yticks(range(3)); ax.set_yticklabels(labs); ax.set_ylim(-0.6, 2.7); ax.set_xlim(0.85, 1.75)
ax.set_xlabel("Clark and Evans ratio (above 1 = more even than random)")
ax.set_title("More even than random", loc="left", fontsize=13, color=INK)
ax.text(1.0, -0.5, "grey bars: 95% range for random points on the same land", fontsize=9.5, color=MUT)
title(fig, "How far apart are the trig points?", "Nearest same-order neighbour, and how evenly spaced each order is compared with random points on the same land.")
foot(fig)
out(fig, "spacing")

# ---------- 3. triangle shapes ----------
TR = pd.read_csv(f"{DATA}/primary_triangles.csv")
mn = TR[["angle_a", "angle_b", "angle_c"]].min(axis=1)
fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.17)
ax.hist(mn, bins=np.arange(0, 61, 2.5), color=RED, alpha=0.85, edgecolor=PAPER, lw=1.5, label="primary triangles")
ax.axvline(30, color=INK, lw=1, ls="--"); ax.text(30.5, ax.get_ylim()[1] * 0.92, "30 degrees", fontsize=10, color=INK)
ax.set_xlabel("smallest angle of each triangle (degrees)"); ax.set_ylabel("triangles")
t = R["tri"]
ax.text(42, ax.get_ylim()[1] * 0.62, f"{t['well_pc']:.0f}% of the {t['n']} primary triangles\nhave every angle of 30 degrees or more.\nRandom points on the same land: {t['csr_well_pc']:.0f}%\n(95% range {t['csr_well_lo']:.0f} to {t['csr_well_hi']:.0f}%)", fontsize=11, color=INK)
title(fig, "Well-shaped triangles", "Smallest angle of each triangle in the net joining neighbouring primary stations (sides up to 80 km).")
foot(fig)
out(fig, "triangles", blog=False)

# ---------- 4. when it was built ----------
pil = S[S.kind == "pillar"]
yrs = np.arange(1936, 1996)
fig, ax = plt.subplots(figsize=(12, 6.2)); fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.17)
bot = np.zeros(len(yrs))
for o in (1, 2, 3, 4):
    c = pil[pil["order"] == o].com_year.value_counts().reindex(yrs, fill_value=0).values
    ax.bar(yrs, c, bottom=bot, color=OC[o], width=0.85, label=f"order {o}", edgecolor=PAPER, lw=0.6)
    bot += c
ax.axvspan(1939.7, 1941.9, color=RULE, alpha=0.6, zorder=0)
ax.text(1940.8, bot.max() * 0.9, "none\ndated\n1940 or\n1941", fontsize=9.5, ha="center", color=MUT)
ax.set_xlim(1935, 1996); ax.set_ylabel("pillars, by recorded commissioning year")
ax.legend(frameon=False, loc="upper right")
b = R["build"]
ax.text(1964, bot.max() * 0.55, f"{b['pillars_1936_1962']:,} of {b['pillars_n']:,} pillars ({b['pc']:.0f}%)\ndated 1936 to 1962", fontsize=13, color=INK, family=DISP)
title(fig, "Built in a generation", "Trig pillars by the commissioning year in the OS station list. Many primaries carry the date of their block of the network.")
foot(fig)
out(fig, "build")

# ---------- 5. intervisibility and placebos ----------
rows = [("Primary, nearest neighbour", R["vis"]["o1"], RED), ("Primary, all triangle sides", R["vis"]["o1_delaunay"], RED),
        ("Secondary pillars, nearest", R["vis"]["o2"], GOLD), ("Third-order pillars, nearest", R["vis"]["o3"], BLUE),
        ("Same lines, both ends moved 1 km", R["plc"]["shift1km"], GREY), ("Random land pairs, same lengths", R["plc"]["random"], GREY),
        ("Primary, terrain-model heights only", R["rob"]["demonly"], "#C9B79A")]
fig, ax = plt.subplots(figsize=(11, 6.8)); fig.subplots_adjust(left=0.33, right=0.95, top=0.8, bottom=0.2)
for j, (lab, v, c) in enumerate(rows[::-1]):
    ax.plot([v["lo"], v["hi"]], [j, j], color=c, lw=3)
    ax.scatter([v["pc"]], [j], s=80, color=c, zorder=3, edgecolor="white")
    ax.text(v["hi"] + 1.5, j, f"{v['pc']:.0f}%  ({v['k']:,} of {v['n']:,})", va="center", fontsize=10.5, color=INK)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]])
ax.set_xlim(0, 118); ax.set_xticks([0, 20, 40, 60, 80, 100]); ax.set_xlabel("share of lines with a clear line of sight (95% interval)")
ax.axvline(80, color=MUT, lw=0.8, ls="--"); ax.text(79.5, len(rows) - 0.55, "planned threshold 80%", fontsize=9, color=MUT, ha="right")
title(fig, "Can neighbouring trig points see each other?", "Lines of sight over the terrain model with Earth curvature and refraction, against placebo lines.")
foot(fig)
out(fig, "vis")

# ---------- 6. robustness forest ----------
rb = [("Main (k = 0.13, 1.5 m, 250 m margin)", R["vis"]["o1"]), ("No refraction (k = 0)", R["rob"]["k0"]), ("k = 0.075", R["rob"]["k075"]),
      ("k = 0.20", R["rob"]["k20"]), ("No end margin", R["rob"]["margin0"]), ("500 m end margin", R["rob"]["margin500"]),
      ("No instrument height", R["rob"]["instr0"]), ("5 m signal height", R["rob"]["instr5"]), ("50 m profile step", R["rob"]["step50"]),
      ("Two nearest neighbours", R["rob"]["nn2"]), ("Pillar to pillar only", R["rob"]["pillars_only"]),
      ("Terrain-model end heights", R["rob"]["demonly"])]
fig, ax = plt.subplots(figsize=(10, 6.6)); fig.subplots_adjust(left=0.36, right=0.95, top=0.82, bottom=0.12)
for j, (lab, v) in enumerate(rb[::-1]):
    ax.plot([v["lo"], v["hi"]], [j, j], color=RED if j == len(rb) - 1 else INK, lw=2.5)
    ax.scatter([v["pc"]], [j], s=55, color=RED if j == len(rb) - 1 else INK, zorder=3)
ax.set_yticks(range(len(rb))); ax.set_yticklabels([r[0] for r in rb[::-1]]); ax.set_xlim(55, 101)
ax.axvline(80, color=MUT, lw=0.8, ls="--")
ax.set_xlabel("primary nearest-neighbour lines clear (%, 95% interval)")
lo_ = R["rob"]["loro_min"]; hi_ = R["rob"]["loro_max"]
ax.text(56, -1.2, f"Leaving out one region at a time: {lo_:.1f}% to {hi_:.1f}%", fontsize=10, color=MUT)
title(fig, "Every planned check", "Share of primary nearest-neighbour lines with a clear sight line under each planned variation.", y=0.97)
foot(fig)
out(fig, "robust", blog=False)

# ---------- 7. profiles ----------
def profile(u, v, hu=None, hv=None, k=K_MAIN):
    a, b = Si.loc[u], Si.loc[v]
    h1 = hu if hu is not None else (a.height if a.height > 0 else a.dem) + INSTR
    h2 = hv if hv is not None else (b.height if b.height > 0 else b.dem) + INSTR
    D = math.hypot(b.easting - a.easting, b.northing - a.northing)
    t = np.linspace(0, 1, int(D // 50) + 1); d1 = t * D
    lon, lat = bng_to_ll(a.easting + t * (b.easting - a.easting), a.northing + t * (b.northing - a.northing))
    z = np.maximum(np.nan_to_num(elev(lon, lat)), 0)
    drop = d1 * (D - d1) * (1 - k) / (2 * R_EARTH)
    return d1 / 1000, z - drop, h1 + t * (h2 - h1), a["name"], b["name"]


def sid(name, o=1):
    return int(S[(S["name"] == name) & (S["order"] == o)].sid.iloc[0])


vis1 = P[(P.order == 1) & (P.set == "nn1") & (P.visible == 1)]
vis1 = vis1[Si.loc[vis1.sid_a].dem.notna().values & Si.loc[vis1.sid_b].dem.notna().values]
lng = vis1.sort_values("dist_km").iloc[-1]
cases = [((int(lng.sid_a), int(lng.sid_b)), None, "The longest nearest-neighbour primary line: clear"),
         ((sid("Crimplesham"), sid("Walpole St Peters")), 30.0, "Flat Norfolk: blocked by a few metres, clear from a 30 m steel tower"),
         ((sid("West Hills"), sid("Buddon")), None, "Buddon, a ground mark with no recorded height: blocked"),
         ((sid("Ben Lomond") if (S["name"] == "Ben Lomond").any() else int(lng.sid_a), None), None, "")]
fig, axs = plt.subplots(3, 1, figsize=(11, 10)); fig.subplots_adjust(left=0.09, right=0.97, top=0.87, bottom=0.12, hspace=0.55)
for ax, ((u, v), tower, lab) in zip(axs, cases[:3]):
    d, z, line, na, nb = profile(u, v)
    ax.fill_between(d, z, -5, color=LAND, ec="#BFAE86", lw=0.8)
    ax.plot(d, line, color=BLUE if tower is None and lab.endswith("clear") else RED, lw=1.8, label="sight line, 1.5 m above each mark")
    if tower:
        a, b = Si.loc[u], Si.loc[v]
        _, _, l2, _, _ = profile(u, v, (a.height if a.height > 0 else a.dem) + tower, (b.height if b.height > 0 else b.dem) + tower)
        ax.plot(d, l2, color=BLUE, lw=1.8, ls="--", label="from 30 m towers")
        ax.legend(frameon=False, fontsize=9.5, loc="upper right")
        line = np.maximum(line, l2)
    ax.set_title(f"{na} to {nb}: {lab.split(': ')[1] if ': ' in lab else lab}", loc="left", fontsize=12, color=INK)
    ax.set_ylabel("height (m)"); ax.set_xlim(0, d.max()); ax.set_ylim(max(-5, min(z.min(), line.min()) - 10), max(z.max(), line.max()) * 1.12 + 5)
axs[-1].set_xlabel("distance along the line (km); terrain lowered for Earth curvature less refraction (k = 0.13)")
title(fig, "Three lines of sight", "Terrain model profiles between trig stations, drawn the way the test sees them.", y=0.975)
foot(fig)
out(fig, "profiles")

# ---------- 8. survival ----------
fig, axs = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={"width_ratios": [1, 1.25]})
fig.subplots_adjust(left=0.2, right=0.97, top=0.8, bottom=0.2, wspace=0.6)
ax = axs[0]
kd = [("pillar", "Pillars"), ("intersected", "Spires, towers, masts"), ("surface", "Ground marks (bolts, blocks)")]
for j, (k_, lab) in enumerate(kd[::-1]):
    v = R["surv"]["kind"][k_]
    ax.barh(j, v["pc"], color=[GREY, GOLD, RED][::-1][j], height=0.6)
    ax.plot([v["lo"], v["hi"]], [j, j], color=INK, lw=1.2)
    ax.text(v["hi"] + 1, j, f"{v['pc']:.0f}%  ({v['k']:,} of {v['n']:,})", va="center", fontsize=10.5, color=INK)
ax.set_yticks(range(3)); ax.set_yticklabels([l for _, l in kd[::-1]]); ax.set_xlim(0, 75)
ax.set_xlabel("recorded destroyed (%)"); ax.set_title("By kind of station", loc="left", fontsize=13, color=INK)
ax = axs[1]
reg = sorted(R["surv"]["region"].items(), key=lambda kv: kv[1]["pil_pc"])
for j, (rn, v) in enumerate(reg):
    ax.plot([v["pil_lo"], v["pil_hi"]], [j, j], color=RED, lw=2)
    ax.scatter([v["pil_pc"]], [j], s=40, color=RED, zorder=3)
    ax.text(v["pil_hi"] + 0.4, j, f"{v['pil_k']} of {v['pil_n']:,}", va="center", fontsize=9.5, color=MUT)
ax.set_yticks(range(len(reg))); ax.set_yticklabels([r for r, _ in reg]); ax.set_xlim(0, 33)
ax.set_xlabel("pillars recorded destroyed (%, 95% interval)"); ax.set_title("Pillars, by region", loc="left", fontsize=13, color=INK)
title(fig, "What has been lost", f"Stations flagged destroyed in the OS list, which OS no longer maintains. {R['headline']['pillars_destroyed']:,} of {R['headline']['pillars']:,} pillars.")
foot(fig)
out(fig, "survival")

# ---------- 9. DEM check ----------
p = S[(S.kind == "pillar") & (S.height > 0) & S.dem.notna()]
fig, ax = plt.subplots(figsize=(10, 6)); fig.subplots_adjust(left=0.1, right=0.97, top=0.8, bottom=0.14)
ax.scatter(p.height, p.dem - p.height, s=4, color=INK, alpha=0.25, lw=0, rasterized=True)
ax.axhline(0, color=MUT, lw=0.8)
ax.set_xlabel("surveyed height of the pillar (m)"); ax.set_ylabel("terrain model minus surveyed height (m)")
ax.text(700, 40, f"median {R['dem']['bias']:.0f} m\n({R['dem']['n']:,} pillars)", fontsize=12, color=INK)
title(fig, "The terrain model rounds off the summits", "At zoom 9 a pixel is about 190 m across, so hilltops come out lower than the surveyed pillar heights.")
foot(fig)
out(fig, "dem", blog=False)

# ---------- header ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100)
ax = fig.add_axes([0.52, 0.0, 0.48, 1.0]); draw_gb(ax)
ax.add_collection(LineCollection(segs(E), colors="#B9A57E", lw=0.4, zorder=2))
ax.add_collection(LineCollection(segs(nn[nn.visible == 1]), colors=BLUE, lw=1.2, zorder=3))
ax.add_collection(LineCollection(segs(nn[nn.visible == 0]), colors=RED, lw=1.8, zorder=4))
ax.scatter(P1.easting / 1000, P1.northing / 1000, s=5, c=INK, zorder=5, lw=0)
ax.set_xlim(0, 660); ax.set_ylim(0, 1000)
fig.text(0.05, 0.8, "The trig pillar\nnetwork", fontsize=46, family=DISP, fontweight="bold", color=INK, va="top", linespacing=1.0)
fig.text(0.05, 0.45, "How Britain was measured, and\nwhether the hills still see each other", fontsize=17, color=MUT, va="top")
fig.text(0.05, 0.24, f"{R['vis']['o1']['pc']:.0f}% of neighbouring primary stations\nare in sight over today's terrain model", fontsize=15, color=RED, va="top", family=DISP)
fig.text(0.05, 0.06, "maps.tristanhotham.com/trig-network", fontsize=11, family=MONO, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
plt.close(fig)
im = Image.open(os.path.join(ROOT, "header.png")); assert im.size == (1200, 630), im.size
print("figures done")
