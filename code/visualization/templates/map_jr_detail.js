/* Demo: JR database detail panel — appended after map.js */
const JR_RECORDS = __JR_RECORDS__;
const CROSS_PAIR_RECORDS = __CROSS_PAIR_RECORDS__;
const WITHIN_PAIR_RECORDS = __WITHIN_PAIR_RECORDS__;

let _jrdActiveIds = [];
let _jrdIndex = 0;
let _jrdActiveRow = null;

function _escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _crossPairKey(a, b) {
  // Must match Python normalize_entity_for_pair → casefold keys in CROSS_PAIR_RECORDS
  return [String(a || '').trim().toLowerCase(), String(b || '').trim().toLowerCase()]
    .filter(Boolean)
    .sort()
    .join('|||');
}

function _crossPairRecordIds(entity, partner) {
  return CROSS_PAIR_RECORDS[_crossPairKey(entity, partner)] || [];
}

function _recordIdsForWithinPair(a, b) {
  const info0 = ENTITY_INFO[_sp.entities[0]] || {};
  const bestKey = _bestKey(info0, _sp.displayName);
  const pk = [a, b].sort().join('|||');
  const fromMap = WITHIN_PAIR_RECORDS[bestKey + '|||' + pk] || [];
  if (fromMap.length) return fromMap;
  const wData = WITHIN_GROUP_MAP[bestKey] || { type_i: [], type_ii: [] };
  for (const bucket of [wData.type_i || [], wData.type_ii || []]) {
    for (const item of bucket) {
      if (item.a === a && item.b === b) return item.record_ids || [];
      if (item.a === b && item.b === a) return item.record_ids || [];
    }
  }
  return [];
}

function closeJrDetail() {
  const panel = document.getElementById('jr-detail-panel');
  if (panel) {
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
  }
  if (_jrdActiveRow) {
    _jrdActiveRow.classList.remove('jr-row-active');
    _jrdActiveRow = null;
  }
  _jrdActiveIds = [];
}

function _resolveRecordId(id) {
  if (JR_RECORDS[id]) return id;
  const asInt = String(id).replace(/\.0+$/, '');
  if (asInt !== String(id) && JR_RECORDS[asInt]) return asInt;
  return id;
}

function showJrDetail(recordIds, rowEl) {
  if (!recordIds || !recordIds.length) return;
  if (_jrdActiveRow) _jrdActiveRow.classList.remove('jr-row-active');
  _jrdActiveRow = rowEl || null;
  if (_jrdActiveRow) _jrdActiveRow.classList.add('jr-row-active');
  _jrdActiveIds = recordIds.map(_resolveRecordId).filter(id => JR_RECORDS[id]);
  _jrdIndex = 0;
  if (!_jrdActiveIds.length) return;
  renderJrDetail();
  const panel = document.getElementById('jr-detail-panel');
  panel.classList.add('open');
  panel.setAttribute('aria-hidden', 'false');
}

function renderJrDetail() {
  const body = document.getElementById('jrd-body');
  const rid = _jrdActiveIds[_jrdIndex];
  const rec = JR_RECORDS[rid];
  if (!rec || !body) return;

  const scopeLabel = {
    kinship: 'Kinship',
    within_group: 'Within group',
    cross_group: 'Cross-group',
    between_groups: 'Cross-group',
  }[rec.scope_coded] || rec.scope_coded || '—';

  const reasoning = rec.reasoning || rec.notes || '—';
  const quote = rec.quote || '—';
  const sourceLine = rec.source_pdf
    ? `${rec.source || 'eHRAF'} · ${rec.source_pdf}`
    : (rec.doc_id || (rec.source === 'Keerthana' ? 'Keerthana analysis / ethnography' : rec.source || '—'));

  body.innerHTML = `
    <div class="jrd-section">
      <div class="jrd-label">Entities</div>
      <div class="jrd-entities">${_escapeHtml(rec.entity_a)} <span style="color:#94a3b8;font-weight:400">↔</span> ${_escapeHtml(rec.entity_b)}</div>
      <div class="jrd-meta">${_escapeHtml(rec.entity_a_type)} · ${_escapeHtml(rec.entity_b_type)}</div>
    </div>
    <div class="jrd-section">
      <div class="jrd-label">Classification</div>
      <div class="jrd-value"><span class="jrd-badge">${_escapeHtml(scopeLabel)}</span></div>
    </div>
    <div class="jrd-section">
      <div class="jrd-label">Source</div>
      <div class="jrd-value">${_escapeHtml(sourceLine)}</div>
      <div class="jrd-meta">${_escapeHtml(rec.ethnography_group || '')}${rec.region ? ' · ' + _escapeHtml(rec.region) : ''}</div>
    </div>
    <div class="jrd-section">
      <div class="jrd-label">Reasoning</div>
      <div class="jrd-value">${_escapeHtml(reasoning)}</div>
    </div>
    <div class="jrd-section">
      <div class="jrd-label">Quote</div>
      <div class="jrd-quote">${_escapeHtml(quote)}</div>
    </div>
    ${_jrdActiveIds.length > 1 ? `
    <div class="jrd-nav">
      <button type="button" onclick="stepJrDetail(-1)" ${_jrdIndex <= 0 ? 'disabled' : ''}>← Prev</button>
      <span>${_jrdIndex + 1} / ${_jrdActiveIds.length} records</span>
      <button type="button" onclick="stepJrDetail(1)" ${_jrdIndex >= _jrdActiveIds.length - 1 ? 'disabled' : ''}>Next →</button>
    </div>` : ''}
  `;
}

