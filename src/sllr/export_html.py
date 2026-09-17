"""
Export lessons learned to a single HTML file with expandable cards and client-side
filtering (Phase, Technical Block, Status).
"""
import json
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT


def _escape(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_html_string(
    lessons: list[dict[str, Any]],
    title: str = "Lessons Learned Registry",
) -> str:
    """Build the HTML report as a string (expandable cards + filters). Use for file export or embedding."""
    lessons_data = [{k: (v or "") for k, v in r.items()} for r in lessons]
    lessons_json = json.dumps(lessons_data).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)}</title>
  <style>
    :root {{
      --bg: #0f1419;
      --card: #1a2332;
      --border: #2d3a4d;
      --text: #e6edf3;
      --muted: #8b949e;
      --accent: #58a6ff;
      --accent-hover: #79b8ff;
      --success: #3fb950;
      --warning: #d29922;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 1rem;
      line-height: 1.5;
    }}
    h1 {{
      font-size: 1.5rem;
      margin: 0 0 1rem 0;
      color: var(--text);
    }}
    .filters {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
      margin-bottom: 1.25rem;
      padding: 0.75rem;
      background: var(--card);
      border-radius: 8px;
      border: 1px solid var(--border);
    }}
    .filters label {{
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.875rem;
      color: var(--muted);
    }}
    .filters select {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.35rem 0.6rem;
      font-size: 0.875rem;
      min-width: 120px;
    }}
    .filters select:focus {{
      outline: none;
      border-color: var(--accent);
    }}
    .count {{
      margin-left: auto;
      font-size: 0.875rem;
      color: var(--muted);
    }}
    .count strong {{ color: var(--text); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1rem;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      transition: border-color 0.15s;
    }}
    .card:hover {{ border-color: var(--accent); }}
    .card-header {{
      padding: 0.85rem 1rem;
      cursor: pointer;
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      user-select: none;
    }}
    .card-header:focus {{
      outline: none;
    }}
    .card-toggle {{
      flex-shrink: 0;
      width: 20px;
      height: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--border);
      border-radius: 4px;
      font-size: 0.75rem;
      transition: transform 0.2s;
    }}
    .card.expanded .card-toggle {{ transform: rotate(90deg); }}
    .card-id {{
      font-size: 0.75rem;
      color: var(--accent);
      font-weight: 600;
    }}
    .card-title {{
      font-size: 0.95rem;
      font-weight: 500;
      margin: 0.2rem 0 0 0;
      color: var(--text);
    }}
    .card-meta {{
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 0.35rem;
    }}
    .card-body {{
      display: none;
      padding: 0 1rem 1rem 1rem;
      border-top: 1px solid var(--border);
    }}
    .card.expanded .card-body {{ display: block; }}
    .card-body dl {{
      margin: 0;
      font-size: 0.875rem;
    }}
    .card-body dt {{
      color: var(--muted);
      font-weight: 500;
      margin-top: 0.5rem;
      margin-bottom: 0.15rem;
    }}
    .card-body dd {{
      margin: 0;
      color: var(--text);
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .badge {{
      display: inline-block;
      font-size: 0.7rem;
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      margin-right: 0.25rem;
      margin-top: 0.25rem;
    }}
    .badge-draft {{ background: var(--muted); color: var(--bg); }}
    .badge-approved {{ background: var(--accent); color: var(--bg); }}
    .badge-embedded {{ background: var(--success); color: var(--bg); }}
    .no-results {{
      padding: 2rem;
      text-align: center;
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <h1>{_escape(title)}</h1>
  <div class="filters">
    <label>Phase <select id="filter-phase"><option value="">All</option></select></label>
    <label>Technical Block <select id="filter-technical-block"><option value="">All</option></select></label>
    <label>Status <select id="filter-status"><option value="">All</option></select></label>
    <label>Implementation <select id="filter-implementation"><option value="">All</option></select></label>
    <span class="count">Showing <strong id="visible-count">0</strong> of <strong id="total-count">0</strong> lessons</span>
  </div>
  <div id="grid" class="grid"></div>
  <div id="no-results" class="no-results" style="display:none;">No lessons match the selected filters.</div>

  <script type="application/json" id="lessons-data">{lessons_json}</script>
  <script>
    const lessons = JSON.parse(document.getElementById('lessons-data').textContent);
    const grid = document.getElementById('grid');
    const noResults = document.getElementById('no-results');
    const visibleCountEl = document.getElementById('visible-count');
    const totalCountEl = document.getElementById('total-count');

    function unique(values) {{
      return [...new Set(values)].filter(Boolean).sort();
    }}

    function populateFilters() {{
      const phases = unique(lessons.map(l => l['Project Phase']));
      const technicalBlocks = unique(lessons.map(l => l['Technical Block']));
      const statuses = unique(lessons.map(l => l['Status']));
      const implementationStatuses = unique(lessons.map(l => l['Implementation Status']));
      const addOptions = (id, values) => {{
        const sel = document.getElementById(id);
        values.forEach(v => {{
          const opt = document.createElement('option');
          opt.value = v;
          opt.textContent = v;
          sel.appendChild(opt);
        }});
      }};
      addOptions('filter-phase', phases);
      addOptions('filter-technical-block', technicalBlocks);
      addOptions('filter-status', statuses);
      addOptions('filter-implementation', implementationStatuses);
      totalCountEl.textContent = lessons.length;
    }}

    function escapeHtml(s) {{
      if (!s) return '';
      const div = document.createElement('div');
      div.textContent = s;
      return div.innerHTML;
    }}

    function statusClass(s) {{
      if (!s) return '';
      return 'badge-' + String(s).toLowerCase().replace(/\\s/g, '-');
    }}

    function renderCard(lesson) {{
      const id = escapeHtml(lesson['Lesson ID'] || '');
      const title = escapeHtml(lesson['Title'] || '');
      const phase = escapeHtml(lesson['Project Phase'] || '');
      const techBlock = escapeHtml(lesson['Technical Block'] || '');
      const status = lesson['Status'] || '';
      const statusCls = statusClass(status);
      const fields = [
        ['Technical Block', lesson['Technical Block']],
        ['Event Description', lesson['Event Description'] || lesson['What Happened']],
        ['Root Cause', lesson['Root Cause']],
        ['Impact', lesson['Impact']],
        ['Lesson Learned', lesson['Lesson Learned']],
        ['Recommendation', lesson['Recommendation']],
        ['Implementation Owner', lesson['Implementation Owner']],
        ['Implementation Due Date', lesson['Implementation Due Date'] || lesson['Recommendation Due Date']],
        ['Implementation Status', lesson['Implementation Status']],
        ['Keywords', lesson['Keywords']],
        ['Owner', lesson['Owner']],
        ['Created', lesson['Created Date']],
        ['Modified', lesson['Modified Date']]
      ].filter(([, v]) => v);
      const bodyRows = fields.map(([k, v]) => `<dt>${{escapeHtml(k)}}</dt><dd>${{escapeHtml(String(v))}}</dd>`).join('');
      const implStatus = lesson['Implementation Status'] || '';
      return `
        <div class="card" data-phase="${{escapeHtml(phase)}}" data-technical-block="${{escapeHtml(techBlock)}}" data-status="${{escapeHtml(status)}}" data-implementation="${{escapeHtml(implStatus)}}">
          <div class="card-header" role="button" tabindex="0" aria-expanded="false">
            <span class="card-toggle">▶</span>
            <div>
              <div class="card-id">${{id}}</div>
              <div class="card-title">${{title}}</div>
              <div class="card-meta">${{phase}} · ${{techBlock}}</div>
              ${{status ? `<span class="badge ${{statusCls}}">${{escapeHtml(status)}}</span>` : ''}}
            </div>
          </div>
          <div class="card-body">
            <dl>${{bodyRows}}</dl>
          </div>
        </div>
      `;
    }}

    function filterAndRender() {{
      const phase = document.getElementById('filter-phase').value;
      const technicalBlock = document.getElementById('filter-technical-block').value;
      const status = document.getElementById('filter-status').value;
      const implementation = document.getElementById('filter-implementation').value;
      const filtered = lessons.filter(l => {{
        if (phase && (l['Project Phase'] || '') !== phase) return false;
        if (technicalBlock && (l['Technical Block'] || '') !== technicalBlock) return false;
        if (status && (l['Status'] || '') !== status) return false;
        if (implementation && (l['Implementation Status'] || '') !== implementation) return false;
        return true;
      }});
      grid.innerHTML = filtered.map(renderCard).join('');
      visibleCountEl.textContent = filtered.length;
      noResults.style.display = filtered.length ? 'none' : 'block';
      grid.querySelectorAll('.card-header').forEach((el, i) => {{
        const card = el.closest('.card');
        el.addEventListener('click', () => card.classList.toggle('expanded'));
        el.addEventListener('keydown', e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); card.classList.toggle('expanded'); }} }});
      }});
    }}

    document.getElementById('filter-phase').addEventListener('change', filterAndRender);
    document.getElementById('filter-technical-block').addEventListener('change', filterAndRender);
    document.getElementById('filter-status').addEventListener('change', filterAndRender);
    document.getElementById('filter-implementation').addEventListener('change', filterAndRender);
    populateFilters();
    filterAndRender();
  </script>
</body>
</html>
"""


def build_html(
    lessons: list[dict[str, Any]],
    output_path: Path | None = None,
    title: str = "Lessons Learned Registry",
) -> Path:
    """Build a single HTML file with expandable cards and filters."""
    path = output_path or (PROJECT_ROOT / "reports" / "lessons_learned.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_html_string(lessons, title), encoding="utf-8")
    return path
