# trig-network: working notes

Brief: /home/claude/work/new13/BRIEFS.md section K (+ shared rules: new12, new11, new10, new9, new8 tops; house brief
/home/claude/newdata/BRIEF.md; GIF brief /home/claude/gifs/BRIEF.md). Format refs: fame-half-life, byelection-attention.
Scratch: /home/claude/scratch/trig-network (delete by exact path at the end). Terrain tiles in raw_new13 are shared with
the sea-view builder: read only, never moved or modified.

## What I looked at before writing the plan (descriptive only, no outcome computed)

- os_trig_stations.csv: 31,521 rows, 24,387 station codes. Rows are marks, not stations: one station can have a pillar,
  a bolt, a centre mark and a refixed mark (e.g. Forres Twr has 6 rows). Some codes are placeholders reused across the
  country (GPSF/D1 for 1990s GPS stations, "/PP53" style). Order 1 to 4, plus 12, 13, 14, 30, 40 (234 rows, codes for later
  control; treated as "other"). com_date is days since 1970: 1936 to 1995, one 2052 typo. Many primary stations carry the
  block date of their figure (FIG1 to FIG6), so com_date is a block commissioning date, not a per-pillar date.
  destroyed: 0 / 1 (plus 2 and 3 for 21 rows). Heights 0 for most non-pillar marks.
- Terrain: Terrarium tiles z9, x 244 to 258, y 145 to 174 (about 190 m pixels at 52 N). West edge -8.44 E: St Kilda lies
  outside (check, report).

## Analysis plan (written 2026 before computing any intervisibility, spacing statistic or survival rate)

Question: how was the Retriangulation network laid out, when was it built, how much survives, and does a modern open
terrain model reproduce the design rule that neighbouring stations of the same order can see each other?

### Units and data construction (01_data.py)
- Station = a station code plus a location cluster (records with the same code within 100 m; placeholder codes such as
  GPSF/D1 become separate stations by location). Each station gets: order = the lowest order 1 to 4 among its records
  (others -> "other"); kind = PILLAR if any record is a pillar, else the type of its first record grouped into families:
  pillar; surface or buried mark (BOLT, RIVET, BLOCK, BURIED BLK, CENTRE, DISC, CUT, HOLE, PEG, PLATE, PUNCH MARK, MARK,
  SPIDER, FENOMARK, CURRY ST'L, PIPE, POST, STONE, CAIRN, OLD TRIG); intersected or roof (SPIRE, FLAGSTAFF, VANE,
  CHIMNEY, MAST, LIGHTHOUSE, CUPOLA, DOME, BELFRY, TOWER, PINNACLE, BEACON, CROSS, APEX, AERIAL, L'NING C, MONUMENT,
  OBELISK, MEMORIAL, TURRET, VENT, LAMP, POLE, PYLON, WIRE, HYDROG, TOPOGRAPH); destroyed = every record flagged
  destroyed (>0); survives = at least one record not destroyed; height = max recorded height; com_year = year of the
  earliest com_date among its records (dates after 2000 set missing); position = the pillar record if any, else the first.
- Region: ONS region (England) or nation (Scotland, Wales) by point in polygon (uk_topo.json rgn/ctry). Stations off the
  land polygons are assigned the nearest region.
- Pillar subset = stations with a PILLAR record ("trig pillars").

### Q1 Geometry (H1, H2)
- Nearest-neighbour distance (NND) to the nearest station of the same order, for orders 1 to 3 (all kinds), and for
  pillars of each order. Median and quartiles, bootstrap 95% CI (2,000 resamples of stations).
- H1 hierarchy: median same-order NND falls with order (1 > 2 > 3). Counts against: overlapping CIs between orders 1 and 2.
- H2 regularity: Clark and Evans (1954) ratio R = mean NND / (0.5 / sqrt(density)), density = n / GB land area, with a
  Monte Carlo reference: 199 simulations of complete spatial randomness on the GB land mask (same n) give the null
  distribution of R (this handles the coast edge effect). Expect R > 1 (more regular than random) for primaries.
  Counts against: R inside the central 95% of the CSR simulations.
