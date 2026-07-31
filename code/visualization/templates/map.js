const MURDOCK_GJ    = __MURDOCK_GJ__;
const GREG_GJ       = __GREG_GJ__;
const GEOPR_GJ      = __GEOPR_GJ__;
const ENTITY_INFO   = __ENTITY_INFO__;
const PARTNER_MAP   = __PARTNER_MAP__;
const CROSS_PAIR_TYPES = __CROSS_PAIR_TYPES__;  // "A|||B" → {EntityA: type, EntityB: type}
const REGION_COLORS = __REGION_COLORS__;
const INTENSITY_COLORS  = __INTENSITY_COLORS__; // "0"-"5" → hex color
const WITHIN_GROUP_MAP  = __WITHIN_GROUP_MAP__; // group_key_UPPER → {type_i:[{a,b}], type_ii:[{a,b}]}
const GROUP_INTENSITY   = __GROUP_INTENSITY__;  // group_key_UPPER → {n_i,n_ii,n_iii,intensity,color}

let INTENSITY_FILTERS = new Set();  // empty = show all; otherwise show matching levels

const map = L.map('map', {center:[5,20], zoom:4});
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
  {attribution:'© OSM © CARTO', maxZoom:18}).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png',
  {attribution:'', maxZoom:18, zIndex:650}).addTo(map);

const layers = {
  murdock: L.layerGroup(),
  greg:    L.layerGroup(),
  geopr:   L.layerGroup(),
  joking:  L.layerGroup().addTo(map),
};
const state = {murdock:false, greg:false, geopr:false, joking:true};
let selectedGroup = null;        // array of entity names currently selected
const jokingViz = {};          // entity → {polys:[], circles:[], labelMarker:null, origColor}
const entityGroupMap = {};     // entity name → {entities:[], displayName} (built in buildJoking)

// ── Helpers ──────────────────────────────────────────────────────────────────
function toTitle(s) {
  return s.toLowerCase().replace(/(?:^|[\\s-])\\S/g, c => c.toUpperCase());
}
// Strip the "[within] " prefix used internally for within-only entities
function cleanName(s) {
  return s.startsWith('[within] ') ? s.slice(9) : s;
}
function fmtEntityType(t) {
  if (!t) return '';
  return String(t).replace(/_/g, ' ').replace(/\s+/g, ' ').trim();
}
function entityTypeHint(type) {
  const label = fmtEntityType(type);
  return label ? `<span class="etype-hint">${label}</span>` : '';
}
let _selectedCopyName = '';  // UPPERCASE name of currently selected group / ref polygon
let _copyFlashTimer = null;
let selectedRef = null;      // { name, source, lyr } when a Murdock/GREG/GeoEPR polygon is selected

function _selectionActive() {
  return !!(selectedGroup || selectedRef);
}

function showInfo(nameHTML, metaHTML) {
  // While something is selected (JR or reference), keep left hover locked.
  if (_selectionActive()) return;
  document.getElementById('ib-name').innerHTML = nameHTML;
  document.getElementById('ib-meta').innerHTML = metaHTML || '';
  document.getElementById('infobox').style.display = 'block';
}
function hideInfo() {
  if (_selectionActive()) return;
  document.getElementById('infobox').style.display = 'none';
}
function _forceHideInfo() {
  document.getElementById('infobox').style.display = 'none';
}
function _copyTextToClipboard(text, btn) {
  if (!text) return false;
  const done = (ok) => {
    if (!btn) return;
    btn.classList.add('copied');
    btn.textContent = ok ? 'Copied!' : 'Select & copy';
    clearTimeout(_copyFlashTimer);
    _copyFlashTimer = setTimeout(() => {
      btn.classList.remove('copied');
      btn.textContent = 'Copy name';
    }, 1400);
  };
  // Prefer execCommand — works on file:// ; clipboard API often blocked there
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    ta.setSelectionRange(0, text.length);
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    if (ok) { done(true); return true; }
  } catch (e) {}
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => done(true)).catch(() => {
      window.prompt('Copy this group name:', text);
      done(false);
    });
    return true;
  }
  window.prompt('Copy this group name:', text);
  done(false);
  return true;
}
function copySelectedGroupName() {
  return _copyTextToClipboard(_selectedCopyName, document.getElementById('sp-copy'));
}
function _setCopyButton(nameUpper) {
  _selectedCopyName = (nameUpper || '').toString().trim().toUpperCase();
  const copyBtn = document.getElementById('sp-copy');
  if (!copyBtn) return;
  copyBtn.classList.remove('copied');
  copyBtn.textContent = 'Copy name';
  copyBtn.title = _selectedCopyName
    ? `Copy "${_selectedCopyName}" — or press C`
    : 'Copy group name (UPPERCASE)';
  copyBtn.style.display = _selectedCopyName ? '' : 'none';
}
function mkBadge(src) {
  const labels = {murdock:'Murdock',greg:'GREG',geopr:'GeoEPR',joshua:'Joshua Project'};
  const colors  = {murdock:'#555',greg:'#c05621',geopr:'#0e7490',joshua:'#6d28d9'};
  if (!src || !labels[src]) return '';
  return `<span style="display:inline-block;padding:1px 7px;border-radius:10px;font-size:10px;font-weight:700;color:#fff;background:${colors[src]}">${labels[src]}</span>`;
}
function mkIntBadge(intensity) {
  const intLabels = {'0':'No JR','1':'Kin only','2':'Within-group','3':'Cross-group','4':'2 types','5':'All types'};
  const bg = INTENSITY_COLORS[String(intensity)] || '#ccc';
  const textColor = intensity >= 3 ? '#fff' : '#555';
  return `<span style="display:inline-block;padding:1px 7px;border-radius:10px;font-size:10px;font-weight:700;color:${textColor};background:${bg};border:1px solid rgba(0,0,0,.1)">&#9632; ${intLabels[String(intensity)] || intensity}</span>`;
}

