# Structured Lessons Learned Registry (SLLR)

Production web application for capturing, classifying, storing, automating, and reusing lessons learned. Built with **FastAPI**, **React**, and **CSV databases** (Power BI source of truth).

## Architecture

- **Backend**: FastAPI 0.115+, Uvicorn, Python 3.12, Pydantic v2
- **Frontend**: Vite 8, React 19, React Router 7, TypeScript, Tailwind CSS 4
- **Data**: CSV files in `data/` (source of truth for Power BI)
- **No Authentication**: Designed to sit behind LearnPower portal

## Quick Start

### Local Development

**Backend:**

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173, proxies /api to backend
```

Visit http://localhost:5173

### Docker Compose

```bash
docker-compose up --build
```

Visit http://localhost:8000

### Production Deployment (Dokploy / Nixpacks)

Deploy to port 8000. Nixpacks automatically:
- Installs Node.js 22.14 via `scripts/install-node.sh`
- Installs Python 3.12 dependencies
- Builds frontend with `npm run build`
- Serves API + static frontend via FastAPI

**Environment Variables:**

- `SLLR_BASE_PATH`: Base path prefix for portal deployment (default: `/sllr`). Set to `/sllr` for deployment behind Traefik at `https://portal.powerlearn.us/sllr`.
- `SLLR_DATA_DIR`: Path to CSV data (default: `data`). Mount a volume to `/data` in production.
- `STATIC_DIR`: Frontend build directory (default: `frontend/dist`)
- `CORS_ORIGINS`: Additional allowed CORS origins (comma-separated). Portal origin `https://portal.powerlearn.us` is included by default.
- `PORT`: Server port (default: 8000)

**Volume:** Mount `/data` for persistent CSV storage.

### Portal Deployment at /sllr

This app is designed to run behind the LearnPower portal at `https://portal.powerlearn.us/sllr`.

**Traefik Configuration:**
- **Host**: `portal.powerlearn.us`
- **Path**: `/sllr`
- **Strip Path**: OFF (paths arrive as `/sllr/...` and `/sllr/api/...`)
- **Container Port**: 8000

**Required Environment Variables for Portal:**
```bash
SLLR_BASE_PATH=/sllr
SLLR_DATA_DIR=/data
STATIC_DIR=frontend/dist
CORS_ORIGINS=https://portal.powerlearn.us
PORT=8000
```

The app will serve:
- Frontend SPA at `/sllr/`
- API endpoints at `/sllr/api/*`
- Health check at `/sllr/api/health`

**Local Development without Prefix:**

For local development without the `/sllr` prefix:
```bash
# Backend (no SLLR_BASE_PATH set)
uvicorn backend.app.main:app --reload --port 8000

# Frontend (no VITE_BASE set)
VITE_BASE=/ npm run dev
```

This runs the app at `http://localhost:5173` with API at `/api/*` (proxied to backend).

## API Endpoints

All endpoints are prefixed with the base path (default `/sllr`):

- `GET /sllr/api/health` — Health check
- `GET /sllr/api/references` — Controlled vocabularies
- `GET /sllr/api/lessons` — List lessons (with filters)
- `GET /sllr/api/lessons/{id}` — Get lesson by ID
- `GET /sllr/api/lessons/next-id` — Suggest next available ID
- `POST /sllr/api/lessons` — Create lesson (Status: Draft, Implementation Status: Not Implemented)
- `PUT /sllr/api/lessons/{id}` — Update lesson (all fields except ID)
- `PATCH /sllr/api/lessons/{id}` — Partial update (e.g., status or implementation_status)
- `GET /sllr/api/kpis` — Compute governance KPIs
- `GET /sllr/api/reports/validation` — Validation report (text)
- `GET /sllr/api/reports/duplicates` — Duplicates report (text)
- `GET /sllr/api/reports/kpi` — KPI summary (text)
- `GET /sllr/api/reports/dashboard-export` — Dashboard CSV (with Validation_Errors column)
- `POST /sllr/api/export/pdf` — Generate PDF (phase → category grouping, page breaks)
- `POST /sllr/api/export/html` — Generate HTML (standalone with filters)

*Note: For local development without the prefix, endpoints are at `/api/*` directly.*

## Frontend Pages

- `/` — Dashboard (5 KPI cards + 4 bar charts)
- `/lessons` — Browse table + filters + inline status updates
- `/lessons/new` — Add new lesson (suggests next ID, saves as Draft)
- `/lessons/:id` — Edit lesson (ID read-only)
- `/approve` — Approve workflow (Draft → Approved)
- `/implementation` — Implementation follow-up (track recommendations)
- `/validation` — Validation errors
- `/duplicates` — Exact + near duplicates
- `/report` — Embedded HTML report (iframe)
- `/export` — Download PDF / HTML
- `/reports` — Download text reports + dashboard CSV

