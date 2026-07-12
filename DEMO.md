# AssetFlow demo — run before presenting

```powershell
python server.py
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173).

## 3-minute demo checklist

- [ ] Login with any credentials
- [ ] Dashboard shows 3+ Risk Twin cards (overdue, maintenance, capacity)
- [ ] Click **Send return reminder** → event ledger updates
- [ ] Resource Booking → book 09:00–10:00 → overlap error
- [ ] Register asset → inventory count increases

## Reset demo data

```powershell
# Stop server first, then:
Remove-Item assetflow.db -Force
python server.py
```