// ── Resolve the best GROUP_INTENSITY / WITHIN_GROUP_MAP key for any entity ────
// Tries: murdock_name → greg_name → displayName → each without trailing 'S'
function _bestKey(info0, displayName) {
  const candidates = [
    (info0.polygon_group_id || '').toUpperCase(),
    (info0.murdock_name || '').toUpperCase(),
    (info0.greg_name   || '').toUpperCase(),
    (displayName       || '').toUpperCase(),
  ].filter(Boolean);
  // Also add de-pluralised variants (e.g. "TUAREGS" → "TUAREG")
  const withDeS = candidates.flatMap(k => k.endsWith('S') ? [k, k.slice(0,-1)] : [k]);
  for (const k of withDeS) {
    if (GROUP_INTENSITY[k] !== undefined) return k;
  }
  // Fallback: first non-empty candidate
  return withDeS[0] || '';
}

function _groupIntensityLevel(gKey) {
  const gInt = GROUP_INTENSITY[gKey] || {};
  return gInt.intensity != null ? gInt.intensity : 0;
}

function passesIntensityFilter(gKey) {
  if (!INTENSITY_FILTERS.size || !gKey) return true;
  return INTENSITY_FILTERS.has(_groupIntensityLevel(gKey));
}

function _syncIntensityFilterUI() {
  document.querySelectorAll('#legend .lr-filter').forEach(el => {
    const lv = parseInt(el.dataset.intensity, 10);
    el.classList.toggle('active', INTENSITY_FILTERS.has(lv));
  });
  const hint = document.getElementById('intensity-filter-hint');
  if (hint) {
    hint.textContent = INTENSITY_FILTERS.size
      ? `Showing: ${[...INTENSITY_FILTERS].sort((a, b) => a - b).join(', ')}`
      : '';
  }
  const clearBtn = document.getElementById('intensity-clear-all');
  if (clearBtn) clearBtn.style.display = INTENSITY_FILTERS.size ? 'flex' : 'none';
}

function toggleIntensityFilter(level) {
  if (INTENSITY_FILTERS.has(level)) INTENSITY_FILTERS.delete(level);
  else INTENSITY_FILTERS.add(level);
  _syncIntensityFilterUI();
  if (state.joking) buildJoking();
}

function clearIntensityFilters() {
  INTENSITY_FILTERS.clear();
  _syncIntensityFilterUI();
  if (state.joking) buildJoking();
}

// ── Side panel state ──────────────────────────────────────────────────────────
const _sp = { entities:[], displayName:'', within:[], cross:[] };

// ── Side panel: intensity summary + within/cross-group tabs ──────────────────
// Compute intensity level (0-5) from actual pair counts
function computeIntensity(n_i, n_ii, n_iii) {
  const has = [n_i > 0, n_ii > 0, n_iii > 0];
  const nTypes = has.filter(Boolean).length;
  if (nTypes === 0) return 0;
  if (nTypes >= 3) return 5;
  if (nTypes === 2) return 4;
  // exactly 1 type
  if (n_iii > 0) return 3;
  if (n_ii > 0)  return 2;
  return 1; // only kin
}

