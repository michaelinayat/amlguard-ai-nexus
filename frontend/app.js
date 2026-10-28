const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const API = '';
let strategy = null;
let currentScore = null;
let toastTimer = null;

function toast(message, isError = false) {
  const el = $('#toast');
  el.textContent = message;
  el.className = `toast show${isError ? ' error' : ''}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.className = 'toast'; }, 4200);
}
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function showView(name) {
  const allowed = ['dashboard','crypto','banking','datasets','alerts','cases','reports'];
  if (!allowed.includes(name)) name = 'dashboard';
  $$('.view').forEach(v => v.classList.toggle('active', v.id === `view-${name}`));
  $$('.nav-item[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === name));
  const titles = {dashboard:'Overview',crypto:'Crypto investigator',banking:'Card fraud lab',datasets:'Data readiness',alerts:'Alerts',cases:'Investigation cases',reports:'Reports'};
  $('#crumbCurrent').textContent = titles[name];
  $('#sidebar').classList.remove('open');
  window.location.hash = name;
}
$$('[data-view]').forEach(b => b.addEventListener('click', () => showView(b.dataset.view)));
$$('[data-goto]').forEach(b => b.addEventListener('click', () => showView(b.dataset.goto)));
$('#mobileMenu').addEventListener('click', () => $('#sidebar').classList.toggle('open'));
$('#dismissNotice').addEventListener('click', () => $('.notice-amber').classList.add('hidden'));

function setStatus(kind, status, ready, foot) {
  const isCrypto = kind === 'crypto';
  const value = $(`#${kind}StatusValue`);
  value.textContent = status;
  value.style.color = ready ? '#168562' : '#b17a25';
  $(`#${kind}StatusFoot`).textContent = foot;
  $(`#${kind}Dot`).style.background = ready ? '#25b48a' : '#d6a34d';
  $(`#${kind}StateDot`).className = `state-dot${ready ? ' ready' : ''}`;
  $(`#${kind}StateText`).textContent = ready ? 'Ready' : 'Needs setup';
  $(`#${kind}DatasetBadge`).textContent = ready ? 'FILES FOUND' : 'FILES MISSING';
  $(`#${kind}DatasetBadge`).className = `result-badge ${ready ? 'low' : 'medium'}`;
}
async function refreshStatus() {
  $('#lastUpdated').textContent = 'Refreshing…';
  try {
    const [healthRes, strategyRes] = await Promise.all([fetch(`${API}/health`), fetch(`${API}/real-data/strategy`)]);
    if (!healthRes.ok) throw new Error(`Health endpoint returned ${healthRes.status}`);
    if (!strategyRes.ok) throw new Error(`Strategy endpoint returned ${strategyRes.status}`);
    const health = await healthRes.json();
    strategy = await strategyRes.json();
    const crypto = strategy.cryptocurrency || {};
    const bank = strategy.banking || {};
    const cryptoReady = crypto.status === 'ready_to_ingest';
    const bankReady = bank.status === 'ready_to_ingest';
    setStatus('crypto', cryptoReady ? 'Files available' : 'Awaiting data', cryptoReady, cryptoReady ? 'Elliptic raw files detected' : '3 CSV files required');
    setStatus('bank', bankReady ? 'Files available' : 'Awaiting data', bankReady, bankReady ? 'Card-fraud CSV detected' : 'creditcard.csv required');
    const models = Number(crypto.model_trained === true) + Number(bank.model_trained === true);
    $('#modelCount').textContent = `${models} / 2`;
    $('#serviceStatus').textContent = health.status === 'ok' ? 'Online' : 'Unavailable';
    $('#serviceStatus').style.color = health.status === 'ok' ? '#168562' : '#bd4d4d';
    $('#serviceFoot').textContent = 'Connected to local FastAPI';
    $('#datasetTimestamp').textContent = new Date().toLocaleTimeString();
    $('#lastUpdated').textContent = `Updated ${new Date().toLocaleTimeString()}`;
    updateChecklist(cryptoReady, bankReady, models);
  } catch (err) {
    $('#serviceStatus').textContent = 'Offline';
    $('#serviceStatus').style.color = '#bd4d4d';
    $('#serviceFoot').textContent = 'Start FastAPI on port 8000';
    $('#lastUpdated').textContent = 'API not reachable';
    $('#cryptoStatusValue').textContent = 'Unavailable';
    $('#bankStatusValue').textContent = 'Unavailable';
    $('#cryptoStatusFoot').textContent = 'Cannot reach API';
    $('#bankStatusFoot').textContent = 'Cannot reach API';
    $('#datasetTimestamp').textContent = 'API offline';
    toast('Cannot reach the local API. Start Uvicorn, then refresh.', true);
  }
}
function updateChecklist(cryptoReady, bankReady, models) {
  const rows = $$('#checklist .check-row');
  const checks = [cryptoReady || bankReady, cryptoReady || bankReady, models > 0, true];
  rows.forEach((row, i) => {
    const state = row.querySelector('.check-state');
    if (checks[i]) { state.textContent = i === 3 ? 'Review required' : 'Detected'; state.className = 'check-state complete'; state.style.color = '#168562'; }
    else { state.textContent = 'Pending'; state.className = 'check-state pending'; state.style.color = ''; }
  });
}
function setBadge(selector, risk) {
  const el = $(selector);
  const normalized = String(risk || '').toLowerCase();
  el.textContent = normalized ? normalized.toUpperCase() : 'RESULT';
  el.className = `result-badge ${['low','medium','high'].includes(normalized) ? normalized : 'idle'}`;
}
function resultCard(data, task) {
  const probKey = task === 'crypto' ? 'model_probability_for_source_illicit_label' : 'model_probability_for_card_fraud_label';
  const prob = Number(data[probKey]);
  const hasProb = Number.isFinite(prob);
  const percent = hasProb ? `${(prob * 100).toFixed(2)}%` : 'N/A';
  const label = task === 'crypto' ? 'Probability for source illicit label' : 'Probability for card-fraud label';
  const extras = task === 'crypto'
    ? [['Transaction ID', data.transaction_id], ['Source label', data.source_label ?? 'Not provided'], ['Human review', data.human_review_required ? 'Required' : 'Not flagged']]
    : [['Task', 'Card fraud proxy'], ['Human review', data.human_review_required ? 'Required' : 'Not flagged'], ['Dataset', data.dataset || 'Credit-card fraud']];
  return `<div class="result-data"><div class="result-main"><div><strong>${escapeHtml(percent)}</strong><small>${escapeHtml(label)}</small></div><span class="result-badge ${escapeHtml(String(data.risk_band || '').toLowerCase())}">${escapeHtml(data.risk_band || 'UNAVAILABLE')}</span></div><div class="result-kv">${extras.map(([k,v])=>`<div><span>${escapeHtml(k)}</span><b>${escapeHtml(v)}</b></div>`).join('')}</div><div class="result-disclaimer">${escapeHtml(data.disclaimer || 'Research output only. This result is not proof of criminal activity and requires human review.')}</div><div class="button-row" style="margin-top:12px"><button class="btn btn-secondary" type="button" data-save-alert>Save this score as alert</button></div></div>`;
}
async function requestJson(url, options = {}) {
  let response;
  try { response = await fetch(url, options); }
  catch { throw new Error('Could not connect to the API. Is the local FastAPI server running?'); }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    let detail = payload.detail || payload.message || `Request failed with HTTP ${response.status}`;
    if (typeof detail === 'object') detail = JSON.stringify(detail);
    throw new Error(`${detail} (HTTP ${response.status})`);
  }
  return payload;
}
$('#cryptoForm').addEventListener('submit', async e => {
  e.preventDefault();
  const id = $('#txId').value.trim();
  if (!id) return;
  const result = $('#cryptoResult');
  result.innerHTML = '<div class="empty-result"><div class="spinner"></div><b>Requesting model score…</b><p>Contacting the local API.</p></div>';
  try {
    const data = await requestJson(`/real-data/elliptic/score/${encodeURIComponent(id)}`);
    const prob = Number(data.model_probability_for_source_illicit_label);
    currentScore = {title:`Elliptic transaction ${data.transaction_id}`,dataset:'elliptic',entity_ref:String(data.transaction_id),risk_band:data.risk_band,score:prob,score_type:'model_probability_for_source_illicit_label',source_label:String(data.source_label ?? 'not provided'),provenance:`GET /real-data/elliptic/score/${encodeURIComponent(id)}`};
    setBadge('#cryptoResultBadge', data.risk_band);
    result.innerHTML = resultCard(data, 'crypto');
    toast('Transaction score retrieved. Review the label and limitations.');
  } catch (err) {
    setBadge('#cryptoResultBadge', 'idle');
    result.innerHTML = `<div class="empty-result"><div class="empty-illustration">!</div><b>Could not score transaction</b><p>${escapeHtml(err.message)}</p></div>`;
    toast(err.message, true);
  }
});
$('#graphBtn').addEventListener('click', async () => {
  const id = $('#txId').value.trim();
  if (!id) { toast('Enter a transaction ID first.', true); return; }
  $('#graphResult').innerHTML = '<div class="graph-empty"><div class="spinner"></div><b>Loading graph neighborhood…</b></div>';
  try {
    const data = await requestJson(`/real-data/elliptic/graph/${encodeURIComponent(id)}`);
    const incoming = data.incoming_neighbors_sample || [];
    const outgoing = data.outgoing_neighbors_sample || [];
    $('#graphResult').innerHTML = `<div class="graph-loaded"><div class="graph-stat"><span>Transaction</span><b style="font-size:12px;overflow-wrap:anywhere">${escapeHtml(data.transaction_id)}</b></div><div class="graph-stat"><span>Incoming degree</span><b>${Number(data.in_degree)||0}</b></div><div class="graph-stat"><span>Outgoing degree</span><b>${Number(data.out_degree)||0}</b></div></div><div class="neighbor-columns"><div class="neighbor-list"><h3>Incoming neighbors (${incoming.length}${incoming.length===20?'+':''})</h3><ul>${incoming.length ? incoming.map(n=>`<li>${escapeHtml(n)}</li>`).join('') : '<li>No sampled neighbors</li>'}</ul></div><div class="neighbor-list"><h3>Outgoing neighbors (${outgoing.length}${outgoing.length===20?'+':''})</h3><ul>${outgoing.length ? outgoing.map(n=>`<li>${escapeHtml(n)}</li>`).join('') : '<li>No sampled neighbors</li>'}</ul></div></div><div class="result-disclaimer">${escapeHtml(data.interpretation || 'Graph relationships are investigative context, not proof of criminal activity.')}</div>`;
    toast('Graph neighborhood loaded.');
  } catch (err) {
    $('#graphResult').innerHTML = `<div class="graph-empty"><b>Graph lookup unavailable</b><p>${escapeHtml(err.message)}</p></div>`;
    toast(err.message, true);
  }
});
$('#bankForm').addEventListener('submit', async e => {
  e.preventDefault();
  let features;
  try { features = JSON.parse($('#bankFeatures').value); }
  catch { toast('Feature input must be valid JSON.', true); return; }
  if (!features || Array.isArray(features) || typeof features !== 'object' || Object.values(features).some(v => typeof v !== 'number' || !Number.isFinite(v))) {
    toast('Provide a JSON object containing only finite numeric values.', true); return;
  }
  $('#bankResult').innerHTML = '<div class="empty-result"><div class="spinner"></div><b>Scoring feature vector…</b><p>Contacting the local API.</p></div>';
  try {
    const data = await requestJson('/real-data/banking/score', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({features})});
    const prob = Number(data.model_probability_for_card_fraud_label);
    currentScore = {title:'Card-fraud model score',dataset:'card_fraud',entity_ref:'analyst-submitted-feature-vector',risk_band:data.risk_band,score:prob,score_type:'model_probability_for_card_fraud_label',source_label:'card_fraud_label',provenance:'POST /real-data/banking/score; analyst-submitted numeric feature vector'};
    setBadge('#bankResultBadge', data.risk_band);
    $('#bankResult').innerHTML = resultCard(data, 'banking');
    toast('Card-fraud score retrieved. This is not an AML score.');
  } catch (err) {
    setBadge('#bankResultBadge', 'idle');
    $('#bankResult').innerHTML = `<div class="empty-result"><div class="empty-illustration">!</div><b>Could not score feature vector</b><p>${escapeHtml(err.message)}</p></div>`;
    toast(err.message, true);
  }
});
$('#resetBank').addEventListener('click', () => { $('#bankFeatures').value = '{\n  "Time": 0,\n  "V1": 0,\n  "V2": 0,\n  "V3": 0,\n  "Amount": 100\n}'; });
$('#refreshBtn').addEventListener('click', refreshStatus);
$('#refreshDataBtn').addEventListener('click', refreshStatus);
const spinStyle = document.createElement('style');
spinStyle.textContent = '.spinner{width:26px;height:26px;border:3px solid #ece9ff;border-top-color:#7565e8;border-radius:50%;animation:spin .7s linear infinite;margin-bottom:14px}@keyframes spin{to{transform:rotate(360deg)}}.notice.hidden{display:none}.check-state.complete{color:#168562}';
document.head.appendChild(spinStyle);
const initialView = window.location.hash.replace('#','');
showView(['dashboard','crypto','banking','datasets','alerts','cases','reports'].includes(initialView) ? initialView : 'dashboard');
refreshStatus();


