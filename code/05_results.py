"""Step 5: data/results.json (every number quoted anywhere), plus the exploratory checks added after the planned analysis:
steel observing towers at the 22 primary stations listed in code/steel_towers.csv, and DEM-only comparisons."""
import pandas as pd
from common import *

R = {}
for f in ("r01", "r02", "r03", "r04"):
    R.update(jload(f"{SCR}/{f}.json"))
S = pd.read_csv(f"{DATA}/stations.csv").set_index("sid")
P = pd.read_csv(f"{DATA}/pairs.csv")
T = pd.read_csv(os.path.join(ROOT, "code", "steel_towers.csv"))
tow = set(S[(S["order"] == 1) & S["name"].str.lower().isin(T.name.str.lower())].index)
assert len(tow) == len(T) == 22

P1 = P[(P.order == 1) & (P.set == "nn1")].copy()
P1["tower"] = P1.sid_a.isin(tow) | P1.sid_b.isin(tow)
fail = P1[P1.visible == 0]
rows = []
for r in fail.itertuples():
    a, b = S.loc[r.sid_a], S.loc[r.sid_b]
    rows.append({"a": a["name"], "b": b["name"], "ka": a.kind, "kb": b.kind, "km": r.dist_km, "clear": r.clear_m,
                 "tower": bool(r.tower), "ha": float(a.height), "hb": float(b.height)})
F = pd.DataFrame(rows)
# exploratory: rerun failing pairs that touch a tower station with the tower (30 m, about 100 ft) at that end
tw = []
for r in fail[fail.tower].itertuples():
    a, b = S.loc[r.sid_a], S.loc[r.sid_b]
    ha = (a.height if a.height > 0 else a.dem) + (30.0 if r.sid_a in tow else INSTR)
    hb = (b.height if b.height > 0 else b.dem) + (30.0 if r.sid_b in tow else INSTR)
    c, _, _ = los(a.easting, a.northing, ha, b.easting, b.northing, hb)
    tw.append(c)
R["fail"] = {"n": len(F), "list": rows, "structure_no_height": int(((F.ka != "pillar") & (F.ha <= 0) | (F.kb != "pillar") & (F.hb <= 0)).sum()),
             "pillar_pillar": int(((F.ka == "pillar") & (F.kb == "pillar")).sum()), "tower_pairs": int(F.tower.sum()),
             "tower_pairs_clear_with_30m": int(sum(c >= 0 for c in tw)),
             "lowland_small_neg": int(((F.ka == "pillar") & (F.kb == "pillar") & (F.clear > -5)).sum())}
import re as _re
_struct = _re.compile(r"L Ho|Minster|Observatory|Castle|Wtr Twr", _re.I)
_named = F.a.str.contains(_struct) | F.b.str.contains(_struct)
R["fail"]["structure_named"] = int(_named.sum())
R["fail"]["unexplained"] = [f"{r.a} to {r.b}" for r in F[~_named & ~F.tower].itertuples()]
R["fail"]["unexplained_n"] = len(R["fail"]["unexplained"])
assert R["fail"]["structure_named"] + R["fail"]["tower_pairs"] + R["fail"]["unexplained_n"] == R["fail"]["n"]
R["towers"] = {"n": len(tow), "pairs_touching": int(P1.tower.sum()), "vis_touching": int(P1[P1.tower].visible.sum())}
pp = R["rob"]["pillars_only"]
R["headline"] = {"primary_pc": R["vis"]["o1"]["pc"], "primary_k": R["vis"]["o1"]["k"], "primary_n": R["vis"]["o1"]["n"],
                 "random_pc": R["plc"]["random"]["pc"], "shift_pc": R["plc"]["shift1km"]["pc"],
                 "pillars": R["build"]["pillars_n"], "pillars_destroyed": R["surv"]["pillar_order"]["1"]["k"] * 0 + int(S[S.kind == "pillar"].destroyed.sum()),
                 "pillars_surviving_pc": 100 * R["surv"]["pillars_surviving"] / R["surv"]["pillars_total"],
                 "pillar_pairs_pc": pp["pc"]}
R["headline"]["pillars_destroyed_pc"] = 100 * R["headline"]["pillars_destroyed"] / R["headline"]["pillars"]
# DEM-only exploratory comparison: primaries with DEM endpoints vs DEM-endpoint placebos
R["explor"] = {"demonly_minus_shift_pp": R["rob"]["demonly"]["pc"] - R["plc"]["shift1km"]["pc"],
               "demonly_minus_random_pp": R["rob"]["demonly"]["pc"] - R["plc"]["random"]["pc"]}
# counts used in copy
R["counts"] = {"stations": len(S), "orders": {str(o): int((S["order"] == o).sum()) for o in (1, 2, 3, 4)},
               "kinds": {k: int((S.kind == k).sum()) for k in ("pillar", "surface", "intersected")},
               "pillar_orders": {str(o): int(((S.kind == "pillar") & (S["order"] == o)).sum()) for o in (1, 2, 3, 4)},
               "pillar_dem_n": R["dem"]["n"], "highest_pillar": S[S.kind == "pillar"].height.idxmax()}
hp = S.loc[R["counts"]["highest_pillar"]]
R["counts"]["highest_pillar"] = {"name": hp["name"], "height": float(hp.height)}
lowp = S[(S.kind == "pillar") & (S.height > 0)]
lp = lowp.loc[lowp.height.idxmin()]
R["counts"]["lowest_pillar"] = {"name": lp["name"], "height": float(lp.height)}
R["counts"]["pillar_height_med"] = float(S[(S.kind == "pillar") & (S.height > 0)].height.median())
for o in (1, 2, 3):
    R["counts"][f"pillar_height_med_o{o}"] = float(S[(S.kind == "pillar") & (S.height > 0) & (S["order"] == o)].height.median())
bn = S[(S["name"] == "Ben Nevis") & (S.kind == "pillar")].iloc[0]
R["dem"]["ben_nevis_gap"] = float(bn.height - bn.dem); R["dem"]["ben_nevis_dem"] = float(bn.dem)
R["counts"]["first_pillar_year"] = R["build"]["pillars_first"]
vals = [R["rob"][k]["pc"] for k in ("k0", "k075", "k20", "step50", "nn2", "margin0", "margin500")] + [R["rob"]["loro_min"], R["rob"]["loro_max"], R["vis"]["o1"]["pc"]]
R["rob"]["range_lo"] = min(vals); R["rob"]["range_hi"] = max(vals)
# checks on statements made in the copy
pp_ = F[(F.ka == "pillar") & (F.kb == "pillar")]
assert pp_.tower.all() and len(pp_) == R["fail"]["tower_pairs"]
assert min(R["surv"]["region"], key=lambda k: R["surv"]["region"][k]["pil_pc"]) == "Scotland"
assert R["build"]["pillars_first"] == 1936
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("fail", "towers", "headline", "explor", "counts")}, indent=1)[:4000])