function showGroupPanel(entities, displayName) {
  _clearRefHighlight();
  selectedRef = null;

  _sp.entities = entities;
  _sp.displayName = displayName;

  const info0 = ENTITY_INFO[entities[0]] || {};
  const bestKey = _bestKey(info0, displayName);
  _setCopyButton(bestKey || displayName);

  // JR mode UI
  const refBody = document.getElementById('sp-ref-body');
  const jrBody = document.getElementById('sp-body');
  if (refBody) refBody.style.display = 'none';
  if (jrBody) jrBody.style.display = '';

  // ── 1. Build within-group pairs from WITHIN_GROUP_MAP ─────────────────────
  const wData = WITHIN_GROUP_MAP[bestKey] || { type_i:[], type_ii:[] };
  _sp.within = [
    ...(wData.type_i  || []).map(p => ({...p, jr_type:'kin'})),
    ...(wData.type_ii || []).map(p => ({...p, jr_type:'group'})),
  ];

  // ── 2. Build cross-group pairs from PARTNER_MAP ────────────────────────────
  const seenPairs = new Set();
  _sp.cross = [];
  entities.forEach(entity => {
    (PARTNER_MAP[entity] || []).forEach(p => {
      const pairKey = [entity, p].sort().join('|||');
      if (seenPairs.has(pairKey)) return;
      seenPairs.add(pairKey);
      const types = CROSS_PAIR_TYPES[pairKey] || {};
      _sp.cross.push({
        entity,
        partner: p,
        entityType: types[entity] || '',
        partnerType: types[p] || '',
      });
    });
  });

  // ── 3. Compute accurate counts and intensity from actual data ──────────────
  const n_i   = _sp.within.filter(p => p.jr_type === 'kin').length;
  const n_ii  = _sp.within.filter(p => p.jr_type === 'group').length;
  const n_iii = _sp.cross.length;
  const intensity = computeIntensity(n_i, n_ii, n_iii);

  // ── 4. Title row: name + source badge + intensity badge ───────────────────
  const titleRow = document.getElementById('sp-title-row');
  titleRow.innerHTML = displayName + ' ' + mkBadge(info0.source || '')
    + (intensity > 0 ? ' ' + mkIntBadge(intensity) : '');

  // ── 5. Counts summary from actual data (not INTENSITY_DATA) ───────────────
  document.getElementById('sp-counts').innerHTML =
    `Within-kin: <b>${n_i}</b>`
    + ` &nbsp;·&nbsp; Within-group: <b>${n_ii}</b>`
    + ` &nbsp;·&nbsp; Cross-group: <b>${n_iii}</b>`;

  // ── 6. Show/hide tabs (only tabs with data), decide default ──────────────
  const hasKin   = n_i   > 0;
  const hasGroup = n_ii  > 0;
  const hasCross = n_iii > 0;
  const nTabs = [hasKin, hasGroup, hasCross].filter(Boolean).length;

  const tabsEl = document.getElementById('sp-tabs');
  document.getElementById('tab-btn-kin').style.display   = hasKin   ? '' : 'none';
  document.getElementById('tab-btn-group').style.display = hasGroup ? '' : 'none';
  document.getElementById('tab-btn-cross').style.display = hasCross ? '' : 'none';
  tabsEl.style.display = nTabs > 1 ? 'flex' : 'none';

  // Default tab: cross > group > kin
  showTab(hasCross ? 'cross' : (hasGroup ? 'group' : 'kin'));

  document.getElementById('side-panel').style.display = 'flex';
}

function showTab(tab) {
  ['kin','group','cross'].forEach(t => {
    const btn = document.getElementById('tab-btn-' + t);
    if (btn) btn.classList.toggle('active', t === tab);
  });

  const tbody = document.getElementById('partner-tbody');
  tbody.innerHTML = '';

  if (tab === 'kin' || tab === 'group') {
    document.getElementById('col-left').textContent  = 'Entity A';
    document.getElementById('col-right').textContent = 'Entity B';
    const pairs = _sp.within.filter(p => p.jr_type === (tab === 'kin' ? 'kin' : 'group'));
    if (!pairs.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td'); td.colSpan = 2;
      td.style.cssText = 'text-align:center;color:#bbb;padding:18px;font-size:11px';
      td.textContent = 'No data for this type';
      tr.appendChild(td); tbody.appendChild(tr);
      return;
    }
    pairs.forEach(({a, b}) => {
      const tr = document.createElement('tr');
      const td1 = document.createElement('td'); td1.className = 'td-self'; td1.textContent = a;
      const td2 = document.createElement('td'); td2.className = 'td-partner';
      td2.style.cursor = 'default'; td2.textContent = b;
      tr.appendChild(td1); tr.appendChild(td2); tbody.appendChild(tr);
    });
  } else {
    document.getElementById('col-left').textContent  = 'Group';
    document.getElementById('col-right').textContent = 'JR Partner';
    if (!_sp.cross.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td'); td.colSpan = 2;
      td.style.cssText = 'text-align:center;color:#bbb;padding:18px;font-size:11px';
      td.textContent = 'No cross-group JR data available';
      tr.appendChild(td); tbody.appendChild(tr);
      return;
    }
    _sp.cross.forEach(({entity, partner, entityType, partnerType}) => {
      const tr = document.createElement('tr');
      const td1 = document.createElement('td'); td1.className = 'td-self';
      const selfName = _sp.entities.length > 1 ? cleanName(entity) : _sp.displayName;
      td1.innerHTML = selfName + entityTypeHint(entityType);
      const td2 = document.createElement('td'); td2.className = 'td-partner';
      const partnerAttr = String(partner).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
      td2.innerHTML =
        `<span data-partner="${partnerAttr}">${cleanName(partner)}</span>`
        + entityTypeHint(partnerType);
      tr.appendChild(td1); tr.appendChild(td2); tbody.appendChild(tr);
    });
  }
}

// ── Selection: fade entities not related to the selected group ────────────────
function _setLayerPointerEvents(lyr, enabled) {
  if (!lyr) return;
  try {
    lyr.options.interactive = !!enabled;
    if (lyr._path) {
      lyr._path.style.pointerEvents = enabled ? 'auto' : 'none';
      if (enabled) L.DomUtil.addClass(lyr._path, 'leaflet-interactive');
      else L.DomUtil.removeClass(lyr._path, 'leaflet-interactive');
    }
    const el = lyr.getElement && lyr.getElement();
    if (el) el.style.pointerEvents = enabled ? 'auto' : 'none';
  } catch (e) {}
}

