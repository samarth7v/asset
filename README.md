# AssetFlow

**AssetFlow prevents operational chaos** — overdue laptops, double-booked rooms, and maintenance bottlenecks — using an **explainable Operational Risk Twin** that detects issues from live data and records every action in an auditable event ledger.

## Problem

Enterprises lose time and money when assets aren't returned, resources double-book, and maintenance blocks teams. Spreadsheets and siloed tools can't detect these patterns before they disrupt the day.

## Solution

AssetFlow is an operational control plane for physical assets and shared resources:

- **Operational Risk Twin** — explainable rules scan live SQLite data for overdue returns, maintenance capacity gaps, and category exhaustion
- **Immutable event ledger** — every action is auditable for compliance and analytics
- **Server-enforced booking conflicts** — overlap checks run at the API boundary, not in the browser

## Demo

**Live (demo session):** [https://forty-times-fail.loca.lt](https://forty-times-fail.loca.lt) — requires the local server and tunnel to be running.

**Persistent deploy:** Push to GitHub and deploy on [Render](https://render.com) using the included `render.yaml` (free tier).

**Run locally:**

```powershell
python server.py
```

Then open [http://127.0.0.1:4173](http://127.0.0.1:4173).

Sign in with any email/password (demo mode). The dashboard shows live risks on first load.

**Reset demo data:**

```powershell
Remove-Item assetflow.db -ErrorAction SilentlyContinue
python server.py
```

## 3-minute demo script

1. **Login** → Dashboard KPIs and Operational Risk Twin cards
2. Click **Send return reminder** or **Escalate maintenance** on a risk card
3. Scroll to **Latest events** — see `risk.mitigated` in the event ledger
4. Go to **Resource Booking** → book `09:00–10:00` on Conference Room B2 → get overlap error
5. **Register asset** → inventory and risk counts update on refresh

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla JavaScript, HTML5, CSS |
| Backend | Python 3 stdlib (`http.server`, `sqlite3`) |
| Database | SQLite (`assetflow.db`, auto-created) |
| Deploy | Render (`render.yaml`) or any host running `python server.py` |

Zero build step. Full persistence. REST API at `/api/*`.

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/assets` | List all assets |
| GET | `/api/risks` | Operational Risk Twin snapshot |
| GET | `/api/events` | Immutable event ledger |
| GET | `/api/bookings` | Shared-resource bookings |
| POST | `/api/bookings` | Create booking (409 on overlap) |
| POST | `/api/risks/action` | Execute risk mitigation |
| POST | `/api/assets` | Register new asset |

## What makes it different

- **Explainable risk detection** — not black-box AI; every risk shows evidence and a one-click action
- **Server-enforced rules** — booking conflicts and persistence survive refresh and restart
- **Auditable by design** — event ledger records registrations, bookings, transfers, and risk mitigations
- **Production-ready UI** — 9-module enterprise shell with responsive layout

## Roadmap

- Role-based authentication
- Maintenance kanban API workflow
- Predictive maintenance from event ledger history