- Triangles: Delaunay triangulation of primary (order 1) stations; keep triangles whose three sides are each <= 80 km
  and whose centroid is on land or within 10 km of land. Report the smallest angle distribution (median, share with all
  angles >= 30 degrees, a usual "well-conditioned" rule) and compare with Delaunay triangles of CSR points (same rule).
  Expect better-shaped triangles than random. Counts against: share within the CSR 95% band.

### Q2 When it was built (H4, descriptive)
- Commissioning year histogram by order and kind. H4: most pillars (>= 75%) have a commissioning year from 1936 to 1962,
  the Retriangulation years. Report share with Wilson 95% CI. Primary figure blocks FIG1 to FIG6 by year (map of the spread
  from south to north). Descriptive; no test beyond the share.

### Q3 Survival (H5)
- Destroyed share by kind, order and region, Wilson 95% CIs. Main model: logit(destroyed) ~ kind + order + region +
  lowland (DEM height < 100 m) + decade of commissioning, SEs clustered by 10 km grid square (sec_com_blk or the
  square derived from the coordinates). Report odds ratios with 95% CI, N.
- H5: pillars are less often recorded destroyed than intersected stations and surface marks; lowland stations more often
  than upland. Counts against: OR CIs including 1.
- Caveat set in advance: the OS list is no longer maintained, so "not destroyed" means "not recorded destroyed by the
  time the list was frozen".
- Check against OSM (osm_trig.tsv): share of OS surviving pillars with an OSM survey point within 50 m; share of OS
  destroyed pillars with one (should be lower). Robustness: 25 m and 100 m radii.

### Q4 Intervisibility (H3, the main test)
- Pairs: for each station of order o (1, 2, 3; pillars only for 2 and 3, all kinds for 1), the line to its nearest
  same-order neighbour; unique undirected pairs. Also (secondary) Delaunay edges of primaries <= 80 km.
- Terrain: Terrarium z9 elevations (bilinear), profile sampled every 100 m in Web Mercator corrected to ground distance.
- Endpoint heights: recorded station height when > 0 (OS height of the mark), else the DEM; plus 1.5 m instrument/signal
  height at both ends (pillar top is about 1.2 m; a theodolite or beacon a little higher). Intersected stations (spires,
  masts) use recorded height or DEM + 1.5 m: a known underestimate; reported separately.
- Earth curvature and refraction: drop of the terrain relative to the chord d1 d2 (1 - k) / (2 R), R = 6,371 km,
  k = 0.13 (main). Intervisible = no profile sample (excluding the first and last 250 m, inside one DEM pixel of the
  station) rises above the sight line. Clearance reported in metres.
- H3: the share of nearest-neighbour primary pairs intervisible is high (>= 80%). Counts against: lower bound of the
  Wilson 95% CI below 80%.
- Placebos (planned): (a) same pairs with both ends moved 1 km in random directions onto land, ground + 1.5 m (does exact
  siting matter?); (b) random land pairs with the same distances (and random bearings) anywhere in GB. Expect primary
  share >> both. Effect = difference in share with bootstrap 95% CI.
- Robustness (planned): k = 0, 0.075 (geodetic standard), 0.20; endpoint margin 0 m and 500 m; instrument height 0 m and
  5 m (signal tower); profile step 50 m; DEM-only endpoint heights; leave-one-region-out share; nearest 2 neighbours
  instead of 1.
- Validation: DEM elevation at each pillar vs recorded height (bias, median absolute error, by order); which pairs
  fail and why (inspect every failing primary pair by eye in a profile figure; record reasons in NOTES).
- Exploratory (labelled so): intervisibility for order 2 and 3 pillars; share by distance band.