function applyJokingSelection(selEntities) {
  const selSet = selEntities ? new Set(selEntities) : null;
  const partnerSet = selEntities
    ? new Set(selEntities.flatMap(e => PARTNER_MAP[e] || []).filter(p => !selSet.has(p)))
    : null;

  // Shared poly/circle/label layers: keep interactive if ANY linked entity is hit
  const keepHit = new Set();
  if (selSet) {
    Object.keys(jokingViz).forEach(name => {
      if (!selSet.has(name) && !(partnerSet && partnerSet.has(name))) return;
      const v = jokingViz[name];
      v.polys.forEach(l => keepHit.add(l));
      v.circles.forEach(l => keepHit.add(l));
      if (v.labelMarker) keepHit.add(v.labelMarker);
    });
  }

  Object.keys(jokingViz).forEach(name => {
    const v = jokingViz[name];
    const isSel  = selSet && selSet.has(name);
    const isPart = partnerSet && partnerSet.has(name);
    const active = !selSet || isSel || isPart;
    const fillOp = active ? (isSel ? 0.95 : 0.85) : 0.08;
    const bw     = isSel ? 3.5 : (isPart ? 2.5 : 1.0);
    const bc     = isSel ? '#c0392b' : (isPart ? '#e67e22' : '#555');
    v.polys.forEach(lyr => {
      lyr.setStyle({fillOpacity:fillOp, color:bc, weight:bw});
      _setLayerPointerEvents(lyr, !selSet || keepHit.has(lyr));
    });
    v.circles.forEach(lyr => {
      lyr.setStyle({fillOpacity:fillOp, color:bc, weight:bw, radius: isSel ? 10 : (isPart ? 9 : 7)});
      _setLayerPointerEvents(lyr, !selSet || keepHit.has(lyr));
    });
    if (v.labelMarker) {
      const labelHit = !selSet || keepHit.has(v.labelMarker);
      _setLayerPointerEvents(v.labelMarker, labelHit);
      try {
        const el  = v.labelMarker.getElement();
        const inn = el && el.querySelector('.joking-lbl');
        if (inn) {
          inn.style.opacity    = active ? '1' : '0.15';
          inn.style.fontSize   = isSel ? '13px' : (isPart ? '12px' : '11px');
          inn.style.color      = isSel ? '#c0392b' : (isPart ? '#c67d0a' : '#111');
          inn.style.pointerEvents = labelHit ? 'auto' : 'none';
          // Bar only appears for selected/partner; transparent when inactive or no selection
          const barColor = !selSet ? 'transparent'
            : isSel ? '#c0392b' : isPart ? '#e67e22' : 'transparent';
          const barW = isSel ? 4 : 3;
          inn.style.borderLeft = `${barW}px solid ${barColor}`;
        }
      } catch(e) {}
    }
  });
}

// Select all entities in a group together
function selectGroup(entities, displayName) {
  selectedGroup = entities;
  _forceHideInfo();  // drop any hover tooltip; selection locks hover updates
  try { map.closeTooltip(); } catch (e) {}
  applyJokingSelection(entities);
  showGroupPanel(entities, displayName || entities[0]);
  const info = ENTITY_INFO[entities[0]];
  if (info && info.lat != null) map.setView([info.lat, info.lon], 6);
}

// Navigate to an entity by name (used from partner list clicks / search)
function selectJokingEntity(name) {
  const grp = entityGroupMap[name];
  if (grp) selectGroup(grp.entities, grp.displayName);
  else selectGroup([name], cleanName(name));
}

function _clearRefHighlight() {
  if (!selectedRef || !selectedRef.lyr) return;
  try {
    if (selectedRef.source === 'murdock' && mMap[selectedRef.name]) {
      const { lyr, idx } = mMap[selectedRef.name];
      lyr.setStyle(mStyle(idx));
    } else if (selectedRef._prev) {
      selectedRef.lyr.setStyle(selectedRef._prev);
    }
  } catch (e) {}
}

function showRefPanel(name, sourceKey) {
  _setCopyButton(name);
  document.getElementById('sp-title-row').innerHTML =
    toTitle(name) + ' ' + mkBadge(sourceKey);
  document.getElementById('sp-counts').innerHTML = '';

  document.getElementById('sp-tabs').style.display = 'none';
  const jrBody = document.getElementById('sp-body');
  const refBody = document.getElementById('sp-ref-body');
  if (jrBody) jrBody.style.display = 'none';
  if (refBody) refBody.style.display = 'block';

  document.getElementById('side-panel').style.display = 'flex';
}

function selectRefHomeland(name, sourceKey, lyr) {
  // Switching away from a JR selection
  if (selectedGroup) {
    selectedGroup = null;
    applyJokingSelection(null);
  }
  _clearRefHighlight();
  selectedRef = { name, source: sourceKey, lyr: lyr || null };

  _forceHideInfo();
  try { map.closeTooltip(); } catch (e) {}

  if (lyr) {
    selectedRef._prev = {
      weight: lyr.options.weight,
      color: lyr.options.color,
      fillOpacity: lyr.options.fillOpacity,
      fillColor: lyr.options.fillColor,
    };
    lyr.setStyle({
      weight: 3.5,
      color: '#c0392b',
      fillOpacity: Math.max(0.72, lyr.options.fillOpacity || 0.55),
    });
    try {
      map.fitBounds(lyr.getBounds(), { maxZoom: 8, padding: [40, 40] });
    } catch (e) {}
  }

  showRefPanel(name, sourceKey);
}

function clearJokingSelection() {
  if (selectedGroup) {
    selectedGroup = null;
    applyJokingSelection(null);
  }
  _clearRefHighlight();
  selectedRef = null;
  _selectedCopyName = '';
  document.getElementById('side-panel').style.display = 'none';
  const refBody = document.getElementById('sp-ref-body');
  const jrBody = document.getElementById('sp-body');
  if (refBody) refBody.style.display = 'none';
  if (jrBody) jrBody.style.display = '';
  _forceHideInfo();
}

