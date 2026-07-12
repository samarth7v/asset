"""AssetFlow API and SQLite persistence layer. Run: python server.py"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sqlite3
from datetime import date, datetime

ROOT = Path(__file__).parent
DB = ROOT / "assetflow.db"

SEED_ASSETS = [
    ("AF-0012", "Dell Latitude 7440", "Electronics", "Allocated", "Priya Shah", "Engineering", "Bengaluru HQ", "Excellent", "2026-07-01"),
    ("AF-0062", "Epson Projector", "Electronics", "Under Maintenance", "", "Facilities", "HQ Floor 2", "Needs repair", None),
    ("AF-0201", "Ergo Office Chair", "Furniture", "Available", "", "Operations", "Warehouse", "Good", None),
    ("AF-0087", "Toyota Forklift", "Vehicles", "Available", "", "Field Ops", "Warehouse", "Good", None),
]

def connection():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def setup_db():
    with connection() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS assets (tag TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, cat TEXT NOT NULL, status TEXT NOT NULL, holder TEXT, dept TEXT, location TEXT NOT NULL, condition TEXT NOT NULL, return_date TEXT);
        CREATE TABLE IF NOT EXISTS departments (name TEXT PRIMARY KEY, head TEXT NOT NULL, parent TEXT NOT NULL, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, resource TEXT NOT NULL, start TEXT NOT NULL, end TEXT NOT NULL, team TEXT NOT NULL, status TEXT NOT NULL, purpose TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, icon TEXT NOT NULL, title TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS maintenance_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, asset_tag TEXT NOT NULL, priority TEXT NOT NULL, issue TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS transfer_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, asset_tag TEXT NOT NULL, reason TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS event_ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, actor TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
        """)
        if not con.execute("SELECT 1 FROM assets LIMIT 1").fetchone():
            con.executemany("INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", SEED_ASSETS)
            con.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", [("Engineering", "Aditi Rao", "—", "Active"), ("Facilities", "Rohan Mehta", "—", "Active"), ("Field Ops (East)", "Sana Iqbal", "Field Ops", "Inactive")])
            con.execute("INSERT INTO bookings (resource,start,end,team,status,purpose,created_at) VALUES (?,?,?,?,?,?,?)", ("Conference Room B2", "09:00", "10:00", "Procurement Team", "Ongoing", "Weekly planning", datetime.now().isoformat()))
            notify(con, "📦", "AssetFlow workspace initialized", "Your live data workspace is ready.")
            record_event(con, "workspace.initialized", "workspace", "assetflow", "System", "SQLite workspace created with operational seed data.")
        con.execute("UPDATE assets SET return_date='2026-07-01' WHERE tag='AF-0012'")

def notify(con, icon, title, detail):
    con.execute("INSERT INTO notifications (icon,title,detail,created_at) VALUES (?,?,?,?)", (icon, title, detail, datetime.now().isoformat()))

def record_event(con, event_type, entity_type, entity_id, actor, detail):
    con.execute("INSERT INTO event_ledger (event_type,entity_type,entity_id,actor,detail,created_at) VALUES (?,?,?,?,?,?)", (event_type, entity_type, entity_id, actor, detail, datetime.now().isoformat()))

def risk_snapshot(con):
    """Deterministic, explainable operational-risk rules."""
    risks = []
    overdue = rows(con.execute("SELECT tag,name,holder,return_date AS returnDate FROM assets WHERE return_date IS NOT NULL AND date(return_date) < date('now')"))
    for asset in overdue:
        risks.append({"id":f"overdue:{asset['tag']}","severity":"high","title":f"Overdue return: {asset['tag']}","evidence":f"{asset['name']} was due on {asset['returnDate']} and is still held by {asset['holder']}.","action":"Send return reminder","actionType":"remind_return"})
    unavailable = rows(con.execute("SELECT tag,name,cat,status FROM assets WHERE status='Under Maintenance'"))
    for asset in unavailable:
        spare_count = con.execute("SELECT COUNT(*) FROM assets WHERE cat=? AND status='Available'", (asset["cat"],)).fetchone()[0]
        risks.append({"id":f"maintenance:{asset['tag']}","severity":"critical" if spare_count == 0 else "medium","title":f"Capacity risk: {asset['name']} is unavailable","evidence":f"Status is {asset['status']}. Available backup assets in {asset['cat']}: {spare_count}.","action":"Escalate maintenance","actionType":"escalate_maintenance"})
    for category in rows(con.execute("SELECT cat, SUM(status='Available') AS available, COUNT(*) AS total FROM assets GROUP BY cat")):
        if category["total"] > 0 and category["available"] == 0:
            risks.append({"id":f"capacity:{category['cat']}","severity":"high","title":f"No available {category['cat'].lower()} assets","evidence":f"All {category['total']} registered {category['cat'].lower()} assets are allocated, reserved, or under maintenance.","action":"Open transfer request","actionType":"open_transfer"})
    return risks

def rows(cursor): return [dict(row) for row in cursor.fetchall()]