## Data construction log
- 01_data.py: 31,521 mark records -> 2 exact duplicates dropped -> 24,433 stations (code + 100 m cluster; up to 11
  records per station). Kinds: pillar 6,573 (order 1: 290, 2: 2,130, 3: 3,972, 4: 180, other 1); surface marks; intersected
  or roof stations. 11 stations (St Kilda group incl. the primary St Kilda) lie west of the terrain mosaic: no DEM,
  kept in geometry and survival tables, excluded from the lowland covariate. 463 stations fall outside the ONS land
  polygons (coastal rocks, lighthouses, piers): nearest region assigned.
- OSM: 2,909 survey points (299 tagged structure=pillar; most untagged). Polygon geometries (3, Irish baseline towers)
  take their first vertex.

## Results log (after the plan; planned items first)

- 02_geometry.py: H1 supported: median same-order NND 19.6 km (order 1, all kinds), 6.6 (order 2), 2.1 (order 3).
  H2 supported: Clark-Evans R 1.54 for primaries vs CSR simulations 1.02 to 1.17. Primary Delaunay triangles (582, sides
  <= 80 km): 71% with all angles >= 30 degrees vs 48% for CSR (44 to 52). H4: 99.0% of pillars dated 1936 to 1962.
  Note: order 4 (all kinds) is clustered (R 0.57): fourth-order marks are town and village infill, a planned set but
  not a design test.
- 03_visibility.py: H3 supported: 228 of 240 nearest-neighbour primary pairs intervisible (95.0%, Wilson 91.5 to 97.1).
  Placebos 16.6% (1 km shift) and 10.9% (random land pairs). Curvature/refraction choices barely matter at ~20 km
  (k 0 to 0.20: 94.6 to 95.0%). Instrument height 0 m: 90.4%. DEM-only endpoint heights: 67.1% (see DEM bias below).
- DEM check (not in the plan as a sub-analysis but planned as validation): z9 Terrarium is smoothed: median DEM minus
  surveyed pillar height -21.7 m, growing with height (about -6 m below 50 m, -106 m above 800 m; Ben Nevis 1,179 m in
  the DEM vs 1,345 m). No positional offset (shifting points 100 m in any direction makes it worse). So the main
  specification's use of surveyed heights at the ends matters; the intervening terrain is also smoothed, which favours
  visibility; placebos use DEM ends and so are disadvantaged. Added check (exploratory, after seeing this): compare
  DEM-only primaries (67%) with the DEM-only placebos (17%, 11%): the gap stays large.
- Failing primary pairs, all 12 read by eye: 2 Lundy lighthouse pairs (lighthouse heights not recorded: the DEM at the
  lighthouse + 1.5 m misses the tower); Lincoln Minster, Greenwich Observatory, water towers and castles (structures
  with no recorded height, so the tower itself is missing); 4 low pillar pairs in flat East Anglia/Lincolnshire with
  clearance between -0.6 and -3.1 m (within DEM error; such lines were observed from towers in flat country, to be
  verified in the literature before saying so); West Hills to Buddon (Buddon is a surface mark at 0 m recorded height
  on the Tay coast, line blocked 33 m by the Sidlaw foothills in the DEM). Pillar-to-pillar pairs: 176 of 179 (98.3%).
- 04_survival.py: 415 of 6,573 pillars recorded destroyed (6.3%). Logit (N 24,421, 2,706 clusters): intersected
  OR 3.25 (2.81 to 3.77), surface marks 5.52 (4.82 to 6.33) vs pillars; lowland 1.47 (1.33 to 1.62). H5 supported.
  OSM: 29.1% of surviving pillars have an OSM survey point within 50 m vs 2.9% of destroyed ones.