map.on('click', () => { if (_selectionActive()) clearJokingSelection(); });

// ── Unified hover info for JR entities (circles / point markers) ─────────────
function showEntityInfo(name) {
  const info = ENTITY_INFO[name] || {};
  const badge = mkBadge(info.source || '');
  showInfo(name, badge);
}

// ── Background layers + GIS search index (Keerthana-style) ───────────────────
const searchIdx = [];
const _searchSeen = new Set();
const mMap = {};

function _pushSearch(label, src, lat, lon, lyr, jrName) {
  const key = src + '|' + label.toUpperCase();
  if (_searchSeen.has(key)) return;
  _searchSeen.add(key);
  searchIdx.push({label, src, lat, lon, lyr: lyr || null, name: jrName || label});
}

function _boundsCenter(lyr) {
  try {
    const c = lyr.getBounds().getCenter();
    return {lat: c.lat, lon: c.lng};
  } catch (e) { return null; }
}

function pickSearch(h) {
  const layerKey = {Murdock:'murdock', GREG:'greg', GeoEPR:'geopr'}[h.src];
  if (layerKey && !state[layerKey]) toggleLayer(layerKey);

  const sourceKey = h.src === 'Murdock' ? 'murdock' : h.src === 'GREG' ? 'greg' : h.src === 'GeoEPR' ? 'geopr' : 'joshua';
  if (h.lyr && (sourceKey === 'murdock' || sourceKey === 'greg' || sourceKey === 'geopr')) {
    selectRefHomeland(h.label, sourceKey, h.lyr);
    return;
  }

  showInfo(h.label + ' ' + mkBadge(sourceKey),
    '<span style="color:#666;font-size:11px">Reference layer — use for polygon_id / aliases</span>');
  if (h.lyr) {
    try {
      map.fitBounds(h.lyr.getBounds(), {maxZoom: 8, padding: [30, 30]});
      if (h.lyr.openTooltip) h.lyr.openTooltip();
      const prev = {weight: h.lyr.options.weight, color: h.lyr.options.color};
      h.lyr.setStyle({weight: 3, color: '#f59e0b'});
      setTimeout(() => {
        if (h.src === 'Murdock' && mMap[h.label]) {
          mMap[h.label].lyr.setStyle(mStyle(mMap[h.label].idx));
        } else {
          h.lyr.setStyle({weight: prev.weight || 0.35, color: prev.color || '#fff'});
        }
      }, 2000);
      return;
    } catch (e) { /* fall through */ }
  }
  if (h.lat != null && h.lon != null) map.setView([h.lat, h.lon], 7);
}

function mStyle(i) {
  const h=(i*0.618033988749895)%1,s=0.55,v=0.72,c=v*s,
        x=c*(1-Math.abs((h*6)%2-1)),m=v-c;
  let r=0,g=0,b=0; const hi=Math.floor(h*6);
  if(hi===0){r=c;g=x;}else if(hi===1){r=x;g=c;}else if(hi===2){g=c;b=x;}
  else if(hi===3){g=x;b=c;}else if(hi===4){r=x;b=c;}else{r=c;b=x;}
  return {fillColor:`rgb(${~~((r+m)*255)},${~~((g+m)*255)},${~~((b+m)*255)})`,fillOpacity:0.55,color:'#fff',weight:0.35};
}
const mFts = MURDOCK_GJ.features;
L.geoJSON(MURDOCK_GJ, {
  style: f => mStyle(mFts.indexOf(f)),
  onEachFeature: (f,lyr) => {
    const p=f.properties;
    mMap[p.NAME]={lyr, idx:mFts.indexOf(f)};
    lyr.bindTooltip(p.NAME,{sticky:false, direction:'center', opacity:0.9});
    lyr.on('mouseover',() => showInfo(p.NAME,'<span style="color:#999;font-size:11px">Murdock reference · click to open panel</span>'));
    lyr.on('mouseout',hideInfo);
    lyr.on('click', e => {
      L.DomEvent.stopPropagation(e);
      selectRefHomeland(p.NAME, 'murdock', lyr);
    });
    _pushSearch(p.NAME, 'Murdock', p.LAT, p.LON, lyr);
  }
}).addTo(layers.murdock);

L.geoJSON(GREG_GJ, {
  style: f => ({fillColor:f.properties.COLOR||'#f4a261',fillOpacity:0.60,color:'#fff',weight:0.35}),
  onEachFeature: (f,lyr) => {
    const p=f.properties;
    lyr.bindTooltip(p.NAME,{sticky:false, direction:'center', opacity:0.9});
    lyr.on('mouseover',() => showInfo(p.NAME,'<span style="color:#999;font-size:11px">GREG reference · click to open panel</span>'));
    lyr.on('mouseout',hideInfo);
    lyr.on('click', e => {
      L.DomEvent.stopPropagation(e);
      selectRefHomeland(p.NAME, 'greg', lyr);
    });
    const c = _boundsCenter(lyr);
    if (c) _pushSearch(p.NAME, 'GREG', c.lat, c.lon, lyr);
  }
}).addTo(layers.greg);