function stepJrDetail(delta) {
  const next = _jrdIndex + delta;
  if (next < 0 || next >= _jrdActiveIds.length) return;
  _jrdIndex = next;
  renderJrDetail();
}

function _attachJrRowClick(tr, recordIds) {
  if (!recordIds || !recordIds.length) return;
  tr.classList.add('jr-row-clickable');
  tr.title = 'View source & quote';
  tr.addEventListener('click', (ev) => {
    ev.stopPropagation();
    showJrDetail(recordIds, tr);
  });
}

function _attachCrossRowClicks(tr, item, recordIds) {
  if (!recordIds || !recordIds.length) return;
  tr.classList.add('jr-row-clickable', 'jr-row-cross');

  const tdSelf = tr.querySelector('.td-self');
  if (tdSelf) {
    tdSelf.title = 'View source & quote';
    tdSelf.addEventListener('click', (ev) => {
      ev.stopPropagation();
      showJrDetail(recordIds, tr);
    });
  }

  // Right column: keep navigate-to-partner; do not open the detail panel.
  const tdPartner = tr.querySelector('.td-partner');
  if (tdPartner) {
    tdPartner.title = 'Go to partner group';
    tdPartner.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const span = ev.target.closest('[data-partner]');
      const partner = (span && span.getAttribute('data-partner')) || item.partner;
      if (partner) selectJokingEntity(partner);
    });
  }
}

const _origShowTab = showTab;
showTab = function(tab) {
  _origShowTab(tab);
  closeJrDetail();

  const tbody = document.getElementById('partner-tbody');
  if (!tbody) return;

  const hint = document.getElementById('sp-hint');
  if (hint) {
    hint.textContent = tab === 'cross'
      ? 'Click Group for source/quote · click JR Partner to open that group'
      : 'Click a row to view source, reasoning, and quote';
  }

  if (tab === 'kin' || tab === 'group') {
    const pairs = _sp.within.filter(p => p.jr_type === (tab === 'kin' ? 'kin' : 'group'));
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((tr, i) => {
      const pair = pairs[i];
      if (!pair) return;
      const ids = pair.record_ids && pair.record_ids.length
        ? pair.record_ids
        : _recordIdsForWithinPair(pair.a, pair.b);
      _attachJrRowClick(tr, ids);
    });
  } else if (tab === 'cross') {
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((tr, i) => {
      const item = _sp.cross[i];
      if (!item) return;
      const ids = item.record_ids && item.record_ids.length
        ? item.record_ids
        : _crossPairRecordIds(item.entity, item.partner);
      _attachCrossRowClicks(tr, item, ids);
    });
  }
};

const _origShowGroupPanel = showGroupPanel;
showGroupPanel = function(entities, displayName) {
  _origShowGroupPanel(entities, displayName);
  _sp.within = _sp.within.map(p => ({
    ...p,
    record_ids: p.record_ids || _recordIdsForWithinPair(p.a, p.b),
  }));
  _sp.cross = _sp.cross.map(item => ({
    ...item,
    record_ids: item.record_ids && item.record_ids.length
      ? item.record_ids
      : _crossPairRecordIds(item.entity, item.partner),
  }));
};

const _origClearJokingSelection = clearJokingSelection;
clearJokingSelection = function() {
  closeJrDetail();
  _origClearJokingSelection();
};
