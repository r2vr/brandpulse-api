"""The public landing page served at ``/``.

A REST API has no natural home page, so the root used to 404. This gives any
visitor — recruiter, collaborator, curious user — a self-contained overview of
what BrandPulse does and a clickable map of every live endpoint. Pure inline
HTML/CSS keeps it dependency-free and instantly served.
"""

from __future__ import annotations

REPO_URL = "https://github.com/r2vr/brandpulse-api"

_PAGE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BrandPulse — brand monitoring & content curation API</title>
<meta name="description" content="BrandPulse fans out across content sources, normalises everything into one model, then deduplicates and ranks results into a curated shortlist.">
<style>
  :root {{
    --bg:#0b0d12; --panel:#13161d; --line:#222733; --ink:#e8ecf3;
    --muted:#9aa4b2; --accent:#7c9cff; --accent2:#56d3a0; --code:#0f1218;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }}
  a {{ color:var(--accent); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:48px 24px 80px; }}
  header .pill {{
    display:inline-block; font-size:12px; letter-spacing:.08em; text-transform:uppercase;
    color:var(--accent2); border:1px solid var(--line); border-radius:999px; padding:4px 12px;
  }}
  h1 {{ font-size:42px; margin:18px 0 6px; letter-spacing:-.02em; }}
  .tagline {{ font-size:19px; color:var(--muted); margin:0 0 28px; max-width:640px; }}
  .cta {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:40px; }}
  .btn {{
    display:inline-block; padding:11px 18px; border-radius:10px; font-weight:600;
    border:1px solid var(--line);
  }}
  .btn.primary {{ background:var(--accent); color:#0b0d12; border-color:var(--accent); }}
  .btn.primary:hover {{ filter:brightness(1.08); text-decoration:none; }}
  .btn.ghost:hover {{ border-color:var(--accent); text-decoration:none; }}
  h2 {{ font-size:14px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted);
        margin:44px 0 16px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  @media (max-width:620px) {{ .grid {{ grid-template-columns:1fr; }} h1 {{ font-size:34px; }} }}
  .ep {{
    display:block; background:var(--panel); border:1px solid var(--line); border-radius:12px;
    padding:14px 16px;
  }}
  .ep:hover {{ border-color:var(--accent); text-decoration:none; }}
  .ep .verb {{ font:12px ui-monospace,Menlo,monospace; color:var(--accent2); }}
  .ep .path {{ font:14px ui-monospace,Menlo,monospace; color:var(--ink); margin-left:6px; }}
  .ep .desc {{ display:block; color:var(--muted); font-size:14px; margin-top:6px; }}
  pre {{
    background:var(--code); border:1px solid var(--line); border-radius:12px;
    padding:16px; overflow:auto; font:13px/1.6 ui-monospace,Menlo,monospace; color:#cdd6e4;
  }}
  .flow {{ color:var(--muted); font:13px ui-monospace,Menlo,monospace; white-space:pre-wrap; }}
  footer {{ margin-top:56px; padding-top:24px; border-top:1px solid var(--line);
            color:var(--muted); font-size:14px; }}
  .tags {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }}
  .tag {{ font-size:12px; color:var(--muted); border:1px solid var(--line);
          border-radius:6px; padding:3px 9px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <span class="pill">Live API · production</span>
    <h1>BrandPulse</h1>
    <p class="tagline">A brand-monitoring &amp; content-curation engine. Point it at a set of
      keywords; it fans out across content sources, normalises everything into one model, then
      deduplicates and ranks the results into a curated, explainable shortlist.</p>
    <div class="cta">
      <a class="btn primary" href="/docs">Interactive API docs →</a>
      <a class="btn ghost" href="/monitor?q=acme&amp;limit=5">Try a live query</a>
      <a class="btn ghost" href="{repo}">Source on GitHub</a>
    </div>
  </header>

  <h2>Live endpoints</h2>
  <div class="grid">
    <a class="ep" href="/health"><span class="verb">GET</span><span class="path">/health</span>
      <span class="desc">Liveness + environment.</span></a>
    <a class="ep" href="/sources"><span class="verb">GET</span><span class="path">/sources</span>
      <span class="desc">Registered source connectors.</span></a>
    <a class="ep" href="/monitor?q=acme&amp;limit=5"><span class="verb">GET</span><span class="path">/monitor</span>
      <span class="desc">Curated, ranked results for your terms.</span></a>
    <a class="ep" href="/campaigns"><span class="verb">GET</span><span class="path">/campaigns</span>
      <span class="desc">Saved monitoring campaigns (persisted).</span></a>
    <a class="ep" href="/docs"><span class="verb">UI</span><span class="path">/docs</span>
      <span class="desc">Swagger — try every endpoint in the browser.</span></a>
    <a class="ep" href="/redoc"><span class="verb">UI</span><span class="path">/redoc</span>
      <span class="desc">ReDoc — clean reference documentation.</span></a>
  </div>

  <h2>Curl it</h2>
  <pre># curated shortlist for a brand
curl "{base}/monitor?q=acme&amp;limit=5"

# create a campaign (persisted in Postgres)
curl -X POST {base}/campaigns \\
  -H "Content-Type: application/json" \\
  -d '{{"name":"my-brand","description":"watch","terms":["acme","widget"]}}'

# read it back
curl {base}/campaigns</pre>

  <h2>How it works</h2>
  <p class="flow">domain/   pure models, no I/O          (the currency: ContentItem)
sources/  SourceConnector + registry   (RSS, Hacker News, Reddit, Mastodon)
curation/ explainable scoring + dedupe (recency + relevance signals)
service   orchestration / fan-out      (shared by every adapter)
db/       SQLAlchemy 2.0 async + repos  (Postgres in prod, SQLite locally)
api/      this FastAPI adapter</p>
  <p style="color:var(--muted);font-size:14px;margin-top:14px">Every platform is reduced to one
    contract — <em>given a query, yield normalised items</em> — so adding a new source is a
    localised change, never a refactor.</p>

  <footer>
    <div>BrandPulse · MIT licensed · <a href="{repo}">github.com/r2vr/brandpulse-api</a></div>
    <div class="tags">
      <span class="tag">FastAPI</span><span class="tag">SQLAlchemy 2.0 async</span>
      <span class="tag">Alembic</span><span class="tag">Pydantic v2</span>
      <span class="tag">PostgreSQL</span><span class="tag">Docker</span>
    </div>
  </footer>
</div>
</body>
</html>
"""


def render_landing(base_url: str) -> str:
    """Return the landing HTML with example URLs bound to the live host."""
    return _PAGE.format(base=base_url.rstrip("/"), repo=REPO_URL)