L.geoJSON(GEOPR_GJ, {
  style: f => ({fillColor:f.properties.COLOR||'#2ec4b6',fillOpacity:0.60,color:'#fff',weight:0.35}),
  onEachFeature: (f,lyr) => {
    const p=f.properties;
    const tip = `${p.NAME} (${p.FROM}–${p.TO})`;
    lyr.bindTooltip(tip,{sticky:false, direction:'center', opacity:0.9});
    lyr.on('mouseover',() => showInfo(p.NAME,'<span style="color:#999;font-size:11px">GeoEPR reference · click to open panel</span>'));
    lyr.on('mouseout',hideInfo);
    lyr.on('click', e => {
      L.DomEvent.stopPropagation(e);
      selectRefHomeland(p.NAME, 'geopr', lyr);
    });
    const c = _boundsCenter(lyr);
    if (c) _pushSearch(p.NAME, 'GeoEPR', c.lat, c.lon, lyr);
  }
}).addTo(layers.geopr);

// ── Joking layer: build from ENTITY_INFO (Keerthana-style) ───────────────────
function reg(rawName, type, lyr, origColor) {
  if (!jokingViz[rawName])
    jokingViz[rawName] = {polys:[], circles:[], labelMarker:null, origColor: origColor||'#888'};
  if (type==='poly')   jokingViz[rawName].polys.push(lyr);
  if (type==='circle') jokingViz[rawName].circles.push(lyr);
  if (type==='label')  jokingViz[rawName].labelMarker = lyr;
}