- Exploratory (added after the planned analysis, labelled so in the paper): steel-tower check (code/steel_towers.csv from
  the TrigpointingUK wiki "Bilby towers" list; all 22 names match a primary). The 3 pillar-to-pillar failures each touch a
  tower station (Crown Corner, Dexthorpe, Crimplesham/Walpole St Peters) and all clear with a 30 m tower. DEM-only
  primaries vs DEM-end placebos: +50 and +56 points.
- Survival robustness: lowland effect holds among pillars only (OR 2.04), at 50 m, and without London.

## References: how each was verified (2026)
- Web pages read: Ordnance Survey blog "History of the trig pillar" (2016); Greaves 2004 OSTN02 (OS-hosted PDF of the
  Survey Review paper: 7 blocks, 1936 to 1953, 11 fixed stations, grid ~20 m too long; its reference list supplied
  Ashkenazi et al. 1972 and 1983, Clarke 1858, OS 1967); Whitmore 1994 thesis (Nottingham eprints: OSGB70, OS(SN)80);
  TrigpointingUK wiki "Pillar" (6,977 pillars, 559 destroyed, June 2025) and "Bilby towers" (22 stations, 1938 to 1939);
  Tilezen joerd docs (sources by zoom: z9 = SRTM/EU-DEM, GMTED above 60 N, ETOPO1 sea); Hirt et al. 2010 (ADS abstract).
- Metadata pages (scilit, USGS, publisher, catalogue): Clark and Evans 1954; Ripley 1977 (pages 172 to 192); Fisher 1991
  (ASPRS PDF), Fisher 1993; Lee 1991; De Floriani and Magillo 1994; Kim et al. 2004 (UCL); Farr et al. 2007; Danielson
  and Gesch 2011; Amante and Eakins 2009; Zhang and Montgomery 1994 (abstract via EarthRef); Barber et al. 1996;
  Efron 1979; Wilson 1927; Cameron and Miller 2015; Virtanen et al. 2020; Seabold and Perktold 2010 (statsmodels docs);
  Delaunay 1934 (scan); Roy 1790 (JSTOR 106834; pages not confirmed, so omitted); Seymour 1980 (NLI catalogue);
  Owen and Pilbeam 1992 (Open Library); Hewitt 2010 (IHR review: covers to the 1870s only, cited for the early history);
  Edney 1997 (review titles); Baddeley et al. 2015 (BL catalogue).
- Not cited because not verifiable from here: Hotine's Empire Survey Review articles (only seen in Wikipedia's list),
  Sander and Manson 2007 (volume unconfirmed).

## Outputs
- index.html (+ js/page.js, data/site.json), header.png, release/paper/Hotham_Trig_Network.pdf (20 pages, ~7,000 words
  before references, abstract 250 words, 35 references), release/paper/cover_note.md, release/blog/post.html + meta.json
  + 5 figures, release/zenodo/, reddit/trig_network_collage.png + collage.py + post.md + trig-network.gif
  (/home/claude/gifs/out/trig-network.gif, script /home/claude/gifs/scripts/trig-network.py), README.md, LICENSE.
- QA: Playwright desktop 1280 and phone 390, no console errors (MapLibre logs a harmless "Expected value to be of type
  number" from the base style), no horizontal scroll, full-screen button present.

## Independent review (2026)
- Reran 01 to 05: results.json reproduced exactly (733 values). Added fail.structure_named (8), fail.unexplained (West Hills to Buddon).
- Fixed: claims that every failure was explained (Buddon is a ground mark, unexplained); 67.1% terrain-height result added to abstract, intro, conclusion, blog lede, page, Reddit post, collage, GIF; St Kilda wording on the page; 1935/1936 start; pillar height sourced to the OS station-type text quoted in the trigpoints README; Fisher 1991 and Lee 1991 claims matched to abstracts; unverified "100 m shift" and "block-by-block scale errors" claims and the Whitmore citation removed; Delaunay issue number; trigpoints title.
- Licence: OS stated (email 19/8/2016, OSM wiki) the station data may be used under OGL v3.0; release now says OS fields remain OGL v3.0.
