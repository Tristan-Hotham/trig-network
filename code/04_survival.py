"""Step 4 (plan Q3): which stations are recorded destroyed; the planned logit with SEs clustered by 10 km square;
the OSM cross-check. Writes data/survival_model.csv, data/destroyed_by_region.csv and scratch r04.json."""
import pandas as pd
import statsmodels.formula.api as smf
from common import *

S = pd.read_csv(f"{DATA}/stations.csv")
R = {"surv": {"kind": {}, "order": {}, "region": {}, "pillar_order": {}}}
k = int(S.destroyed.sum()); n = len(S)
R["surv"]["all"] = dict(zip(("pc", "lo", "hi"), wilson(k, n))) | {"k": k, "n": n}
for kd, g in S.groupby("kind"):
    R["surv"]["kind"][kd] = dict(zip(("pc", "lo", "hi"), wilson(int(g.destroyed.sum()), len(g)))) | {"k": int(g.destroyed.sum()), "n": len(g)}
for o, g in S.groupby("order"):
    R["surv"]["order"][str(o)] = dict(zip(("pc", "lo", "hi"), wilson(int(g.destroyed.sum()), len(g)))) | {"k": int(g.destroyed.sum()), "n": len(g)}
pil = S[S.kind == "pillar"]
for o, g in pil.groupby("order"):
    R["surv"]["pillar_order"][str(o)] = dict(zip(("pc", "lo", "hi"), wilson(int(g.destroyed.sum()), len(g)))) | {"k": int(g.destroyed.sum()), "n": len(g)}
rows = []
for rgn, g in S.groupby("region"):
    gp = g[g.kind == "pillar"]
    a = wilson(int(g.destroyed.sum()), len(g)); b = wilson(int(gp.destroyed.sum()), len(gp))
    R["surv"]["region"][rgn] = {"pc": a[0], "lo": a[1], "hi": a[2], "n": len(g), "pil_pc": b[0], "pil_lo": b[1], "pil_hi": b[2],
                                "pil_n": len(gp), "pil_k": int(gp.destroyed.sum())}
    rows.append({"region": rgn, "stations": len(g), "destroyed": int(g.destroyed.sum()), "pc": round(a[0], 1),
                 "pillars": len(gp), "pillars_destroyed": int(gp.destroyed.sum()), "pillar_pc": round(b[0], 1)})
pd.DataFrame(rows).to_csv(f"{DATA}/destroyed_by_region.csv", index=False)
R["surv"]["pillars_total"] = len(pil); R["surv"]["pillars_surviving"] = int((pil.destroyed == 0).sum())

# planned logit
M = S[S.dem.notna()].copy()
M["lowland"] = (M.dem < 100).astype(int)
M["decade"] = pd.cut(M.com_year, [1930, 1939, 1949, 1959, 2000], labels=["1930s", "1940s", "1950s", "1960 on"]).astype(str)
M["ordc"] = M["order"].map({1: "1", 2: "2", 3: "3", 4: "4", 0: "other"})
M = M.dropna(subset=["kind", "ordc", "region", "lowland", "sq10", "destroyed"])
M = M[M.decade.isin(["1930s", "1940s", "1950s", "1960 on"])].reset_index(drop=True)
f = "destroyed ~ C(kind, Treatment('pillar')) + C(ordc, Treatment('3')) + C(region, Treatment('South East')) + lowland + C(decade, Treatment('1950s'))"


def fit(df, formula=f):
    m = smf.logit(formula, data=df).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": pd.factorize(df.sq10)[0]})
    return m


m = fit(M)
tab = pd.DataFrame({"term": m.params.index, "coef": m.params.values, "se": m.bse.values, "or": np.exp(m.params.values),
                    "or_lo": np.exp(m.conf_int()[0].values), "or_hi": np.exp(m.conf_int()[1].values), "p": m.pvalues.values})
tab.to_csv(f"{DATA}/survival_model.csv", index=False)
print(tab.to_string())


def orr(term, mm=m):
    i = [t for t in mm.params.index if term in t][0]
    return {"or": float(np.exp(mm.params[i])), "lo": float(np.exp(mm.conf_int().loc[i, 0])), "hi": float(np.exp(mm.conf_int().loc[i, 1])), "p": float(mm.pvalues[i])}


R["surv"]["model"] = {"n": int(m.nobs), "clusters": int(M.sq10.nunique()), "pseudo_r2": float(m.prsquared),
                      "intersected": orr("[T.intersected]"), "surface": orr("[T.surface]"), "lowland": orr("lowland"),
                      "london": orr("[T.London]"), "scotland": orr("[T.Scotland]"), "order1": orr("ordc, Treatment('3'))[T.1]"),
                      "order2": orr("ordc, Treatment('3'))[T.2]")}
# robustness: pillars only; drop London; lowland threshold 50 m
mp = fit(M[M.kind == "pillar"], "destroyed ~ C(ordc, Treatment('3')) + C(region, Treatment('South East')) + lowland")
R["surv"]["rob_pillars_lowland"] = orr("lowland", mp)
mL = fit(M[M.region != "London"]); R["surv"]["rob_nolondon_intersected"] = orr("[T.intersected]", mL); R["surv"]["rob_nolondon_lowland"] = orr("lowland", mL)
M2 = M.assign(lowland=(M.dem < 50).astype(int)); m50 = fit(M2); R["surv"]["rob_low50"] = orr("lowland", m50)
print(R["surv"]["model"], R["surv"]["rob_pillars_lowland"], R["surv"]["rob_low50"])

# OSM cross-check
O = pd.read_csv(f"{DATA}/osm_points.csv")
P = S[S.kind == "pillar"].set_index("sid")
R["osm"] = {"points": len(O), "pillar_tagged": int((O.struct == "pillar").sum())}
for rad in (25, 50, 100):
    hit = set(O.loc[O.nearest_m <= rad, "nearest_sid"])
    for st, lab in ((0, "surv"), (1, "dest")):
        g = P[P.destroyed == st]
        kk = int(sum(s in hit for s in g.index))
        R["osm"][f"{lab}_{rad}"] = dict(zip(("pc", "lo", "hi"), wilson(kk, len(g)))) | {"k": kk, "n": len(g)}
near = O[(O.nearest_m <= 50) & O.ele.notna()]
near = near.assign(h=P.reindex(near.nearest_sid).height.values)
near = near[(near.h > 0)]
ele = pd.to_numeric(near.ele.astype(str).str.extract(r"([-\d.]+)")[0], errors="coerce")
R["osm"]["ele_n"] = int(ele.notna().sum()); R["osm"]["ele_mae"] = float((ele - near.h).abs().median())
print(R["osm"])
jsave(R, f"{SCR}/r04.json", indent=1)
