"""Step 7: data/site.json (every station and every tested line, compact) and index.html from code/page_template.html and
code/page.css, filled from data/results.json, with the full-screen snippet. 10.5281/zenodo.24104644, https://doi.org/10.5281/zenodo.24104644 and https://blog.tristanhotham.com/2026/10/31/trig-network/ are left
for the publisher to fill."""
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
S = pd.read_csv(f"{DATA}/stations.csv")
P = pd.read_csv(f"{DATA}/pairs.csv")
KC = {"pillar": 0, "surface": 1, "intersected": 2}
S = S.sort_values(["order", "sid"], key=lambda c: c.replace(0, 9) if c.name == "order" else c).reset_index(drop=True)
idx = {s: i for i, s in enumerate(S.sid)}
st = []
for r in S.itertuples():
    st.append([round(r.lon, 5), round(r.lat, 5), int(r.order), KC[r.kind], int(r.destroyed),
               int(r.com_year) if r.com_year == r.com_year else None, round(r.height, 1) if r.height > 0 else None,
               r.name, r.station, r.types.replace("|", ", ").lower()])
ln = []
for r in P.itertuples():
    ln.append([idx[r.sid_a], idx[r.sid_b], int(r.order), int(r.visible), round(r.clear_m, 1), round(r.dist_km, 2), 0 if r.set == "nn1" else 1])
site = {"s": st, "l": ln}
jsave(site, f"{DATA}/site.json")
sj = json.dumps(site, ensure_ascii=False)
assert "—" not in sj and "–" not in sj
print("site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")

KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{CSS}}", open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
names = set(S.name)
for g in re.findall(r'data-go="([^"]+)"', t):
    assert g in names, g
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
