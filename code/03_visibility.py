"""Step 3 (plan Q4, the main test): intervisibility of nearest same-order neighbours over the Terrarium z9 terrain model
with curvature and refraction; planned placebos and robustness. Writes data/pairs.csv, data/profiles.json, scratch r03.json."""
import pandas as pd
import geopandas as gpd
import shapely
from scipy.spatial import Delaunay
from common import *

rng = np.random.default_rng(SEED + 3)
S = pd.read_csv(f"{DATA}/stations.csv").set_index("sid")
NN = pd.read_csv(f"{DATA}/nn_pairs.csv")
rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True)
land = shapely.make_valid(rg[rg.areanm != "Northern Ireland"].to_crs(27700).geometry.make_valid().buffer(0).union_all())
shapely.prepare(land)
minx, miny, maxx, maxy = land.bounds
load_dem()


def top(sid, extra=INSTR, dem_only=False):
    r = S.loc[sid]
    h = r.dem if (dem_only or not (r.height > 0)) else r.height
    if not np.isfinite(h): h = r.height if r.height > 0 else 0.0
    return float(h) + extra


def pairs_for(order, k=1):
    """unique undirected pairs to each station's k nearest same-order neighbours (plan sets)."""
    from scipy.spatial import cKDTree
    sel = (S["order"] == order) & ((S["kind"] == "pillar") if order > 1 else True)
    G = S[sel]
    xy = G[["easting", "northing"]].values
    d, i = cKDTree(xy).query(xy, k=k + 1)
    out = set()
    for a in range(len(G)):
        for j in range(1, k + 1):
            u, v = G.index[a], G.index[i[a, j]]
            out.add((min(u, v), max(u, v)))
    return sorted(out)


def run(pairs, **kw):
    dem_only = kw.pop("dem_only", False); extra = kw.pop("extra", INSTR)
    res = []
    for u, v in pairs:
        a, b = S.loc[u], S.loc[v]
        c, D, w = los(a.easting, a.northing, top(u, extra, dem_only), b.easting, b.northing, top(v, extra, dem_only), **kw)
        res.append((u, v, c, D, w))
    return pd.DataFrame(res, columns=["sid_a", "sid_b", "clear_m", "dist_m", "worst_at_m"])


def share(df):
    k = int((df.clear_m >= 0).sum()); n = len(df)
    p, lo, hi = wilson(k, n)
    return {"k": k, "n": n, "pc": p, "lo": lo, "hi": hi}


def on_land(x, y):
    return shapely.contains_xy(land, x, y)


def placebo_shift(pairs, km=1.0, draws=10):
    out = []
    for u, v in pairs:
        a, b = S.loc[u], S.loc[v]
        for _ in range(draws):
            pts = []
            for r in (a, b):
                for _t in range(50):
                    th = rng.uniform(0, 2 * np.pi)
                    x, y = r.easting + km * 1000 * np.cos(th), r.northing + km * 1000 * np.sin(th)
                    if on_land(x, y): break
                pts.append((x, y))
            (x1, y1), (x2, y2) = pts
            l1, t1 = bng_to_ll([x1, x2], [y1, y2])
            z = elev(l1, t1)
            z = np.where(np.isnan(z), 0, np.maximum(z, 0))
            c, D, w = los(x1, y1, z[0] + INSTR, x2, y2, z[1] + INSTR)
            out.append((u, v, c, D))
    return pd.DataFrame(out, columns=["sid_a", "sid_b", "clear_m", "dist_m"])


def placebo_random(dists, draws=10):
    out = []
    for D in dists:
        for _ in range(draws):
            while True:
                x1, y1 = rng.uniform(minx, maxx), rng.uniform(miny, maxy)
                th = rng.uniform(0, 2 * np.pi)
                x2, y2 = x1 + D * np.cos(th), y1 + D * np.sin(th)
                if on_land(x1, y1) and on_land(x2, y2): break
            lo_, la_ = bng_to_ll([x1, x2], [y1, y2])
            z = elev(lo_, la_); z = np.where(np.isnan(z), 0, np.maximum(z, 0))
            c, _, _ = los(x1, y1, z[0] + INSTR, x2, y2, z[1] + INSTR)
            out.append((D, c))
    return pd.DataFrame(out, columns=["dist_m", "clear_m"])


def boot_diff(a, b, B=2000):
    a = (np.asarray(a) >= 0).astype(float); b = (np.asarray(b) >= 0).astype(float)
    d = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(B)]
    return 100 * (a.mean() - b.mean()), 100 * np.percentile(d, 2.5), 100 * np.percentile(d, 97.5)


R = {"vis": {}, "rob": {}, "plc": {}, "dem": {}}
allp = []
for o in (1, 2, 3):
    pr = pairs_for(o)
    df = run(pr); df["order"] = o; df["set"] = "nn1"
    allp.append(df)
    R["vis"][f"o{o}"] = share(df) | {"dist_med_km": float(df.dist_m.median() / 1000), "clear_med_m": float(df.clear_m.median())}
    print(o, R["vis"][f"o{o}"])
