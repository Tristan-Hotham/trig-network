**Title:** [OC] Britain's trig pillars were sited so each could see its neighbours. Over a modern terrain model, with the surveyed station heights, 95% of neighbouring primary stations still can; random lines of the same length, 11%

**Body:**

I mapped every station in the Ordnance Survey's old triangulation list (24,433 stations, 6,573 concrete pillars) and checked the rule they were built to: every station must see its neighbours.

- 228 of 240 lines from a primary station to its nearest primary neighbour are clear over the terrain, allowing for the curve of the Earth (95%).
- Move both ends 1 km in a random direction: 17% clear. Random pairs of points on land at the same distances: 11%.
- The 12 failures: 8 touch lighthouses, a cathedral, an observatory, castles or water towers whose heights the list leaves out; 3 are lines in flat East Anglia and Lincolnshire at stations where the surveyors used steel towers (often about 30 m); 1 is unexplained.
- The catch: this uses the surveyed station heights. With the terrain model's own heights at the ends, only 67% are clear, because the model rounds off hilltops (a median 22 m too low at the pillars). Still far above the random lines.
- 99% of pillars carry a commissioning date from 1936 to 1962. 6.3% are recorded destroyed, against 36% of bolts and ground marks.

Interactive map with every trig point, the lines of sight and an era slider: https://maps.tristanhotham.com/trig-network/

**Source comment:**

Data: Ordnance Survey legacy triangulation station list (Contains OS data (c) Crown copyright and database right 2018, Open Government Licence v3.0, via the trigpoints R package); Terrain Tiles on AWS (Mapzen; SRTM, EU-DEM, GMTED2010); OpenStreetMap (ODbL). Method: line of sight sampled every 100 m with Earth curvature and refraction (k = 0.13), ends 1.5 m above the surveyed station height; placebo lines; plan written before the analysis. Tools: Python (pandas, scipy, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/trig-network
