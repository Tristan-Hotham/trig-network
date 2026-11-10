"""Step 9: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24104644, https://doi.org/10.5281/zenodo.24104644 and https://blog.tristanhotham.com/2026/10/31/trig-network/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Trig_Network"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "The trig pillar network: how Britain was measured",
        "slug": "trig-network",
        "excerpt": f"I mapped all {R['counts']['kinds']['pillar']:,} Ordnance Survey trig pillars and tested the rule they were built to: every station must see its neighbours. Using the surveyed station heights over a modern terrain model, {R['vis']['o1']['pc']:.0f}% of neighbouring primary stations still can; random lines of the same length, {R['plc']['random']['pc']:.0f}%.",
        "seo_description": f"Britain's {R['counts']['kinds']['pillar']:,} trig pillars mapped: how far apart, when built, what survives, and can neighbours still see each other?",
        "tags": ["maps", "data visualisation", "Ordnance Survey", "trig points", "surveying", "history of science", "landscape", "terrain"],
        "header_alt": "Title card on cream paper reading 'The trig pillar network' beside a map of Great Britain's primary triangulation stations joined by blue lines of sight, with a few red blocked lines in eastern England."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("stations.csv", "nn_pairs.csv", "pairs.csv", "primary_triangles.csv", "commissioning_by_year.csv", "destroyed_by_region.csv",
               "survival_model.csv", "osm_points.csv", "results.json"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "The Trig Pillar Network: Geometry, Construction, Survival and Intervisibility of the Ordnance Survey Retriangulation of Great Britain",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/trig-network/}}.</p><p>Sources: Ordnance Survey legacy triangulation station list (contains OS data, Crown copyright and database right 2018, used under the Open Government Licence v3.0, via the trigpoints R package); Terrain Tiles (AWS Open Data; Mapzen: SRTM and GMTED2010 courtesy of the USGS, EU-DEM produced using Copernicus data, ETOPO1 NOAA); OpenStreetMap contributors (ODbL); ONS boundaries (OGL v3.0). Text, figures and derived data CC BY 4.0, except that OS station fields remain under the Open Government Licence v3.0 and the OSM-derived file osm_points.csv is ODbL; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["triangulation", "Ordnance Survey", "trig pillars", "Retriangulation of Great Britain", "intervisibility", "viewshed", "digital elevation model", "history of surveying"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
