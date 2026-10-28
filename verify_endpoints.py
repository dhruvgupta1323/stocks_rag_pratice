import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_endpoints():
    print("Testing /health...")
    r = client.get("/health")
    assert r.status_code == 200, f"/health failed: {r.text}"
    print("  [OK] /health:", r.json()["status"])

    print("Testing /api/v1/stocks/search?q=Reliance...")
    r = client.get("/api/v1/stocks/search?q=Reliance")
    assert r.status_code == 200, f"Search failed: {r.text}"
    data = r.json()
    assert len(data) > 0, "No search results returned"
    print(f"  [OK] Found {len(data)} results for 'Reliance'")

    print("Testing /api/v1/stocks/RELIANCE/overview...")
    r = client.get("/api/v1/stocks/RELIANCE/overview")
    assert r.status_code == 200, f"Overview failed: {r.text}"
    ov = r.json()
    print(f"  [OK] Overview price: INR {ov['quote']['last_price']}, status: {ov['data_status']}")

    print("Testing /api/v1/stocks/RELIANCE/history?days=30...")
    r = client.get("/api/v1/stocks/RELIANCE/history?days=30")
    assert r.status_code == 200, f"History failed: {r.text}"
    hist = r.json()
    print(f"  [OK] History bars returned: {len(hist['bars'])}, status: {hist['data_status']}")

    print("Testing /api/v1/stocks/RELIANCE/financials...")
    r = client.get("/api/v1/stocks/RELIANCE/financials")
    assert r.status_code == 200, f"Financials failed: {r.text}"
    fin = r.json()
    print(f"  [OK] Financial metrics returned: {len(fin['annual_metrics'])} annual")

    print("Testing /api/v1/stocks/RELIANCE/news...")
    r = client.get("/api/v1/stocks/RELIANCE/news")
    assert r.status_code == 200, f"News failed: {r.text}"
    nw = r.json()
    print(f"  [OK] News articles returned: {nw['total_articles']}")

    print("Testing /api/v1/stocks/RELIANCE/report...")
    r = client.get("/api/v1/stocks/RELIANCE/report")
    assert r.status_code == 200, f"Report failed: {r.text}"
    rep = r.json()
    print(f"  [OK] Report generated: '{rep['title']}'")

    print("Testing POST /api/v1/research/ask...")
    r = client.post("/api/v1/research/ask", json={"question": "What is the RSI of INFY?", "instrument_id": "INFY"})
    assert r.status_code == 200, f"Ask failed: {r.text}"
    ans = r.json()
    print(f"  [OK] Ask response direct_answer: {ans['direct_answer'][:60]}...")

    print("Testing /api/v1/evaluation/runs...")
    r = client.get("/api/v1/evaluation/runs")
    assert r.status_code == 200, f"Evaluation runs failed: {r.text}"
    runs = r.json()
    print(f"  [OK] Recorded evaluation runs in DB: {len(runs)}")

    print("\nALL FASTAPI ENDPOINTS VERIFIED & WORKING PERFECTLY!")

if __name__ == "__main__":
    test_endpoints()
