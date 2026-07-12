# AssetFlow demo tunnel — run before presenting

```powershell
# Terminal 1: start the app
python server.py

# Terminal 2: expose to judges (URL changes each session)
npx localtunnel --port 4173
```

Copy the `your url is:` link into README before submission.

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
