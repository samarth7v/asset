# AssetFlow

AssetFlow is an enterprise asset and shared-resource management prototype with a responsive browser interface, a Python HTTP API, and SQLite persistence.

## Run locally

```powershell
python server.py
```

Then open [http://127.0.0.1:4173](http://127.0.0.1:4173).

The backend creates `assetflow.db` automatically on first run. It exposes REST endpoints for assets, departments, bookings, transfer requests, maintenance requests, notifications, and dashboard counts. Booking conflicts are validated transactionally by the server.
