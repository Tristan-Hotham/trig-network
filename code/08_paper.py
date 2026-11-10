"""Step 8: the paper. Fills code/paper_template.tex from data/results.json and the data tables, compiles with xelatex.
Output: release/paper/Hotham_Trig_Network.pdf and .tex beside the f_*.pdf figures. The DOI stays a placeholder
(https://doi.org/10.5281/zenodo.24104644 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/08_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Trig_Network"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    for k in ("f0", "f1", "f2", "f3"):
        if f == k: return f"{float(v):.{k[1]}f}".replace("-", "$-$")
    return tex(str(v))


S = pd.read_csv(f"{DATA}/stations.csv")
rows = ""
for o, lab in ((1, "Primary (1)"), (2, "Secondary (2)"), (3, "Third order (3)"), (4, "Fourth order (4)"), (0, "Later codes")):
    g = S[S["order"] == o]
    c = g.kind.value_counts()
    rows += f"{lab} & {c.get('pillar', 0):,} & {c.get('surface', 0):,} & {c.get('intersected', 0):,} & {len(g):,} & {100 * g.destroyed.mean():.1f}\\\\\n"
c = S.kind.value_counts()
rows += f"\\midrule All & {c['pillar']:,} & {c['surface']:,} & {c['intersected']:,} & {len(S):,} & {100 * S.destroyed.mean():.1f}\\\\\n"
TST = ("\\begin{table}[tbp]\\centering\\small\\caption{Stations in the OS legacy list after grouping mark rows, by order and kind, with the share recorded destroyed.}\\label{tab:stations}"
       "\\begin{tabular}{lrrrrr}\\toprule Order & Pillars & Ground marks & Intersected & All & Destroyed (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

rows = ""
for k, lab in (("o1_all", "Primary, all kinds"), ("o1_pillar", "Primary pillars"), ("o2_all", "Secondary, all kinds"), ("o2_pillar", "Secondary pillars"),
               ("o3_all", "Third order, all kinds"), ("o3_pillar", "Third-order pillars"), ("o4_all", "Fourth order, all kinds")):
    g = R["geom"][k]
    rows += (f"{lab} & {g['n']:,} & {g['nnd_med']:.2f} [{g['nnd_lo']:.2f}, {g['nnd_hi']:.2f}] & {g['nnd_q25']:.2f} to {g['nnd_q75']:.2f} & {g['density_per_1000km2']:.1f} & "
             f"{g['ce_R']:.2f} & {g['ce_csr_lo']:.2f} to {g['ce_csr_hi']:.2f}\\\\\n")
TSP = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Nearest same-order neighbour distances (km; median with bootstrap 95\\% CI, interquartile range), density per 1,000 km$^2$ of land, and the Clark and Evans ratio with the 95\\% band of CSR simulations on the same land.}\\label{tab:spacing}"
       "\\setlength{\\tabcolsep}{2.5pt}\\begin{tabular}{lrlllrl}\\toprule Set & N & Median [95\\% CI] & IQR & Density & $R$ & CSR band\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")


def vrow(lab, v, extra=""):
    return f"{lab} & {v['k']:,} & {v['n']:,} & {v['pc']:.1f} [{v['lo']:.1f}, {v['hi']:.1f}]{extra}\\\\\n"


rows = vrow("Primary, nearest neighbour (main)", R["vis"]["o1"]) + vrow("Primary, Delaunay sides up to 80 km", R["vis"]["o1_delaunay"])
for k, lab in (("o1_delaunay_0_20", "\\quad sides under 20 km"), ("o1_delaunay_20_40", "\\quad sides 20 to 40 km"), ("o1_delaunay_40_80", "\\quad sides 40 to 80 km")):
    rows += vrow(lab, R["vis"][k])
rows += vrow("Secondary pillars, nearest neighbour", R["vis"]["o2"]) + vrow("Third-order pillars, nearest neighbour", R["vis"]["o3"])
rows += "\\midrule\\multicolumn{4}{l}{\\textit{Placebos (ground height plus 1.5 m at each end)}}\\\\\n"
rows += vrow("Primary lines, both ends moved 1 km", R["plc"]["shift1km"]) + vrow("Random land pairs, primary lengths", R["plc"]["random"])
rows += vrow("Random land pairs, secondary lengths", R["plc"]["random_o2"]) + vrow("Random land pairs, third-order lengths", R["plc"]["random_o3"])
TV = ("\\begin{table}[tbp]\\centering\\small\\caption{Lines clear over the terrain model (Wilson 95\\% CI). Main specification: surveyed heights plus 1.5 m, $k = 0.13$, 100 m step, 250 m end margin.}\\label{tab:vis}"
      "\\begin{tabular}{lrrl}\\toprule Set & Clear & Lines & \\% clear [95\\% CI]\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

KN = {"pillar": "P", "surface": "G", "intersected": "I"}
rows = "".join(f"{tex(f['a'])} & {tex(f['b'])} & {KN[f['ka']]}, {KN[f['kb']]} & {f['km']:.1f} & {f['clear']:.1f} & {'yes' if f['tower'] else ''}\\\\\n".replace("-", "$-$")
               for f in sorted(R["fail"]["list"], key=lambda x: x["clear"]))
TF = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Every failing nearest-neighbour primary line: kinds of station (P pillar, G ground mark, I intersected or roof station), length (km), clearance (m; negative = blocked) and whether an end is a listed steel-tower station.}\\label{tab:fail}"
      "\\begin{tabular}{lllrrl}\\toprule From & To & Kinds & km & Clearance & Tower\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

L = pd.read_csv(f"{DATA}/survival_model.csv")
def tl(t):
    t = re.sub(r"C\((\w+), Treatment\('([^']+)'\)\)\[T\.([^\]]+)\]", lambda m: f"{m.group(1)}: {m.group(3)} (vs {m.group(2)})", t)
    return tex(t.replace("kind", "Kind").replace("ordc", "Order").replace("region", "Region").replace("decade", "Decade").replace("lowland", "Lowland (below 100 m)"))
rows = "".join(f"{tl(r.term)} & {r.coef:.3f} & ({r.se:.3f}) & {r['or']:.2f} [{r.or_lo:.2f}, {r.or_hi:.2f}] & {r.p:.3f}\\\\\n".replace("-0.", "$-$0.").replace("-1.", "$-$1.").replace("-2.", "$-$2.")
               for _, r in L.iterrows())
m = R["surv"]["model"]
TL = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Planned logit of the destroyed flag, all stations with a terrain value and a commissioning decade. Standard errors clustered by 10 km grid square. "
      f"N = {m['n']:,}; clusters = {m['clusters']:,}; pseudo-$R^2$ = {m['pseudo_r2']:.3f}.}}\\label{{tab:logit}}"
      "\\begin{tabular}{p{7.2cm}rrlr}\\toprule Term & Coef. & (SE) & OR [95\\% CI] & $p$\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

G = pd.read_csv(f"{DATA}/destroyed_by_region.csv").sort_values("pillar_pc")
rows = "".join(f"{tex(r.region)} & {r.stations:,} & {r.pc:.1f} & {r.pillars:,} & {r.pillars_destroyed:,} & {r.pillar_pc:.1f}\\\\\n" for r in G.itertuples())
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Stations and pillars recorded destroyed by region.}\\label{tab:region}"
      "\\begin{tabular}{lrrrrr}\\toprule Region & Stations & Destroyed (\\%) & Pillars & Destroyed & (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

rb = [("Main ($k = 0.13$, 1.5 m, 250 m margin, 100 m step)", R["vis"]["o1"]), ("$k = 0$", R["rob"]["k0"]), ("$k = 0.075$", R["rob"]["k075"]), ("$k = 0.20$", R["rob"]["k20"]),
      ("No end margin", R["rob"]["margin0"]), ("500 m end margin", R["rob"]["margin500"]), ("Instrument height 0 m", R["rob"]["instr0"]),
      ("Signal height 5 m", R["rob"]["instr5"]), ("50 m profile step", R["rob"]["step50"]), ("Two nearest neighbours", R["rob"]["nn2"]),
      ("Pillar to pillar only", R["rob"]["pillars_only"]), ("Any intersected station", R["rob"]["intersected_any"]), ("Terrain-model heights at the ends", R["rob"]["demonly"])]
rows = "".join(vrow(a, b) for a, b in rb)
rows += "\\midrule\\multicolumn{4}{l}{\\textit{Leave one region out (\\% clear)}}\\\\\n" + "".join(f"\\quad without {tex(k)} & & & {v:.1f}\\\\\n" for k, v in R["rob"]["loro"].items())
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Planned robustness checks for nearest-neighbour primary lines (Wilson 95\\% CI).}\\label{tab:robust}"
      "\\begin{tabular}{lrrl}\\toprule Check & Clear & Lines & \\% clear [95\\% CI]\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_STATIONS", TST), ("TABLE_SPACING", TSP), ("TABLE_VIS", TV), ("TABLE_FAIL", TF), ("TABLE_LOGIT", TL), ("TABLE_REGION", TG), ("TABLE_ROBUST", TR)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24104644", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("DSIT", "DCMS", "pre-registered", "preregistered", "civil serv"):
    assert bad not in t, bad
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = txt.split("Abstract")[1].split("Keywords")[0]
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013"))