class API(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    def body(self):
        size = int(self.headers.get("Content-Length", 0)); return json.loads(self.rfile.read(size) or b"{}")

    def do_GET(self):
        if not self.path.startswith("/api/"): return super().do_GET()
        with connection() as con:
            if self.path == "/api/assets": return self.send_json(200, rows(con.execute("SELECT tag,name,cat,status,holder,dept,location,condition,return_date AS returnDate FROM assets ORDER BY tag DESC")))
            if self.path == "/api/departments": return self.send_json(200, [list(x) for x in con.execute("SELECT name,head,parent,status FROM departments ORDER BY name")])
            if self.path == "/api/bookings": return self.send_json(200, rows(con.execute("SELECT id,resource,start,end,team,status,purpose,created_at AS createdAt FROM bookings ORDER BY start")))
            if self.path == "/api/notifications": return self.send_json(200, [[x["icon"],x["title"],x["detail"],x["created_at"]] for x in con.execute("SELECT icon,title,detail,created_at FROM notifications ORDER BY id DESC LIMIT 30")])
            if self.path == "/api/events": return self.send_json(200, rows(con.execute("SELECT id,event_type AS eventType,entity_type AS entityType,entity_id AS entityId,actor,detail,created_at AS createdAt FROM event_ledger ORDER BY id DESC LIMIT 50")))
            if self.path == "/api/risks": return self.send_json(200, risk_snapshot(con))
            if self.path == "/api/dashboard":
                count = lambda sql: con.execute(sql).fetchone()[0]
                return self.send_json(200, {"available":count("SELECT COUNT(*) FROM assets WHERE status='Available'"),"allocated":count("SELECT COUNT(*) FROM assets WHERE status='Allocated'"),"maintenance":count("SELECT COUNT(*) FROM assets WHERE status='Under Maintenance'"),"bookings":count("SELECT COUNT(*) FROM bookings"),"transfers":count("SELECT COUNT(*) FROM transfer_requests WHERE status='Pending'")})
        return self.send_json(404, {"error":"Not found"})

    def do_POST(self):
        try: data = self.body()
        except json.JSONDecodeError: return self.send_json(400, {"error":"Invalid JSON"})
        try:
            with connection() as con:
                if self.path == "/api/assets":
                    next_number = con.execute("SELECT COALESCE(MAX(CAST(SUBSTR(tag,4) AS INTEGER)),0)+1 FROM assets").fetchone()[0]
                    tag = f"AF-{next_number:04d}"
                    con.execute("INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?)", (tag, data["name"], data["cat"], "Available", "", "", data["location"], data["condition"], None)); notify(con,"📦",f"{tag} registered",f"{data['name']} is available for allocation."); record_event(con,"asset.registered","asset",tag,"Alex Sharma",f"{data['name']} registered at {data['location']}."); return self.send_json(201,{"tag":tag})
                if self.path == "/api/departments":
                    con.execute("INSERT INTO departments VALUES (?,?,?,?)",(data["name"],data.get("head") or "Unassigned","—","Active")); notify(con,"▦", "Department created", data["name"]); record_event(con,"department.created","department",data["name"],"Alex Sharma",f"Department created with head {data.get('head') or 'Unassigned'}."); return self.send_json(201,{"ok":True})
                if self.path == "/api/bookings":
                    conflict=con.execute("SELECT 1 FROM bookings WHERE resource=? AND ? < end AND ? > start",(data["resource"],data["start"],data["end"])).fetchone()
                    if conflict: return self.send_json(409,{"error":"This time overlaps an existing booking."})
                    con.execute("INSERT INTO bookings (resource,start,end,team,status,purpose,created_at) VALUES (?,?,?,?,?,?,?)",(data["resource"],data["start"],data["end"],"Alex Sharma","Upcoming",data["purpose"],datetime.now().isoformat())); notify(con,"📅",f"Booking confirmed: {data['resource']}",f"Your booking is scheduled for {data['start']} – {data['end']}."); record_event(con,"booking.created","booking",data["resource"],"Alex Sharma",f"Booked {data['start']}–{data['end']} for {data['purpose']}."); return self.send_json(201,{"ok":True})
                if self.path == "/api/transfers":
                    asset_tag = data.get("assetTag", "AF-0012")
                    con.execute("INSERT INTO transfer_requests (asset_tag,reason,status,created_at) VALUES (?,?,?,?)",(asset_tag,data["reason"],"Pending",datetime.now().isoformat())); notify(con,"↗","Transfer request submitted",f"{asset_tag} transfer awaits manager approval."); record_event(con,"transfer.requested","asset",asset_tag,"Alex Sharma",data["reason"]); return self.send_json(201,{"ok":True})
                if self.path == "/api/maintenance":
                    asset_tag = data.get("assetTag", "AF-0012")
                    con.execute("INSERT INTO maintenance_requests (asset_tag,priority,issue,status,created_at) VALUES (?,?,?,?,?)",(asset_tag,data["priority"],data["issue"],"Pending",datetime.now().isoformat())); notify(con,"🔧","Maintenance request submitted","Awaiting Asset Manager approval."); record_event(con,"maintenance.requested","asset",asset_tag,"Alex Sharma",data["issue"]); return self.send_json(201,{"ok":True})
                if self.path == "/api/risks/action":
                    risk_id, action = data["riskId"], data["actionType"]
                    if action == "open_transfer":
                        asset_tag = risk_id.split(":")[-1] if ":" in risk_id else "AF-0012"
                        con.execute("INSERT INTO transfer_requests (asset_tag,reason,status,created_at) VALUES (?,?,?,?)",(asset_tag,f"Risk Twin mitigation for {risk_id}","Pending",datetime.now().isoformat()))
                    if action == "escalate_maintenance":
                        notify(con,"⚠","Maintenance escalation created",f"Risk Twin escalated {risk_id} for review.")
                    if action == "remind_return":
                        notify(con,"↳","Return reminder sent",f"Risk Twin sent a reminder for {risk_id}.")
                    record_event(con,"risk.mitigated","risk",risk_id,"Alex Sharma",f"Executed action: {action}.")
                    return self.send_json(201,{"ok":True})
        except (KeyError, sqlite3.IntegrityError) as exc: return self.send_json(400,{"error":str(exc)})
        return self.send_json(404,{"error":"Not found"})

if __name__ == "__main__":
    import os
    setup_db()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "4173"))
    print(f"AssetFlow running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), API).serve_forever()
