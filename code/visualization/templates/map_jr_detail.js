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
  // Align with Python normalize_entity_for_pair (canonicalize + casefold)
  function norm(s) {
    let t = String(s || '').trim();
    t = t.replace(/^the\s+/i, '');
    const key = t.toLowerCase();
    if (key === 'wa-sukuma' || key === 'sukuma') return 'sukuma';
    return key;
  }
  return [norm(a), norm(b)].filter(Boolean).sort().join('|||');
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

function _isHttpUrl(s) {
  return /^https?:\/\//i.test(String(s || '').trim());
}

function _formatPageSuffix(page) {
  const p = String(page || '').trim();
  if (!p) return '';
  // Already looks like "p. 12" / "pp. 12–14" / "page 12"
  if (/^(pp?\.|pages?)\b/i.test(p)) return ` ${_escapeHtml(p)}`;
  return ` p. ${_escapeHtml(p)}`;
}

function _formatSourceHtml(rec) {
  // Prefer full citation → URL link → file. Append page when present.
  const cite = String(rec.source_citation || '').trim();
  const url = String(rec.source_url || '').trim();
  const file = String(rec.source_pdf || rec.doc_id || '').trim()
    .replace(/^\/+/, '');
  const pageSuffix = _formatPageSuffix(rec.source_page);

  if (cite) {
    if (_isHttpUrl(cite)) {
      return `<a href="${_escapeHtml(cite)}" target="_blank" rel="noopener noreferrer">${_escapeHtml(cite)}</a>${pageSuffix}`;
    }
    return _escapeHtml(cite) + pageSuffix;
  }
  if (url) {
    if (_isHttpUrl(url)) {
      return `<a href="${_escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${_escapeHtml(url)}</a>${pageSuffix}`;
    }
    return _escapeHtml(url) + pageSuffix;
  }
  if (file) return _escapeHtml(file) + pageSuffix;
  if (pageSuffix) return pageSuffix.trim();
  return '—';
}

function _formatReasoning(rec) {
  const note = String(rec.notes || rec.reasoning || '').trim();
  if (note) return _escapeHtml(note);
  return 'see quote';
}

function _toTitleName(s) {
  return String(s || '')
    .toLowerCase()
    .replace(/(?:^|[\s-])\S/g, c => c.toUpperCase());
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

  const quote = rec.quote || '—';
  const isCross = ['cross_group', 'between_groups'].includes(rec.scope_coded);
  const nameA = isCross ? _toTitleName(rec.entity_a) : rec.entity_a;
  const nameB = isCross ? _toTitleName(rec.entity_b) : rec.entity_b;

  body.innerHTML = `
    <div class="jrd-section">
      <div class="jrd-label">Entities</div>
      <div class="jrd-entities">${_escapeHtml(nameA)} <span style="color:#94a3b8;font-weight:400">↔</span> ${_escapeHtml(nameB)}</div>
      <div class="jrd-meta">${_escapeHtml(rec.entity_a_type)} · ${_escapeHtml(rec.entity_b_type)}</div>
    </div>
    <div class="jrd-section">
      <div class="jrd-label">Classification</div>
      <div class="jrd-value"><span class="jrd-badge">${_escapeHtml(scopeLabel)}</span></div>
    </div>
    <div class="jrd-section">
      <div class="jrd-label">Source</div>
      <div class="jrd-value">${_formatSourceHtml(rec)}</div>
    </div>
    <div class="jrd-section">
      <div class="jrd-label">Reasoning</div>
      <div class="jrd-value">${_formatReasoning(rec)}</div>
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