// Investigation workspace: all records are persisted by the local FastAPI/SQLite backend.
async function loadCases() {
  const el = $('#casesTable'); if (!el) return;
  el.innerHTML = '<p class="field-hint">Loading cases…</p>';
  try {
    const rows = await requestJson('/workspace/cases');
    el.innerHTML = rows.length ? `<table class="data-table"><thead><tr><th>Case</th><th>Entity</th><th>Priority</th><th>Status</th><th>Update</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>#${r.id} ${escapeHtml(r.title)}</b><small>${escapeHtml(r.dataset)} · ${escapeHtml((r.summary||'').slice(0,90))}</small></td><td><code>${escapeHtml(r.entity_ref)}</code></td><td><span class="tag tag-${r.priority==='critical'||r.priority==='high'?'amber':'blue'}">${escapeHtml(r.priority)}</span></td><td>${escapeHtml(r.status)}</td><td><select data-case-status="${r.id}" aria-label="Update case status"><option value="open" ${r.status==='open'?'selected':''}>Open</option><option value="in_review" ${r.status==='in_review'?'selected':''}>In review</option><option value="closed" ${r.status==='closed'?'selected':''}>Closed</option></select></td></tr>`).join('')}</tbody></table>` : '<div class="empty-result"><b>No cases yet</b><p>Create a case using a real source reference. No demo cases are generated.</p></div>';
  } catch(e) { el.innerHTML = `<p class="error-text">${escapeHtml(e.message)}</p>`; }
}
async function loadAlerts() {
  const el = $('#alertsTable'); if (!el) return;
  el.innerHTML = '<p class="field-hint">Loading saved alerts…</p>';
  try {
    const rows = await requestJson('/workspace/alerts');
    $('#alertCountLabel').textContent = `${rows.length} saved alert${rows.length===1?'':'s'} · from actual model responses or documented analyst records`;
    $('#navAlertCount').textContent = rows.filter(r=>r.status==='new').length;
    const filter = $('#alertFilter').value;
    const shown = filter ? rows.filter(r=>r.status===filter) : rows;
    el.innerHTML = shown.length ? `<table class="data-table"><thead><tr><th>Alert</th><th>Score</th><th>Provenance</th><th>Status</th><th>Update</th></tr></thead><tbody>${shown.map(r=>`<tr><td><b>#${r.id} ${escapeHtml(r.title)}</b><small>${escapeHtml(r.dataset)} · ${escapeHtml(r.entity_ref)} · label: ${escapeHtml(r.source_label)}</small><small>${escapeHtml(r.notes||'No analyst notes')}</small></td><td><span class="result-badge ${String(r.risk_band).toLowerCase()}">${escapeHtml(r.risk_band)}</span><small>${(Number(r.score)*100).toFixed(2)}% · ${escapeHtml(r.score_type)}</small></td><td><small>${escapeHtml(r.provenance)}</small></td><td>${escapeHtml(r.status)}</td><td><select data-alert-status="${r.id}" aria-label="Update alert status"><option value="new" ${r.status==='new'?'selected':''}>New</option><option value="reviewing" ${r.status==='reviewing'?'selected':''}>Reviewing</option><option value="escalated" ${r.status==='escalated'?'selected':''}>Escalated</option><option value="dismissed" ${r.status==='dismissed'?'selected':''}>Dismissed</option></select></td></tr>`).join('')}</tbody></table>` : '<div class="empty-result"><b>No saved alerts</b><p>Run a real-data score and use “Save this score as alert” after a successful response. No alerts are fabricated.</p></div>';
  } catch(e) { el.innerHTML = `<p class="error-text">${escapeHtml(e.message)}</p>`; }
}
async function loadReports() {
  try {
    const [summary, evals] = await Promise.all([requestJson('/workspace/reports/summary'),requestJson('/workspace/reports/evaluations')]);
    $('#reportCases').textContent = summary.recent_cases ? Object.values((summary.case_breakdown||[]).reduce((a,r)=>(a[r.status]=(a[r.status]||0)+r.count,a),{})).reduce((a,b)=>a+b,0) : '0';
    $('#reportAlerts').textContent = Object.values((summary.alert_breakdown||[]).reduce((a,r)=>(a[r.status]=(a[r.status]||0)+r.count,a),{})).reduce((a,b)=>a+b,0);
    $('#reportTime').textContent = new Date(summary.generated_at).toLocaleTimeString();
    $('#evaluationFiles').innerHTML = Object.entries(evals).map(([key,v])=>`<div class="eval-row"><span><b>${key==='elliptic'?'Elliptic cryptocurrency':'Card-fraud research'}</b><small>${escapeHtml(v.file)}</small></span><span class="result-badge ${v.status==='available'?'low':'medium'}">${escapeHtml(v.status.replaceAll('_',' '))}</span>${v.status==='available'?`<details><summary>View metrics</summary><pre>${escapeHtml(JSON.stringify(v.metrics,null,2))}</pre></details>`:`<small>${escapeHtml(v.message||'Evaluation artifact unavailable')}</small>`}</div>`).join('');
  } catch(e) { $('#evaluationFiles').innerHTML = `<p class="error-text">${escapeHtml(e.message)}</p>`; }
}
$('#caseForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  const body = {title:$('#caseTitle').value.trim(),dataset:$('#caseDataset').value,entity_ref:$('#caseEntity').value.trim(),priority:$('#casePriority').value,summary:$('#caseSummary').value.trim()};
  try { await requestJson('/workspace/cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); $('#caseForm').reset(); toast('Case saved to the local workspace.'); await loadCases(); await loadReports(); }
  catch(err) { toast(err.message,true); }
});
document.addEventListener('click', async e => {
  const btn = e.target.closest('[data-save-alert]'); if (!btn) return;
  if (!currentScore || !Number.isFinite(currentScore.score) || currentScore.score < 0 || currentScore.score > 1) { toast('No valid real-data score is available to save.',true); return; }
  const notes = window.prompt('Optional analyst notes (do not state an unverified crime):',''); if (notes === null) return;
  const body = {...currentScore,notes};
  try { await requestJson('/workspace/alerts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); toast('Score-backed alert saved with provenance.'); await loadAlerts(); await loadReports(); }
  catch(err) { toast(err.message,true); }
});
document.addEventListener('change', async e => {
  const c = e.target.closest('[data-case-status]');
  if (c) { try { await requestJson(`/workspace/cases/${c.dataset.caseStatus}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:c.value})}); toast('Case status updated.'); await loadCases(); await loadReports(); } catch(err){toast(err.message,true);} }
  const a = e.target.closest('[data-alert-status]');
  if (a) { try { await requestJson(`/workspace/alerts/${a.dataset.alertStatus}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:a.value})}); toast('Alert status updated.'); await loadAlerts(); await loadReports(); } catch(err){toast(err.message,true);} }
});
$('#refreshAlertsBtn')?.addEventListener('click',loadAlerts);
$('#refreshCasesBtn')?.addEventListener('click',loadCases);
$('#refreshReportsBtn')?.addEventListener('click',loadReports);
$('#alertFilter')?.addEventListener('change',loadAlerts);
const workspaceCss = document.createElement('style');
workspaceCss.textContent = `.inline-select, .data-table select{border:1px solid #dfe5ed;border-radius:7px;background:#fff;color:#526074;padding:8px;font:10px 'DM Sans',sans-serif}.table-wrap{width:100%;overflow:auto;margin-top:16px}.data-table{width:100%;border-collapse:collapse;min-width:650px;text-align:left}.data-table th{font-size:9px;letter-spacing:.5px;text-transform:uppercase;color:#8e99a9;background:#f8f9fc;padding:12px;border-bottom:1px solid #e9edf3}.data-table td{font-size:10px;color:#536176;padding:13px 12px;border-bottom:1px solid #eef1f5;vertical-align:top;max-width:300px}.data-table td b{display:block;color:#334157;font-size:10px;margin-bottom:4px}.data-table td small{display:block;color:#929dad;font-size:9px;line-height:1.6;margin-top:3px;max-width:300px;overflow-wrap:anywhere}.data-table code{font-size:9px;overflow-wrap:anywhere}.export-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:18px}.eval-row{display:grid;grid-template-columns:minmax(150px,1fr) auto;gap:10px;align-items:center;padding:14px 0;border-bottom:1px solid #eef1f5}.eval-row b,.eval-row small{display:block}.eval-row b{font-size:10px}.eval-row small{font-size:9px;color:#929dad;margin-top:5px;overflow-wrap:anywhere}.eval-row details{grid-column:1/-1;font-size:10px}.eval-row pre{white-space:pre-wrap;overflow:auto;background:#f7f8fb;padding:12px;border-radius:7px;font-size:10px}.error-text{font-size:11px;color:#bd4d4d}.report-metrics{margin-bottom:18px}@media(max-width:700px){.export-grid{grid-template-columns:1fr}.eval-row{grid-template-columns:1fr auto}}`;
document.head.appendChild(workspaceCss);
// Load only persisted records; no sample cases, alerts, or model metrics are generated.
loadCases(); loadAlerts(); loadReports();
