"""Step 1: OS mark records -> stations (data/stations.csv), with region, WGS84 position and DEM height; OSM survey points
matched to OS stations (data/osm_match.csv). See NOTES.md for the rules (written before any outcome was computed)."""
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree
from common import *

d = pd.read_csv(f"{RAW}/os_trig_stations.csv", dtype={"station": str, "new_name": str, "sec_com_blk": str})
d["name"] = d["name"].astype(str).str.strip()
d["type"] = d["type"].astype(str).str.strip().str.upper()
n_rows = len(d)
# exact duplicate rows
dup = d.duplicated(subset=["station", "type", "easting", "northing", "com_date", "destroyed"]).sum()
d = d.drop_duplicates(subset=["station", "type", "easting", "northing", "com_date", "destroyed"]).reset_index(drop=True)
d["kind"] = d["type"].map(kind_of)
d["ord"] = d["order"].where(d["order"].isin([1, 2, 3, 4]), 9)
day = pd.to_numeric(d["com_date"], errors="coerce")
d["cyear"] = (pd.Timestamp("1970-01-01") + pd.to_timedelta(day.where(day.between(-30000, 11000)), unit="D")).dt.year
d["dest"] = (d["destroyed"] > 0).astype(int)

# cluster records: same station code within 100 m
d = d.sort_values(["station", "easting"]).reset_index(drop=True)
sid = np.full(len(d), -1); nxt = 0
for code, g in d.groupby("station", sort=False):
    ix = g.index.values; xy = g[["easting", "northing"]].values
    lab = np.full(len(ix), -1)
    for a in range(len(ix)):
        if lab[a] >= 0: continue
        lab[a] = nxt; stack = [a]
        while stack:
            b = stack.pop()
            near = np.where((lab < 0) & (np.hypot(*(xy - xy[b]).T) <= 100))[0]
            for c in near:
                lab[c] = nxt; stack.append(c)
        nxt += 1
    sid[ix] = lab
d["sid"] = sid
print("records", n_rows, "exact duplicates", dup, "stations", nxt)

rows = []
for s, g in d.groupby("sid"):
    pil = g[g["type"] == "PILLAR"]
    lead = pil.iloc[0] if len(pil) else g.iloc[0]
    o = g["ord"].min()
    rows.append({
        "sid": int(s), "station": lead["station"], "name": lead["name"], "order": int(o) if o < 9 else 0,
        "type": lead["type"], "kind": "pillar" if len(pil) else lead["kind"], "n_marks": len(g),
        "types": "|".join(sorted(set(g["type"]))),
        "height": float(g["height"].max()), "com_year": float(g["cyear"].min()) if g["cyear"].notna().any() else np.nan,
        "block": lead["sec_com_blk"], "destroyed": int(g["dest"].min() == 1),
        "pillar_destroyed": int(pil["dest"].min() == 1) if len(pil) else np.nan,
        "notes": "; ".join(sorted(set(str(x) for x in g["notes"].dropna())))[:160],
        "easting": float(lead["easting"]), "northing": float(lead["northing"]),
    })
S = pd.DataFrame(rows)
lon, lat = bng_to_ll(S.easting, S.northing)
S["lon"] = np.round(lon, 6); S["lat"] = np.round(lat, 6)
S["dem"] = np.round(elev(S.lon.values, S.lat.values), 1)

rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True)
rg = rg[rg.areanm != "Northern Ireland"].to_crs(27700)
pts = gpd.GeoDataFrame(S[["sid"]], geometry=gpd.points_from_xy(S.easting, S.northing), crs=27700)
j = gpd.sjoin(pts, rg[["areanm", "geometry"]], how="left", predicate="within").drop_duplicates("sid")
S["region"] = j.set_index("sid").loc[S.sid, "areanm"].values
S["on_land"] = S["region"].notna().astype(int)
miss = S["region"].isna()
if miss.any():
    nn = gpd.sjoin_nearest(pts[miss.values], rg[["areanm", "geometry"]], how="left").drop_duplicates("sid")
    S.loc[miss, "region"] = nn.set_index("sid").loc[S.loc[miss, "sid"], "areanm"].values
S["sq10"] = (S.easting // 10000).astype(int).astype(str) + "_" + (S.northing // 10000).astype(int).astype(str)
S.to_csv(f"{DATA}/stations.csv", index=False)

# OSM survey points
o = pd.read_csv(f"{RAW}/osm_trig.tsv", sep="\t", dtype=str)
o.columns = [c.lstrip("?") for c in o.columns]
for c in o.columns:
    o[c] = o[c].fillna("").str.replace(r'^"|"(@\w+|\^\^.*)?$', "", regex=True)
o["id"] = o["x"].str.extract(r"openstreetmap.org/(\w+/\d+)")
xy = o["wkt"].str.extract(r"\(+([-\d.]+) ([-\d.]+)")
o["lon"] = xy[0].astype(float); o["lat"] = xy[1].astype(float)
oe, on = ll_to_bng(o.lon, o.lat)
o["easting"] = oe; o["northing"] = on
o["struct"] = o["struct"].str.lower()
tree = cKDTree(np.c_[S.easting, S.northing])
dd, ii = tree.query(np.c_[o.easting, o.northing])
o["nearest_sid"] = S.sid.values[ii]; o["nearest_m"] = np.round(dd, 1)
o[["id", "name", "ref", "struct", "cond", "ele", "lon", "lat", "nearest_sid", "nearest_m"]].to_csv(f"{DATA}/osm_points.csv", index=False)

R = {"data": {"records": n_rows, "exact_dupes": int(dup), "stations": len(S), "records_per_station_max": int(d.groupby("sid").size().max()),
              "osm_points": len(o), "osm_pillars": int((o.struct == "pillar").sum()),
              "off_mosaic": int(S.dem.isna().sum()), "not_on_land_poly": int((S.on_land == 0).sum())}}
jsave(R, f"{SCR}/r01.json", indent=1)
print(R)
print(S.groupby(["order", "kind"]).size().unstack(fill_value=0))
print(S[S.dem.isna()][["name", "order", "lon", "lat"]].to_string())