function buildJoking() {
  layers.joking.clearLayers();
  Object.keys(jokingViz).forEach(k => delete jokingViz[k]);

  const murdockGroup={}, gregGroup={}, eprGroup={};
  const pointEntities=[];

  Object.keys(ENTITY_INFO).forEach(name => {
    const info = ENTITY_INFO[name];
    if (!info) return;
    if (info.source==='murdock' && info.murdock_name) {
      const gKey = info.murdock_name.toUpperCase();
      if (!passesIntensityFilter(gKey)) return;
      const gInt = GROUP_INTENSITY[gKey];
      const iColor = gInt ? gInt.color : info.color;
      const g = murdockGroup[info.murdock_name] = murdockGroup[info.murdock_name] || {entities:[], color: iColor};
      g.entities.push(name);
    } else if (info.source==='greg' && info.greg_name) {
      const gKey = info.greg_name.toUpperCase();
      if (!passesIntensityFilter(gKey)) return;
      const gInt = GROUP_INTENSITY[gKey];
      const iColor = gInt ? gInt.color : info.color;
      const g = gregGroup[info.greg_name] = gregGroup[info.greg_name] || {entities:[], color: iColor};
      g.entities.push(name);
    } else if (info.source==='geopr' && info.greg_name) {
      const gKey = info.greg_name.toUpperCase();
      if (!passesIntensityFilter(gKey)) return;
      const gInt = GROUP_INTENSITY[gKey];
      const iColor = gInt ? gInt.color : info.color;
      const g = eprGroup[info.greg_name] = eprGroup[info.greg_name] || {entities:[], color: iColor};
      g.entities.push(name);
    } else if (info.lat != null) {
      const pg = (info.polygon_group_id || '').toUpperCase();
      const gKey = pg || name.toUpperCase();
      if (!passesIntensityFilter(gKey)) return;
      pointEntities.push(name);
    }
  });

  // Murdock JR polygons (colored by intensity)
  const jmFeats = MURDOCK_GJ.features.filter(f => murdockGroup[f.properties.NAME]);
  L.geoJSON({type:'FeatureCollection', features:jmFeats}, {
    style: f => ({fillColor:murdockGroup[f.properties.NAME].color, fillOpacity:0.88, color:'#444', weight:1.5}),
    onEachFeature: (f,lyr) => {
      const p=f.properties, grp=murdockGroup[p.NAME];
      grp.entities.forEach(e => reg(e,'poly',lyr,grp.color));
      lyr.on('click',e => { L.DomEvent.stopPropagation(e); selectGroup(grp.entities, toTitle(p.NAME)); });
      lyr.on('mouseover',() => showInfo(`${toTitle(p.NAME)} ${mkBadge('murdock')}`, intHoverLines(p.NAME, grp.entities)));
      lyr.on('mouseout',hideInfo);
    }
  }).addTo(layers.joking);

  // Helper: build hover lines using pre-computed GROUP_INTENSITY
  function intHoverLines(grpName, entities) {
    const info0 = ENTITY_INFO[entities[0]] || {};
    const k = _bestKey(info0, toTitle(grpName));
    const gInt = GROUP_INTENSITY[k] || {};
    const n_i = gInt.n_i || 0, n_ii = gInt.n_ii || 0, n_iii = gInt.n_iii || 0;
    const intensity = gInt.intensity != null ? gInt.intensity : computeIntensity(n_i, n_ii, n_iii);
    const intLine = intensity > 0
      ? `<div style="margin-top:4px;font-size:11px">${mkIntBadge(intensity)}</div>`
        + `<div style="font-size:10px;color:#999;margin-top:3px">`
        + `Kin: ${n_i} · Within: ${n_ii} · Cross: ${n_iii}</div>`
      : '';
    const coNames = entities.length > 1
      ? `<div style="color:#888;font-size:11px;margin-top:3px">${entities.map(cleanName).join(', ')}</div>` : '';
    return intLine + coNames;
  }

  // GREG JR polygons
  Object.keys(gregGroup).forEach(grpName => {
    const grp=gregGroup[grpName];
    const feats=GREG_GJ.features.filter(f =>
      f.properties.NAME===grpName||
      (f.properties.NAME||'').toLowerCase()===grpName.toLowerCase());
    if (!feats.length) return;
    L.geoJSON({type:'FeatureCollection',features:feats}, {
      style: () => ({fillColor:grp.color, fillOpacity:0.88, color:'#444', weight:1.5}),
      onEachFeature: (f,lyr) => {
        grp.entities.forEach(e => reg(e,'poly',lyr,grp.color));
        lyr.on('click',e => { L.DomEvent.stopPropagation(e); selectGroup(grp.entities, toTitle(grpName)); });
        lyr.on('mouseover',() => showInfo(`${toTitle(grpName)} ${mkBadge('greg')}`, intHoverLines(grpName, grp.entities)));
        lyr.on('mouseout',hideInfo);
      }
    }).addTo(layers.joking);
  });

  // GeoEPR JR polygons (exact NAME match only)
  Object.keys(eprGroup).forEach(grpName => {
    const grp=eprGroup[grpName];
    const feats=GEOPR_GJ.features.filter(f => f.properties.NAME===grpName);
    if (!feats.length) return;
    L.geoJSON({type:'FeatureCollection',features:feats}, {
      style: () => ({fillColor:grp.color, fillOpacity:0.88, color:'#444', weight:1.5}),
      onEachFeature: (f,lyr) => {
        grp.entities.forEach(e => reg(e,'poly',lyr,grp.color));
        lyr.on('click',e => { L.DomEvent.stopPropagation(e); selectGroup(grp.entities, toTitle(grpName)); });
        lyr.on('mouseover',() => showInfo(`${toTitle(grpName)} ${mkBadge('geopr')}`, intHoverLines(grpName, grp.entities)));
        lyr.on('mouseout',hideInfo);
      }
    }).addTo(layers.joking);
  });

  // Point markers (Joshua / fallback coords)
  const usedCoords = {};
  pointEntities.forEach(name => {
    const info=ENTITY_INFO[name]; if (!info || info.lat==null) return;
    // Use GROUP_INTENSITY color (avoids grey for unmatched regions)
    const pg = (info.polygon_group_id || '').toUpperCase();
    const gInt = GROUP_INTENSITY[pg] || GROUP_INTENSITY[name.toUpperCase()] || {};
    const iColor = gInt.color || info.color;
    const key=info.lat.toFixed(2)+'|'+info.lon.toFixed(2);
    if (usedCoords[key]) { reg(name,'circle',usedCoords[key],iColor); return; }
    const circ=L.circleMarker([info.lat,info.lon],{
      radius:8, fillColor:iColor, color:'#333', weight:1.5, fillOpacity:0.92
    })
    .on('mouseover',() => showInfo(name + ' ' + mkBadge(info.source||''), intHoverLines(name, [name])))
    .on('mouseout',hideInfo)
    .on('click',e => { L.DomEvent.stopPropagation(e); selectJokingEntity(name); })
    .addTo(layers.joking);
    usedCoords[key]=circ;
    reg(name,'circle',circ,iColor);
  });

  // ── Register entityGroupMap and create one label per polygon group ──────────
  function makeLabel(lat, lon, color, displayName, entities, srcKey) {
    return L.marker([lat, lon], {
      icon: L.divIcon({
        className:'',
        html:`<div class="joking-lbl" style="border-left:3px solid transparent;padding-left:5px">${displayName}</div>`,
        iconAnchor:[0,10]
      }),
      interactive:true, zIndexOffset:500
    })
    .on('mouseover', () => showInfo(displayName + ' ' + mkBadge(srcKey), intHoverLines(displayName, entities)))
    .on('mouseout', hideInfo)
    .on('click', e => { L.DomEvent.stopPropagation(e); selectGroup(entities, displayName); });
  }

  // Murdock groups
  Object.keys(murdockGroup).forEach(mName => {
    const grp = murdockGroup[mName];
    const displayName = toTitle(mName);
    const mKey = mName.toUpperCase();
    grp.entities.forEach(e => { entityGroupMap[e] = {entities: grp.entities, displayName, murdockKey: mKey}; });
    const firstInfo = ENTITY_INFO[grp.entities[0]]; if (!firstInfo || firstInfo.lat==null) return;
    const marker = makeLabel(firstInfo.lat, firstInfo.lon, grp.color, displayName, grp.entities, 'murdock');
    marker.addTo(layers.joking);
    grp.entities.forEach(e => reg(e,'label',marker,grp.color));
  });

  // GREG groups
  Object.keys(gregGroup).forEach(gName => {
    const grp = gregGroup[gName];
    const displayName = toTitle(gName);
    grp.entities.forEach(e => { entityGroupMap[e] = {entities: grp.entities, displayName, murdockKey: null}; });
    const firstInfo = ENTITY_INFO[grp.entities[0]]; if (!firstInfo || firstInfo.lat==null) return;
    const marker = makeLabel(firstInfo.lat, firstInfo.lon, grp.color, displayName, grp.entities, 'greg');
    marker.addTo(layers.joking);
    grp.entities.forEach(e => reg(e,'label',marker,grp.color));
  });

  // GeoEPR groups
  Object.keys(eprGroup).forEach(eName => {
    const grp = eprGroup[eName];
    const displayName = toTitle(eName);
    grp.entities.forEach(e => { entityGroupMap[e] = {entities: grp.entities, displayName, murdockKey: null}; });
    const firstInfo = ENTITY_INFO[grp.entities[0]]; if (!firstInfo || firstInfo.lat==null) return;
    const marker = makeLabel(firstInfo.lat, firstInfo.lon, grp.color, displayName, grp.entities, 'geopr');
    marker.addTo(layers.joking);
    grp.entities.forEach(e => reg(e,'label',marker,grp.color));
  });

  // Point entities: label = entity name (no parent polygon)
  const usedLabelCoords = {};
  pointEntities.forEach(name => {
    const info = ENTITY_INFO[name]; if (!info || info.lat==null) return;
    const dispName = cleanName(name);
    entityGroupMap[name] = {entities:[name], displayName:dispName, murdockKey: null};
    const key = info.lat.toFixed(2)+'|'+info.lon.toFixed(2);
    if (usedLabelCoords[key]) return;
    usedLabelCoords[key] = true;
    const marker = makeLabel(info.lat, info.lon, info.color, dispName, [name], info.source||'');
    marker.addTo(layers.joking);
    reg(name,'label',marker,info.color);
  });
}

