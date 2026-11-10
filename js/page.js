/* The trig pillar network. Every Ordnance Survey triangulation station in Great Britain on a plain MapLibre base map
 * (OpenFreeMap Positron), coloured by order, with lines to each station's nearest same-order neighbour coloured by whether
 * the terrain model (Terrain Tiles z9, curvature and refraction k = 0.13) shows a clear line of sight.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const OC = { 1: '#B4442E', 2: '#C98A2B', 3: '#2F6A9E', 4: '#8E8576' };
  const KIND = ['pillar', 'ground mark', 'intersected or roof station'];
  const ORD = { 1: 'primary (order 1)', 2: 'secondary (order 2)', 3: 'third order', 4: 'fourth order', 9: 'later control mark' };
  let map = null, D = null, yMax = 1995, timer = null, filt = qs.get('show') || 'all', showNP = false;
  const byStation = {};
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function stFilter(o) {
    const f = ['all', ['==', ['get', 'o'], o], ['<=', ['get', 'y'], yMax]];
    if (filt === 'ok') f.push(['==', ['get', 'd'], 0]);
    if (filt === 'gone') f.push(['==', ['get', 'd'], 1]);
    if (!showNP) f.push(['==', ['get', 'k'], 0]);
    return f;
  }
  function applyFilters() {
    [1, 2, 3, 4].forEach(o => map.setFilter('st' + o, stFilter(o)));
    map.setFilter('ln', ['all', ['==', ['get', 's'], 0], ['<=', ['get', 'y'], yMax]]);
    map.setFilter('dl', ['all', ['==', ['get', 's'], 1], ['<=', ['get', 'y'], yMax]]);
    map.setFilter('lbl', ['all', ['<=', ['get', 'o'], 2], ['<=', ['get', 'y'], yMax]]);
    document.querySelectorAll('.chip[data-f]').forEach(x => x.setAttribute('aria-pressed', x.dataset.f === filt));
  }
  function setYear(y) {
    yMax = y; applyFilters();
    document.getElementById('yr').value = y; document.getElementById('yrLab').textContent = `1936 to ${y}`;
  }
  function stPopup(i, ll) {
    const s = D.s[i];
    let h = `<b class="t">${esc(s[7])}</b><div class="nt">${esc(ORD[s[2] || 9])} · station ${esc(s[8])}</div><table>`;
    h += `<tr><td>Kind</td><td>${esc(KIND[s[3]])}${s[9] !== KIND[s[3]] ? ' (' + esc(s[9]) + ')' : ''}</td></tr>`;
    if (s[6] != null) h += `<tr><td>Height</td><td>${s[6].toLocaleString('en-GB')} m</td></tr>`;
    if (s[5] != null) h += `<tr><td>Commissioned</td><td>${s[5]}</td></tr>`;
    h += `<tr><td>Status</td><td><b>${s[4] ? 'recorded destroyed' : 'not recorded destroyed'}</b></td></tr></table>`;
    (byStation[i] || []).forEach(j => {
      const l = D.l[j], o = l[0] === i ? l[1] : l[0];
      h += `<div class="pl">${l[6] ? 'Triangle side to' : 'Neighbour line to'} <b>${esc(D.s[o][7])}</b>, ${l[5].toFixed(1)} km<br>${l[3] ? `in sight over the terrain model (${l[4].toFixed(0)} m to spare)` : `blocked in the model by ${(-l[4]).toFixed(1)} m`}</div>`;
    });
    h += `<p class="nt">Source: Ordnance Survey legacy triangulation list (Crown copyright; no longer maintained, so "not destroyed" may be out of date). Line of sight: Terrain Tiles z9, no trees or buildings.</p>`;
    new maplibregl.Popup({ maxWidth: '330px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function lnPopup(j, ll) {
    const l = D.l[j], a = D.s[l[0]], b = D.s[l[1]];
    const h = `<b class="t">${esc(a[7])} to ${esc(b[7])}</b><div class="nt">${esc(ORD[l[2]])}, ${l[6] ? 'side of the primary triangle net' : 'nearest same-order neighbour'}</div><table><tr><td>Length</td><td>${l[5].toFixed(1)} km</td></tr><tr><td>Terrain model</td><td><b>${l[3] ? 'clear' : 'blocked'}</b> (${l[4] >= 0 ? l[4].toFixed(0) + ' m clearance' : (-l[4]).toFixed(1) + ' m short'})</td></tr></table><p class="nt">Sight line 1.5 m above each surveyed station height, with Earth curvature and refraction (k = 0.13). Towers, spires and trees are not in the model.</p>`;
    new maplibregl.Popup({ maxWidth: '320px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function setup() {
    const feats = D.s.map((s, i) => ({ type: 'Feature', properties: { i, o: s[2] >= 1 && s[2] <= 3 ? s[2] : 4, k: s[3], d: s[4], y: s[5] || 1936, n: s[7] }, geometry: { type: 'Point', coordinates: [s[0], s[1]] } }));
    const lf = D.l.map((l, j) => { (byStation[l[0]] = byStation[l[0]] || []).push(j); (byStation[l[1]] = byStation[l[1]] || []).push(j);
      const a = D.s[l[0]], b = D.s[l[1]];
      return { type: 'Feature', properties: { j, o: l[2], v: l[3], s: l[6], y: Math.max(a[5] || 1936, b[5] || 1936) }, geometry: { type: 'LineString', coordinates: [[a[0], a[1]], [b[0], b[1]]] } }; });
    map.addSource('st', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Contains OS data © Crown copyright and database right 2018' });
    map.addSource('ln', { type: 'geojson', data: { type: 'FeatureCollection', features: lf }, attribution: 'Terrain Tiles (AWS; Mapzen)' });
    map.addLayer({ id: 'dl', type: 'line', source: 'ln', layout: { visibility: 'none' }, paint: { 'line-color': ['case', ['==', ['get', 'v'], 1], '#7C9CBC', '#B4442E'], 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 10, 2], 'line-opacity': 0.8 } });
    map.addLayer({ id: 'ln', type: 'line', source: 'ln', paint: { 'line-color': ['case', ['==', ['get', 'v'], 1], '#2F6A9E', '#B4442E'],
      'line-width': ['interpolate', ['linear'], ['zoom'], 5, ['match', ['get', 'o'], 1, 1.6, 2, 0.9, 0.6], 10, ['match', ['get', 'o'], 1, 3.5, 2, 2.6, 2], 14, 4], 'line-opacity': ['case', ['==', ['get', 'v'], 1], 0.75, 1] } });
    const base = { 1: [4.5, 7, 11], 2: [3.2, 5, 8.5], 3: [3, 4.2, 7.5], 4: [3, 3.5, 6] };
    [4, 3, 2, 1].forEach(o => {
      const r = base[o];
      map.addLayer({ id: 'st' + o, type: 'circle', source: 'st', layout: { visibility: o === 4 ? 'none' : 'visible' }, paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, ['case', ['==', ['get', 'k'], 0], r[0], 3], 9, ['case', ['==', ['get', 'k'], 0], r[1], r[1] * 0.75], 14, ['case', ['==', ['get', 'k'], 0], r[2], r[2] * 0.75]],
        'circle-color': ['case', ['==', ['get', 'd'], 1], 'rgba(255,255,255,0.6)', OC[o]],
        'circle-stroke-color': ['case', ['==', ['get', 'd'], 1], OC[o], '#ffffff'],
        'circle-stroke-width': ['case', ['==', ['get', 'd'], 1], 1.6, 0.9] } });
    });
    map.addLayer({ id: 'lbl', type: 'symbol', source: 'st', minzoom: 9, filter: ['<=', ['get', 'o'], 2], layout: { 'text-field': ['get', 'n'], 'text-size': 11.5, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.0], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#fff', 'text-halo-width': 1.5 } });
    ['st1', 'st2', 'st3', 'st4'].forEach(l => { map.on('click', l, e => { e.preventDefault(); const f = e.features[0]; stPopup(f.properties.i, f.geometry.coordinates); }); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    ['ln', 'dl'].forEach(l => { map.on('click', l, e => { if (e.defaultPrevented) return; lnPopup(e.features[0].properties.j, e.lngLat); }); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    [1, 2, 3, 4].forEach(o => document.getElementById('ly' + o).addEventListener('change', e => vis(['st' + o], e.target.checked)));
    document.getElementById('lyNP').addEventListener('change', e => { showNP = e.target.checked; applyFilters(); });
    document.getElementById('lyL').addEventListener('change', e => vis(['ln'], e.target.checked));
    document.getElementById('lyD').addEventListener('change', e => vis(['dl'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && l.id !== 'lbl').map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    document.querySelectorAll('.chip[data-f]').forEach(b => b.addEventListener('click', () => { filt = b.dataset.f; applyFilters(); }));
    const yr = document.getElementById('yr'), play = document.getElementById('play');
    yr.addEventListener('input', () => { if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; } setYear(+yr.value); });
    play.addEventListener('click', () => {
      if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; return; }
      let y = yMax >= 1995 ? 1936 : yMax; setYear(y); play.textContent = 'Pause';
      timer = setInterval(() => { y += 1; setYear(y); if (y >= 1995) { clearInterval(timer); timer = null; play.textContent = 'Play'; } }, 200);
    });
    setYear(1995);
  }
  function go(i) {
    const s = D.s[i]; fold(true);
    if (s[5] && s[5] > yMax) setYear(1995);
    const o = s[2] >= 1 && s[2] <= 3 ? s[2] : 4;
    const box = document.getElementById('ly' + o); if (!box.checked) { box.checked = true; map.setLayoutProperty('st' + o, 'visibility', 'visible'); }
    if (s[3] !== 0 && !showNP) { showNP = true; document.getElementById('lyNP').checked = true; }
    if ((filt === 'ok' && s[4]) || (filt === 'gone' && !s[4])) filt = 'all';
    applyFilters();
    map.flyTo({ center: [s[0], s[1]], zoom: small ? 10 : 10.5, duration: 1200, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.3 : 0.2))] });
    map.once('moveend', () => stPopup(i, [s[0], s[1]]));
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.s.map((s, i) => ({ t: s[7], nn: norm(s[7]), i, o: s[2] || 9, sub: `${ORD[s[2] || 9]}, ${KIND[s[3]]}` }));
    idx.sort((a, b) => a.o - b.o);
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && v.length > 3 && x.nn.includes(v))).slice(0, 14);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.t)} <span>${esc(it.sub)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.t; sug.style.display = 'none'; go(it.i); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const it = idx.find(x => x.t === a.dataset.go); if (!it) return;
      document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); go(it.i); }));
  }
  fetch('data/site.json').then(r => r.json()).then(d => {
    D = d;
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-7.8, 49.9], [1.8, 60.9]], fitBoundsOptions: { padding: small ? { top: 10, bottom: 60, left: 10, right: 10 } : { top: 40, bottom: 70, left: 380, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 16 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
    if (qs.get('trig')) { const i = D.s.findIndex(s => norm(s[7]) === norm(qs.get('trig'))); if (i >= 0) go(i); }
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov-top,.lp,.keys,.tl,.mfs-btn,.maplibregl-ctrl,.maplibregl-popup')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