## Data Model

CSV schema defined in `src/sllr/config.py`. Required fields:

- **Lesson ID** (unique, immutable after create)
- **Title** (≤200 chars)
- **Category** (controlled: Development, Engineering, Procurement, Construction, O&M)
- **Technical Block** (controlled: Civil, HV & Grid, PV, BESS)
- **Sub-category** (free text)
- **Project Phase** (controlled: Development, Pre-Execution, Construction, O&M)
- **Root Cause**
- **What Happened**
- **Impact**
- **Lesson Learned** (≤500 chars)
- **Recommendation**
- **Status** (controlled: Draft, Approved)
- **Implementation Status** (controlled: Not Implemented, Implemented)
- **Owner**

Optional: Recommendation Due Date (YYYY-MM-DD), Keywords, Created Date, Modified Date

Controlled vocabularies in `data/*.csv`. API enforces exact, case-sensitive values.

## Storage

CSV files with file locking (fcntl). Last-write-wins is the current behavior; lock prevents torn reads/writes. No delete endpoint.

## Tests

```bash
pytest
```

API tests use FastClient (no browser required for CI).

## Legacy Streamlit App

The original Streamlit UI is in `legacy/streamlit_app.py`. See `legacy/README.md` for instructions. **Deprecated** — use the FastAPI + React app.

## Governance KPIs

- **Total Lessons**
- **Capture-to-Approval Time** (avg days)
- **Repeated Issues** (same technical block / category / root cause pattern)
- **% Recommendations Implemented** (among approved lessons)
- **Overdue (Not Implemented)** (approved, past due date, not implemented)

See `docs/GOVERNANCE_AND_KPIS.md` for definitions.

## Power BI Integration

Connect Power BI to `data/lessons_master.csv` or download `dashboard_export.csv` via `/api/reports/dashboard-export`. See `docs/POWER_BI_INTEGRATION.md`.

## Repository Layout

```
backend/app/              # FastAPI application
  main.py                 # FastAPI app, CORS, static serving, routers
  storage.py              # CSV I/O with file locking
  routers/                # API routers (lessons, references, kpis, reports, export)
frontend/                 # Vite + React + TypeScript
  src/
    pages/                # Dashboard, Lessons, Add, Edit, Approve, Implementation, Validation, Duplicates, Report, Export, Reports
    components/           # Layout, UI components
    lib/api.ts            # API client
src/sllr/                 # Business logic (reused by backend)
  config.py               # Paths, schema, controlled vocabularies
  loaders.py              # CSV I/O
  validation.py           # Schema validation
  duplicate_detection.py  # Exact + near duplicates
  kpi.py                  # KPI computation
  reports.py              # Text reports + dashboard CSV
  export_pdf.py           # PDF export (reportlab)
  export_html.py          # HTML export
data/                     # CSV data (lessons_master.csv + reference tables)
scripts/                  # CLI tools (validate_lessons.py, run_reports.py, kpi_summary.py)
  install-node.sh         # Node.js 22.14 installer (for Nixpacks)
legacy/                   # Legacy Streamlit app (deprecated)
tests/                    # Pytest API tests
docs/                     # SharePoint schema, Power BI integration, governance
Dockerfile                # Multi-stage build (Node + Python)
docker-compose.yml        # Local Docker setup
nixpacks.toml             # Dokploy / Nixpacks config
.env.example              # Environment variables template
```

## Development Notes

- Reuse existing Python business logic (`src/sllr/`) — do not reimplement KPI/validation/duplicates/PDF/HTML
- CSV is the source of truth (Power BI reads it)
- File locking prevents torn reads/writes during concurrent access
- API returns 409 on duplicate Lesson ID, 422 on validation errors
- PDF export requires `reportlab` (optional dependency); returns 501 if missing
- No auth (portal sits in front)
- Tailwind 4 via `@tailwindcss/vite`
- Dark theme: ink #0c0e12, panel #141820, raised #1b212c, line #2a3140, text #e8eaef, muted #8b93a7, blue #3b82f6
- Font: IBM Plex Sans + IBM Plex Mono, 14px base

## Contributing

1. Branch: `git checkout -b feature/xyz`
2. Backend: `uvicorn backend.app.main:app --reload`
3. Frontend: `cd frontend && npm run dev`
4. Test: `pytest`
5. Commit and push

## License

See project documentation.
