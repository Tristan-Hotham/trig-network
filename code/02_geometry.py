"""Step 2 (plan Q1, Q2): spacing, regularity and triangle shapes of the network; commissioning years.
Writes data/nn_pairs.csv (each station's nearest same-order neighbour), data/primary_triangles.csv and scratch r02.json."""
import pandas as pd
import geopandas as gpd
import shapely
from scipy.spatial import cKDTree, Delaunay
from common import *

rng = np.random.default_rng(SEED)
S = pd.read_csv(f"{DATA}/stations.csv")
rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True)
land = shapely.make_valid(rg[rg.areanm != "Northern Ireland"].to_crs(27700).geometry.make_valid().buffer(0).union_all())
shapely.prepare(land)
AREA = land.area / 1e6
minx, miny, maxx, maxy = land.bounds


def csr(n):
    out = []
    while sum(len(a) for a in out) < n:
        x = rng.uniform(minx, maxx, 4 * n); y = rng.uniform(miny, maxy, 4 * n)
        k = shapely.contains_xy(land, x, y)
        out.append(np.c_[x[k], y[k]])
    return np.vstack(out)[:n]


def nnd(xy):
    d, _ = cKDTree(xy).query(xy, k=2)
    return d[:, 1]


def boot_median(x, B=2000):
    m = [np.median(rng.choice(x, len(x))) for _ in range(B)]
    return float(np.median(x)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def tri_stats(xy, maxside=80000):
    T = Delaunay(xy).simplices
    P = xy[T]
    a = np.linalg.norm(P[:, 1] - P[:, 2], axis=1); b = np.linalg.norm(P[:, 0] - P[:, 2], axis=1); c = np.linalg.norm(P[:, 0] - P[:, 1], axis=1)
    ok = (a <= maxside) & (b <= maxside) & (c <= maxside)
    cen = P.mean(axis=1)
    near = shapely.dwithin(land, shapely.points(cen[:, 0], cen[:, 1]), 10000)
    ok &= near
    A = np.degrees(np.arccos(np.clip((b ** 2 + c ** 2 - a ** 2) / (2 * b * c), -1, 1)))
    B_ = np.degrees(np.arccos(np.clip((a ** 2 + c ** 2 - b ** 2) / (2 * a * c), -1, 1)))
    C = 180 - A - B_
    mn = np.minimum(np.minimum(A, B_), C)[ok]
    side = np.r_[a[ok], b[ok], c[ok]]
    return T[ok], mn, np.c_[A, B_, C][ok], side


R = {"geom": {}, "build": {}}
pairs = []
for o in (1, 2, 3, 4):
    for sub, sel in (("all", S["order"] == o), ("pillar", (S["order"] == o) & (S["kind"] == "pillar"))):
        G = S[sel].reset_index(drop=True)
        if len(G) < 20: continue
        xy = G[["easting", "northing"]].values
        d, i = cKDTree(xy).query(xy, k=2)
        dist = d[:, 1] / 1000
        med, lo, hi = boot_median(dist)
        ce = dist.mean() / (0.5 / math.sqrt(len(G) / AREA))
        sims = []
        nsim = 199 if len(G) <= 4000 else 49
        for _ in range(nsim):
            q = csr(len(G)); sims.append(nnd(q).mean() / 1000 / (0.5 / math.sqrt(len(G) / AREA)))
        sims = np.array(sims)
        R["geom"][f"o{o}_{sub}"] = {"n": len(G), "nnd_med": med, "nnd_lo": lo, "nnd_hi": hi,
                                    "nnd_q25": float(np.percentile(dist, 25)), "nnd_q75": float(np.percentile(dist, 75)),
                                    "nnd_mean": float(dist.mean()), "density_per_1000km2": 1000 * len(G) / AREA,
                                    "ce_R": ce, "ce_csr_mean": float(sims.mean()), "ce_csr_lo": float(np.percentile(sims, 2.5)),
                                    "ce_csr_hi": float(np.percentile(sims, 97.5)), "ce_nsim": nsim,
                                    "ce_p": float((np.sum(sims >= ce) + 1) / (nsim + 1))}
        if sub == ("all" if o == 1 else "pillar"):
            for a_, b_ in zip(range(len(G)), i[:, 1]):
                pairs.append({"order": o, "set": sub, "sid_a": int(G.sid[a_]), "sid_b": int(G.sid[b_]), "km": round(float(d[a_, 1] / 1000), 3)})
        print(o, sub, R["geom"][f"o{o}_{sub}"])
R["geom"]["land_km2"] = AREA
pd.DataFrame(pairs).to_csv(f"{DATA}/nn_pairs.csv", index=False)

# H1 bootstrap difference order1 vs order2 median (all kinds)
d1 = pd.DataFrame(pairs)
# triangles of primaries
P1 = S[S["order"] == 1].reset_index(drop=True)
xy1 = P1[["easting", "northing"]].values
T, mn, ang, side = tri_stats(xy1)
csr_mn, csr_w = [], []
for _ in range(199):
    q = csr(len(P1))
    _, m2, _, _ = tri_stats(q)
    csr_mn.append(np.median(m2)); csr_w.append(np.mean(m2 >= 30))
csr_mn = np.array(csr_mn); csr_w = np.array(csr_w)
bw = [np.mean(rng.choice(mn, len(mn)) >= 30) for _ in range(2000)]
R["tri"] = {"n": int(len(T)), "minang_med": float(np.median(mn)), "well_pc": float(100 * np.mean(mn >= 30)),
            "well_lo": float(100 * np.percentile(bw, 2.5)), "well_hi": float(100 * np.percentile(bw, 97.5)),
            "csr_minang_med": float(csr_mn.mean()), "csr_well_pc": float(100 * csr_w.mean()),
            "csr_well_lo": float(100 * np.percentile(csr_w, 2.5)), "csr_well_hi": float(100 * np.percentile(csr_w, 97.5)),
            "side_med_km": float(np.median(side) / 1000), "side_q25_km": float(np.percentile(side, 25) / 1000),
            "side_q75_km": float(np.percentile(side, 75) / 1000), "max_angle_med": float(np.median(ang.max(axis=1)))}
tri = pd.DataFrame({"sid_a": P1.sid.values[T[:, 0]], "sid_b": P1.sid.values[T[:, 1]], "sid_c": P1.sid.values[T[:, 2]],
                    "angle_a": ang[:, 0].round(2), "angle_b": ang[:, 1].round(2), "angle_c": ang[:, 2].round(2)})
tri.to_csv(f"{DATA}/primary_triangles.csv", index=False)
np.save(f"{SCR}/csr_minang.npy", csr_mn)
print(R["tri"])

# Q2 commissioning years
pil = S[S.kind == "pillar"]
k = int(pil.com_year.between(1936, 1962).sum()); n = int(pil.com_year.notna().sum())
p, lo, hi = wilson(k, n)
R["build"] = {"pillars_n": len(pil), "pillars_dated": n, "pillars_1936_1962": k, "pc": p, "lo": lo, "hi": hi,
              "first": int(S.com_year.min()), "last": int(S.com_year.max()),
              "pillars_first": int(pil.com_year.min()), "pillars_last": int(pil.com_year.max()),
              "pillars_peak_year": int(pil.com_year.value_counts().idxmax()), "pillars_peak_n": int(pil.com_year.value_counts().max()),
              "pre_war_pillars": int((pil.com_year <= 1939).sum()), "pillars_1940s": int(pil.com_year.between(1940, 1949).sum()),
              "pillars_1950s": int(pil.com_year.between(1950, 1959).sum()), "pillars_after_1962": int((pil.com_year > 1962).sum()),
              "stations_dated": int(S.com_year.notna().sum()),
              "primary_blocks": {b: {"n": int(len(g)), "year": int(g.com_year.min())} for b, g in S[S["order"] == 1].groupby("block") if str(b).startswith("FIG")}}
by = S[S.com_year.notna()].groupby(["com_year", "kind"]).size().unstack(fill_value=0)
by.to_csv(f"{DATA}/commissioning_by_year.csv")
print(R["build"])
jsave(R, f"{SCR}/r02.json", indent=1)