function _appendJrSearchHits() {
  const seen = new Set(searchIdx.map(h => h.label.toUpperCase()));
  Object.keys(ENTITY_INFO).forEach(name => {
    const info = ENTITY_INFO[name];
    if (info.lat == null) return;
    const disp = cleanName(name);
    if (seen.has(disp.toUpperCase())) return;
    seen.add(disp.toUpperCase());
    const src = (info.source === 'joshua') ? 'Joshua' : 'JR';
    _pushSearch(disp, src, info.lat, info.lon, null, name);
  });
  Object.keys(entityGroupMap).forEach(name => {
    const grp = entityGroupMap[name];
    if (!grp || seen.has(grp.displayName.toUpperCase())) return;
    const info = ENTITY_INFO[name];
    if (!info || info.lat == null) return;
    seen.add(grp.displayName.toUpperCase());
    _pushSearch(grp.displayName, 'JR', info.lat, info.lon, null, name);
  });
}

// ── Layer toggle ─────────────────────────────────────────────────────────────
function toggleLayer(id) {
  state[id] = !state[id];
  document.getElementById('b-'+id).classList.toggle('on', state[id]);
  if (state[id]) {
    if (id==='joking') { buildJoking(); layers.joking.addTo(map); }
    else layers[id].addTo(map);
  } else {
    map.removeLayer(layers[id]);
    if (id==='joking') clearJokingSelection();
    if ((id==='murdock' || id==='greg' || id==='geopr') && selectedRef && selectedRef.source === id) {
      clearJokingSelection();
    }
  }
}

// ── Search with autocomplete ───────────────────────────────────────────────
const sEl=document.getElementById('search'), aEl=document.getElementById('ac');
let aList=[], aIdx=-1;

function _runSearch(q) {
  aEl.innerHTML=''; aList=[]; aIdx=-1;
  if (q.length < 2) { aEl.style.display='none'; return; }
  const hits=searchIdx.filter(x => x.label.toLowerCase().includes(q)).slice(0,60);
  aList=hits;
  if (!hits.length) { aEl.style.display='none'; return; }
  hits.forEach(h => {
    const d=document.createElement('div');
    d.className='aci';
    d.innerHTML=`${h.label} <span class="acs">[${h.src}]</span>`;
    d.addEventListener('mousedown', e => {
      e.preventDefault();
      sEl.value=h.label;
      aEl.style.display='none';
      if (entityGroupMap[h.name] || ENTITY_INFO[h.name]) selectJokingEntity(h.name || h.label);
      else pickSearch(h);
    });
    aEl.appendChild(d);
  });
  aEl.style.display='block';
}

sEl.addEventListener('input', () => _runSearch(sEl.value.trim().toLowerCase()));
sEl.addEventListener('keydown', e => {
  const els=aEl.querySelectorAll('.aci');
  if (e.key==='ArrowDown') { aIdx=Math.min(aIdx+1,els.length-1); els.forEach((el,i)=>el.classList.toggle('sel',i===aIdx)); e.preventDefault(); }
  else if (e.key==='ArrowUp') { aIdx=Math.max(aIdx-1,0); els.forEach((el,i)=>el.classList.toggle('sel',i===aIdx)); e.preventDefault(); }
  else if (e.key==='Enter' && aIdx>=0) {
    const h=aList[aIdx]; sEl.value=h.label; aEl.style.display='none';
    if (entityGroupMap[h.name] || ENTITY_INFO[h.name]) selectJokingEntity(h.name || h.label);
    else pickSearch(h);
  }
  else if (e.key==='Escape') aEl.style.display='none';
});
document.addEventListener('click', e => {
  if (!document.getElementById('sw').contains(e.target)) aEl.style.display='none';
});

// ── Init ─────────────────────────────────────────────────────────────────────
(function _wireCopyNameUI() {
  const spCopy = document.getElementById('sp-copy');
  if (spCopy) {
    spCopy.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      copySelectedGroupName();
    });
  }
  document.addEventListener('keydown', e => {
    if (e.key !== 'c' && e.key !== 'C') return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = (e.target && e.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || (e.target && e.target.isContentEditable)) return;
    if (copySelectedGroupName()) e.preventDefault();
  });
})();

buildJoking();
_appendJrSearchHits();