P1 = allp[0]
pr1 = list(zip(P1.sid_a, P1.sid_b))

# Delaunay edges of primaries <= 80 km (secondary set)
G = S[S["order"] == 1]
T = Delaunay(G[["easting", "northing"]].values).simplices
E = set()
for t in T:
    for i_, j_ in ((0, 1), (1, 2), (0, 2)):
        u, v = G.index[t[i_]], G.index[t[j_]]
        if math.hypot(S.loc[u].easting - S.loc[v].easting, S.loc[u].northing - S.loc[v].northing) <= 80000:
            E.add((min(u, v), max(u, v)))
dl = run(sorted(E)); dl["order"] = 1; dl["set"] = "delaunay"
allp.append(dl)
R["vis"]["o1_delaunay"] = share(dl) | {"dist_med_km": float(dl.dist_m.median() / 1000)}
print("delaunay", R["vis"]["o1_delaunay"])
# by distance band (exploratory)
for lo_, hi_ in ((0, 20), (20, 40), (40, 80)):
    sub = dl[(dl.dist_m >= lo_ * 1000) & (dl.dist_m < hi_ * 1000)]
    R["vis"][f"o1_delaunay_{lo_}_{hi_}"] = share(sub)

# robustness for primaries (planned)
for name, kw in (("k0", {"k": 0.0}), ("k075", {"k": 0.075}), ("k20", {"k": 0.20}), ("margin0", {"margin": 0.0}),
                 ("margin500", {"margin": 500.0}), ("instr0", {"extra": 0.0}), ("instr5", {"extra": 5.0}),
                 ("step50", {"step": 50.0}), ("demonly", {"dem_only": True})):
    R["rob"][name] = share(run(pr1, **kw))
    print(name, R["rob"][name])
pr1k2 = pairs_for(1, k=2)
R["rob"]["nn2"] = share(run(pr1k2))
P1r = P1.assign(region=S.loc[P1.sid_a, "region"].values)
R["rob"]["loro"] = {rgn: share(P1r[P1r.region != rgn])["pc"] for rgn in sorted(P1r.region.unique())}
R["rob"]["loro_min"] = min(R["rob"]["loro"].values()); R["rob"]["loro_max"] = max(R["rob"]["loro"].values())
R["rob"]["pillars_only"] = share(P1[(S.loc[P1.sid_a, "kind"].values == "pillar") & (S.loc[P1.sid_b, "kind"].values == "pillar")])
R["rob"]["intersected_any"] = share(P1[(S.loc[P1.sid_a, "kind"].values == "intersected") | (S.loc[P1.sid_b, "kind"].values == "intersected")])
print(R["rob"])

# placebos (planned)
pa = placebo_shift(pr1)
pb = placebo_random(P1.dist_m.values)
R["plc"]["shift1km"] = share(pa); R["plc"]["random"] = share(pb)
R["plc"]["diff_shift"] = dict(zip(("pp", "lo", "hi"), boot_diff(P1.clear_m, pa.clear_m)))
R["plc"]["diff_random"] = dict(zip(("pp", "lo", "hi"), boot_diff(P1.clear_m, pb.clear_m)))
for o in (2, 3):
    Po = allp[o - 1]
    rb = placebo_random(Po.dist_m.values, draws=2)
    R["plc"][f"random_o{o}"] = share(rb)
    R["plc"][f"diff_random_o{o}"] = dict(zip(("pp", "lo", "hi"), boot_diff(Po.clear_m, rb.clear_m)))
print(R["plc"])

# DEM validation at pillars with a recorded height
pil = S[(S.kind == "pillar") & (S.height > 0) & S.dem.notna()]
err = pil.dem - pil.height
R["dem"] = {"n": len(pil), "bias": float(err.median()), "mae": float(err.abs().median()), "p90": float(err.abs().quantile(0.9)),
            "below_pc": float(100 * (err < 0).mean())}
for o in (1, 2, 3):
    e = err[pil["order"] == o]
    R["dem"][f"o{o}_bias"] = float(e.median()); R["dem"][f"o{o}_mae"] = float(e.abs().median()); R["dem"][f"o{o}_n"] = len(e)
print(R["dem"])

out = pd.concat(allp, ignore_index=True)
out["visible"] = (out.clear_m >= 0).astype(int)
out["clear_m"] = out.clear_m.round(1); out["dist_km"] = (out.dist_m / 1000).round(3); out["worst_at_km"] = (out.worst_at_m / 1000).round(2)
out = out.drop(columns=["dist_m", "worst_at_m"])
out.to_csv(f"{DATA}/pairs.csv", index=False)
pa.to_csv(f"{SCR}/placebo_shift.csv", index=False); pb.to_csv(f"{SCR}/placebo_random.csv", index=False)
jsave(R, f"{SCR}/r03.json", indent=1)
