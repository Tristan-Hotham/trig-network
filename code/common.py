"""Shared paths, constants and helpers for the trig-network study ("The trig pillar network: how Britain was measured").

Inputs (read in place, never modified or moved):
  RAW/os_trig_stations.csv   Ordnance Survey legacy triangulation station list, as packaged in the trigpoints R package
                             (Phil Mike Jones, MIT licence; "Contains OS data (c) Crown copyright and database right 2018").
                             One row per mark: name, station code, order (1 to 4; 12, 13, 14, 30, 40 later codes), type,
                             commissioning date (com_date, days since 1970-01-01), maintenance and levelling dates,
                             destroyed flag, notes, easting/northing (approximately OSGB36 National Grid).
  RAW/os_trig_stations_README.md  the package README (licence, station types).
  RAW/osm_trig.tsv           OpenStreetMap survey points (man_made=survey_point) in the UK via QLever osm-planet, retrieved
                             2026 (ODbL, OpenStreetMap contributors): OSM id, name, ref, structure, condition, ele, WKT.
  RAW/terrarium_z9_pack0..5  Terrain Tiles (AWS Open Data; Mapzen), Terrarium PNG encoding, zoom 9, Britain and Ireland;
                             .json lists [file, byte offset, length] into the matching .bin. SHARED with the sea-view
                             study: opened read-only.
  GEO/uk_topo.json           ONS boundaries (OGL v3): regions of England, Scotland and Wales (layer rgn).
"""
import json, gzip, os, re, math, io
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("TN_RAW", "/home/claude/newdata/raw_new13")
GEO = os.environ.get("TN_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("TN_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("TN_SCRATCH", "/home/claude/scratch/trig-network")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "trig-network"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"

# planned constants (NOTES.md analysis plan)
R_EARTH = 6371000.0
K_MAIN = 0.13           # refraction coefficient
INSTR = 1.5             # instrument / signal height above the mark, metres
MARGIN = 250.0          # profile samples this close to either end are ignored, metres
STEP = 100.0            # profile sampling step, metres
SEED = 20261110
Z = 9
TILE = 256

SURFACE = {"BOLT", "RIVET", "BLOCK", "BURIED BLK", "CENTRE", "DISC", "CUT", "HOLE", "PEG", "PLATE", "PUNCH MARK", "MARK",
           "SPIDER", "FENOMARK", "CURRY ST'L", "PIPE", "POST", "STONE", "CAIRN", "OLD TRIG"}
INTERSECTED = {"SPIRE", "FLAGSTAFF", "VANE", "CHIMNEY", "MAST", "LIGHTHOUSE", "CUPOLA", "DOME", "BELFRY", "TOWER",
               "PINNACLE", "BEACON", "CROSS", "APEX", "AERIAL", "L'NING C", "MONUMENT", "OBELISK", "MEMORIAL", "TURRET",
               "VENT", "LAMP", "POLE", "PYLON", "WIRE", "HYDROG", "TOPOGRAPH"}


def kind_of(t):
    t = str(t).strip().upper()
    if t == "PILLAR": return "pillar"
    if t in SURFACE: return "surface"
    if t in INTERSECTED: return "intersected"
    return "surface"


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    raise ValueError(f)


def wilson(k, n, z=1.96):
    if n == 0: return (None, None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * p, 100 * (c - h), 100 * (c + h))


# ---------- terrain (Terrarium z9) ----------
_DEM = None


def load_dem():
    """Mosaic of every Terrarium z9 tile in the six packs, float32 metres, plus the global pixel offset. Read-only."""
    global _DEM
    if _DEM is not None:
        return _DEM
    from PIL import Image
    idx = []
    for i in range(6):
        for fn, off, ln in jload(f"{RAW}/terrarium_z9_pack{i}.json"):
            _, x, y = fn[:-4].split("_")
            idx.append((i, int(x), int(y), off, ln))
    xs = [r[1] for r in idx]; ys = [r[2] for r in idx]
    x0, y0 = min(xs), min(ys)
    W = (max(xs) - x0 + 1) * TILE; H = (max(ys) - y0 + 1) * TILE
    A = np.full((H, W), np.nan, dtype=np.float32)
    for i in range(6):
        with open(f"{RAW}/terrarium_z9_pack{i}.bin", "rb") as f:
            buf = f.read()
        for (j, x, y, off, ln) in idx:
            if j != i: continue
            im = np.asarray(Image.open(io.BytesIO(buf[off:off + ln])).convert("RGB"), dtype=np.float32)
            h = im[..., 0] * 256 + im[..., 1] + im[..., 2] / 256 - 32768
            A[(y - y0) * TILE:(y - y0 + 1) * TILE, (x - x0) * TILE:(x - x0 + 1) * TILE] = h
        del buf
    _DEM = (A, x0 * TILE, y0 * TILE)
    return _DEM


def lonlat_to_px(lon, lat):
    n = TILE * 2 ** Z
    lon = np.asarray(lon, dtype=float); lat = np.asarray(lat, dtype=float)
    X = (lon + 180.0) / 360.0 * n
    s = np.sin(np.radians(lat))
    Y = (0.5 - np.log((1 + s) / (1 - s)) / (4 * np.pi)) * n
    return X, Y


def elev(lon, lat):
    """Bilinear DEM height (m) at lon/lat (arrays). NaN outside the mosaic."""
    A, ox, oy = load_dem()
    X, Y = lonlat_to_px(lon, lat)
    x = X - ox - 0.5; y = Y - oy - 0.5
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = x - x0; fy = y - y0
    H, W = A.shape
    ok = (x0 >= 0) & (y0 >= 0) & (x0 < W - 1) & (y0 < H - 1)
    x0c = np.clip(x0, 0, W - 2); y0c = np.clip(y0, 0, H - 2)
    v = (A[y0c, x0c] * (1 - fx) * (1 - fy) + A[y0c, x0c + 1] * fx * (1 - fy) +
         A[y0c + 1, x0c] * (1 - fx) * fy + A[y0c + 1, x0c + 1] * fx * fy)
    return np.where(ok, v, np.nan)


_TF = None


def bng_to_ll(e, n):
    global _TF
    from pyproj import Transformer
    if _TF is None:
        _TF = Transformer.from_crs(27700, 4326, always_xy=True)
    return _TF.transform(np.asarray(e, float), np.asarray(n, float))


_TB = None


def ll_to_bng(lon, lat):
    global _TB
    from pyproj import Transformer
    if _TB is None:
        _TB = Transformer.from_crs(4326, 27700, always_xy=True)
    return _TB.transform(np.asarray(lon, float), np.asarray(lat, float))


def los(e1, n1, h1, e2, n2, h2, k=K_MAIN, step=STEP, margin=MARGIN):
    """Line of sight between two National Grid points with observer heights h1, h2 (m above datum).
    Profile sampled every `step` metres; curvature and refraction drop d1*d2*(1-k)/(2R) applied to the terrain.
    Returns (min clearance in m over samples outside `margin` of either end, distance m, position of the worst sample)."""
    D = math.hypot(e2 - e1, n2 - n1)
    m = max(int(D // step), 2)
    t = np.linspace(0, 1, m + 1)
    d1 = t * D
    keep = (d1 >= margin) & (d1 <= D - margin)
    if keep.sum() == 0:
        return (float("inf"), D, None)
    t = t[keep]; d1 = d1[keep]
    E = e1 + t * (e2 - e1); N = n1 + t * (n2 - n1)
    lon, lat = bng_to_ll(E, N)
    z = elev(lon, lat)
    z = np.where(np.isnan(z), 0.0, np.maximum(z, 0.0))   # sea and missing: sea level
    drop = d1 * (D - d1) * (1 - k) / (2 * R_EARTH)
    line = h1 + t * (h2 - h1)
    c = line - (z - drop)
    j = int(np.argmin(c))
    return (float(c[j]), D, float(d1[j]))
