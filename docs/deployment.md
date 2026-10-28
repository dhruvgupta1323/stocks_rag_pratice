# Deployment & Operations Guide

## 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- PostgreSQL (Supabase recommended) or local SQLite

---

## 2. Local Development Quickstart

### Backend Setup:
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt

# Copy environment template
cp ../.env.example .env

# Initialize database schema and seed initial Indian equities
python app/db/init_db.py

# Start FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 3. Production Deployment

### Backend on Render / Fly.io / Container Host:
1. Connect your repository to Render / Fly.io.
2. Select **Docker** or Python environment.
3. Set environment variables:
   - `ENVIRONMENT=production`
   - `DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres`
   - `UPSTOX_API_KEY=[YOUR_KEY]`
   - `UPSTOX_ACCESS_TOKEN=[YOUR_TOKEN]`
   - `LLM_PROVIDER=openai` (or `gemini`)
   - `OPENAI_API_KEY=[YOUR_KEY]`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

### Frontend on Vercel:
1. Import repository to Vercel.
2. Set Root Directory to `frontend`.
3. Set Environment Variable:
   - `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api/v1`
4. Deploy!

### Background Ingestion Worker:
To run the automated scheduled news crawler in a dedicated background worker:
```bash
python backend/app/workers/scheduled_ingestion.py
```
This runs continuously, checking for corporate disclosures and syndicated news every 60 minutes with SHA-256 deduplication.

---

## 4. Running the Benchmark Evaluation Suite
To execute the reproducible 12-question benchmark test:
```bash
python run_benchmark.py
```
Or trigger it directly from the web UI at `/evaluation` or via API:
```bash
curl -X POST http://localhost:8000/api/v1/evaluation/run -H "Content-Type: application/json" -d "{}"
```

