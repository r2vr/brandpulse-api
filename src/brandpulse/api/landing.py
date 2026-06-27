"""The interactive dashboard served at ``/``.

A REST API has no natural home page, so the root used to 404. This serves a
self-contained single-page app — no build step, no dependencies — that drives
every live endpoint from the browser: health, sources, the curated monitor
query, and campaign create/list against Postgres. It is the visual proof that
the whole stack works end to end.
"""

from __future__ import annotations

REPO_URL = "https://github.com/r2vr/brandpulse-api"

_PAGE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BrandPulse — live dashboard</title>
<style>
  :root {
    --bg:#0b0d12; --panel:#13161d; --panel2:#171b24; --line:#232936; --ink:#e8ecf3;
    --muted:#9aa4b2; --accent:#7c9cff; --good:#56d3a0; --warn:#ffcc66; --bad:#ff7a7a;
    --code:#0f1218;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
  .wrap { max-width:1080px; margin:0 auto; padding:28px 22px 80px; }
  header { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  header h1 { font-size:26px; margin:0; letter-spacing:-.02em; }
  header .sub { color:var(--muted); font-size:14px; }
  .spacer { flex:1; }
  .chip { display:inline-flex; align-items:center; gap:7px; font-size:13px; color:var(--muted);
    border:1px solid var(--line); border-radius:999px; padding:5px 12px; }
  .dot { width:8px; height:8px; border-radius:50%; background:var(--muted); }
  .dot.ok { background:var(--good); box-shadow:0 0 0 3px rgba(86,211,160,.18); }
  .dot.err { background:var(--bad); box-shadow:0 0 0 3px rgba(255,122,122,.18); }
  .row { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:22px; }
  @media (max-width:840px){ .row { grid-template-columns:1fr; } }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px; }
  .card h2 { font-size:13px; letter-spacing:.09em; text-transform:uppercase; color:var(--muted);
    margin:0 0 14px; }
  label { display:block; font-size:13px; color:var(--muted); margin:0 0 6px; }
  input, textarea { width:100%; background:var(--code); border:1px solid var(--line); color:var(--ink);
    border-radius:9px; padding:10px 12px; font:14px inherit; }
  input:focus, textarea:focus { outline:none; border-color:var(--accent); }
  .btn { cursor:pointer; border:1px solid var(--accent); background:var(--accent); color:#0b0d12;
    font-weight:650; border-radius:9px; padding:10px 16px; font-size:14px; }
  .btn:hover { filter:brightness(1.07); }
  .btn:disabled { opacity:.5; cursor:default; filter:none; }
  .btn.ghost { background:transparent; color:var(--ink); border-color:var(--line); }
  .field { margin-bottom:12px; }
  .inline { display:flex; gap:10px; align-items:end; }
  .inline .grow { flex:1; }
  .pills { display:flex; gap:7px; flex-wrap:wrap; }
  .pill { font-size:12px; color:var(--ink); background:var(--panel2); border:1px solid var(--line);
    border-radius:7px; padding:4px 10px; }
  .muted { color:var(--muted); font-size:13px; }
  .results { display:flex; flex-direction:column; gap:10px; margin-top:6px; }
  .item { background:var(--panel2); border:1px solid var(--line); border-radius:11px; padding:12px 14px; }
  .item .top { display:flex; align-items:center; gap:8px; margin-bottom:4px; }
  .src { font:11px ui-monospace,Menlo,monospace; text-transform:uppercase; letter-spacing:.05em;
    color:var(--good); border:1px solid var(--line); border-radius:6px; padding:1px 7px; }
  .score { margin-left:auto; font:12px ui-monospace,Menlo,monospace; color:var(--accent); }
  .item .title { font-size:14px; }
  .bars { display:flex; gap:14px; margin-top:8px; }
  .bar { flex:1; }
  .bar .lab { font-size:11px; color:var(--muted); display:flex; justify-content:space-between; }
  .track { height:6px; background:var(--code); border-radius:4px; overflow:hidden; margin-top:3px; }
  .fill { height:100%; background:linear-gradient(90deg,#5570ff,#7c9cff); }
  .fill.green { background:linear-gradient(90deg,#2fa06f,#56d3a0); }
  .camp { display:flex; align-items:center; gap:10px; padding:9px 0; border-top:1px solid var(--line); }
  .camp:first-child { border-top:none; }
  .camp .id { font:12px ui-monospace,Menlo,monospace; color:var(--muted); }
  .toast { font-size:13px; margin-top:10px; min-height:18px; }
  .toast.ok { color:var(--good); } .toast.err { color:var(--bad); }
  footer { margin-top:30px; color:var(--muted); font-size:13px; display:flex; gap:14px; flex-wrap:wrap; }
  .skel { color:var(--muted); font-size:13px; padding:10px 0; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>BrandPulse</h1>
    <span class="sub">live dashboard</span>
    <span class="spacer"></span>
    <span class="chip"><span id="healthDot" class="dot"></span><span id="healthText">checking…</span></span>
    <a class="chip" href="/docs">API docs ↗</a>
    <a class="chip" href="__REPO__">GitHub ↗</a>
  </header>
  <p class="muted" style="margin:10px 0 0">Point it at keywords; it fans out across content sources,
    normalises everything into one model, then deduplicates and ranks the results. Everything below is
    live — each control calls the real API.</p>

  <div class="row">
    <!-- MONITOR -->
    <div class="card">
      <h2>① Monitor &amp; curate</h2>
      <div class="inline">
        <div class="grow">
          <label for="terms">Brands / keywords (comma-separated)</label>
          <input id="terms" value="acme, widget" placeholder="acme, openai, ...">
        </div>
        <button class="btn" id="runBtn" onclick="runMonitor()">Search</button>
      </div>
      <div class="muted" style="margin:8px 0 4px">Sources:
        <span id="sources" class="pills" style="display:inline-flex"></span></div>
      <div id="monitorOut" class="results"></div>
    </div>

    <!-- CAMPAIGNS -->
    <div class="card">
      <h2>② Campaigns <span class="muted" style="text-transform:none;letter-spacing:0">· persisted in Postgres</span></h2>
      <div class="field">
        <label for="cname">Name</label>
        <input id="cname" value="my-brand" placeholder="campaign name">
      </div>
      <div class="field">
        <label for="cterms">Terms (comma-separated)</label>
        <input id="cterms" value="acme, widget" placeholder="acme, widget">
      </div>
      <div class="inline">
        <button class="btn" id="saveBtn" onclick="createCampaign()">Save campaign</button>
        <button class="btn ghost" onclick="loadCampaigns()">Refresh list</button>
      </div>
      <div id="campToast" class="toast"></div>
      <div id="campOut" style="margin-top:6px"></div>
    </div>
  </div>

  <footer>
    <span>BrandPulse · MIT</span>
    <span>FastAPI · SQLAlchemy 2.0 async · Alembic · Pydantic v2 · PostgreSQL · Docker</span>
  </footer>
</div>

<script>
const $ = (id) => document.getElementById(id);
const pct = (x) => Math.round((x || 0) * 100);
const esc = (s) => (s || "").replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

async function health() {
  try {
    const r = await fetch('/health'); const j = await r.json();
    $('healthDot').className = 'dot ok';
    $('healthText').textContent = j.status + ' · ' + j.environment;
  } catch (e) {
    $('healthDot').className = 'dot err'; $('healthText').textContent = 'offline';
  }
}

async function loadSources() {
  try {
    const r = await fetch('/sources'); const j = await r.json();
    $('sources').innerHTML = j.sources.map(s => `<span class="pill">${esc(s)}</span>`).join('');
  } catch (e) { $('sources').innerHTML = '<span class="muted">—</span>'; }
}

async function runMonitor() {
  const raw = $('terms').value.split(',').map(s => s.trim()).filter(Boolean);
  if (!raw.length) return;
  $('runBtn').disabled = true;
  $('monitorOut').innerHTML = '<div class="skel">Fanning out across sources…</div>';
  try {
    const qs = raw.map(t => 'q=' + encodeURIComponent(t)).join('&');
    const r = await fetch('/monitor?' + qs + '&limit=12');
    const j = await r.json();
    if (!j.items || !j.items.length) { $('monitorOut').innerHTML = '<div class="skel">No results.</div>'; return; }
    $('monitorOut').innerHTML = j.items.map(it => `
      <div class="item">
        <div class="top">
          <span class="src">${esc(it.source)}</span>
          ${it.author ? '<span class="muted">@' + esc(it.author) + '</span>' : ''}
          <span class="score">score ${(it.score ?? 0).toFixed(3)}</span>
        </div>
        <div class="title"><a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)}</a></div>
        <div class="bars">
          <div class="bar"><div class="lab"><span>relevance</span><span>${pct(it.signals?.relevance)}%</span></div>
            <div class="track"><div class="fill" style="width:${pct(it.signals?.relevance)}%"></div></div></div>
          <div class="bar"><div class="lab"><span>recency</span><span>${pct(it.signals?.recency)}%</span></div>
            <div class="track"><div class="fill green" style="width:${pct(it.signals?.recency)}%"></div></div></div>
        </div>
      </div>`).join('');
  } catch (e) {
    $('monitorOut').innerHTML = '<div class="toast err">Error: ' + esc(String(e)) + '</div>';
  } finally { $('runBtn').disabled = false; }
}

async function loadCampaigns() {
  try {
    const r = await fetch('/campaigns'); const list = await r.json();
    if (!list.length) { $('campOut').innerHTML = '<div class="skel">No campaigns yet — create one above.</div>'; return; }
    $('campOut').innerHTML = list.map(c => `
      <div class="camp">
        <span class="id">#${c.id}</span>
        <strong>${esc(c.name)}</strong>
        <span class="pills">${(c.terms||[]).map(t => '<span class="pill">' + esc(t) + '</span>').join('')}</span>
      </div>`).join('');
  } catch (e) { $('campOut').innerHTML = '<div class="toast err">Could not load campaigns.</div>'; }
}

async function createCampaign() {
  const name = $('cname').value.trim();
  const terms = $('cterms').value.split(',').map(s => s.trim()).filter(Boolean);
  const t = $('campToast');
  if (!name || !terms.length) { t.className = 'toast err'; t.textContent = 'Name and at least one term are required.'; return; }
  $('saveBtn').disabled = true; t.className = 'toast'; t.textContent = 'Saving…';
  try {
    const r = await fetch('/campaigns', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ name, description:'created from dashboard', terms })
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const c = await r.json();
    t.className = 'toast ok'; t.textContent = '✓ Saved campaign #' + c.id + ' — persisted in Postgres.';
    loadCampaigns();
  } catch (e) {
    t.className = 'toast err'; t.textContent = 'Error: ' + e.message;
  } finally { $('saveBtn').disabled = false; }
}

health(); loadSources(); runMonitor(); loadCampaigns();
</script>
</body>
</html>
"""


def render_landing(base_url: str) -> str:  # noqa: ARG001 — kept for signature stability
    """Return the dashboard HTML. ``base_url`` is unused: the page uses
    relative URLs so it works on any host without server-side templating."""
    return _PAGE.replace("__REPO__", REPO_URL)
