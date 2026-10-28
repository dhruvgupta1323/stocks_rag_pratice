# AI Stock Intelligence Platform (Indian Equities — NSE & BSE)

A full-stack, enterprise-grade AI equity research and market analytics platform for Indian stocks listed on the **National Stock Exchange (NSE)** and **Bombay Stock Exchange (BSE)**.

Built with **FastAPI**, **Next.js 14**, **LangGraph**, **SQLAlchemy**, and **Tailwind CSS**.

---

## Key Features

1. **Indian Equity Resolution & Search**:
   - Search by ticker symbol (e.g., `RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `TATAMOTORS`) or company name.
   - Distinct support for NSE and BSE exchange listings and ISIN identifiers.
   - Recently viewed stock history stored in local browser state.

2. **Market Data Provider Abstraction**:
   - Provider-independent market interface (`BaseMarketDataProvider`).
   - Authenticated adapter for **Upstox API v2** with rate-limiting and token lifecycle support.
   - Fully documented deterministic **MockMarketDataProvider** for offline/local development, clearly labeling simulated quotes with `data_status="mock"`.
   - Data status badges distinguishing realtime, delayed, cached, and mock quotes.

3. **Deterministic Financial Analytics**:
   - Standalone mathematical calculations implemented in pure Python (no LLM hallucinated math).
   - Technical Indicators: Absolute & Percentage Change, 20-day SMA, EMA, 14-day RSI (0–100 bounded), Annualized Historical Volatility, and Peak-to-Trough Max Drawdown.
   - Fundamental Metrics: Revenue Growth, Net Profit Growth, PE, PB, and Debt-to-Equity.
   - Division-by-zero protection, NaN handling, and period-alignment checks.

4. **Automated Financial Research Ingestion**:
   - Syndicated RSS news feeds and corporate disclosure indexing (Google News India Equities, Economic Times, Moneycontrol).
   - Content normalization, HTML tag removal, and prompt-injection defusal.
   - Duplicate prevention via SHA-256 content hashing and canonical URL deduplication.
   - Scheduled background ingestion worker (`backend/app/workers/scheduled_ingestion.py`).

5. **LangGraph 10-Node Research Workflow**:
   - Bounded typed state graph with conditional edges.
   - Nodes: `resolve_stock` ➔ `classify_question` ➔ `fetch_market_data` ➔ `fetch_financial_data` ➔ `calculate_metrics` ➔ `search_news_disclosures` ➔ `retrieve_stored_research` ➔ `synthesize_answer` ➔ `validate_evidence` ➔ `finalize_response`.
   - Adheres to the **Answer Generation Contract**: Direct Answer, Supporting Numerical Facts, Explanations, Source Citations, Timestamps, and Limitations.
   - Strict abstention and clarifying prompts when data is ambiguous or insufficient.

6. **Guardrails & Safety**:
   - **Citation Guardrail**: Rejects unverified or hallucinated citation IDs not found in retrieved source metadata.
   - **Prompt Injection Defense**: Strips and defuses adversarial system override instructions.
   - **Trade Execution Refusal**: Safely rejects trading, shorting, or order-execution prompts.
   - **Investment Advisory Disclaimer**: Factual research and quantitative metrics only; no buy/sell speculative advice.

7. **Custom Evaluation Framework & Dashboard**:
   - Reproducible 12-question benchmark covering market quotes, technical indicators, financial reports, news summaries, ambiguous tickers, and prompt injection attempts.
   - Quantitative measurement of **Correctness**, **Citation Precision**, and **P50/P95 Latency**.
   - Inspectable evaluation dashboard web page (`/evaluation`) and REST API (`POST /api/v1/evaluation/run`).

---

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts, Lucide Icons.
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, HTTPX, Pandas, NumPy.
- **AI / Workflows**: LangGraph, LangChain Core.
- **Database**: PostgreSQL (Supabase ready) / SQLite with `aiosqlite`.
- **Deployment**: Docker, Docker Compose, Render / Vercel ready.

---

## Project Structure

```
stocks_rag/
├── backend/
│   ├── app/
│   │   ├── analytics/       # Deterministic quantitative formulas (RSI, SMA, Drawdown, Ratios)
│   │   ├── api/             # FastAPI REST routes (/api/v1/stocks, /research, /evaluation)
│   │   ├── core/            # Settings, logging, custom domain exceptions
│   │   ├── crawler/         # Ingestion feeds, normalizer, and prompt-injection defusal
│   │   ├── db/              # SQLAlchemy Base, session maker, schema initialization
│   │   ├── evaluation/      # Benchmark runner and metrics formulas
│   │   ├── graph/           # LangGraph state, nodes, and conditional workflow router
│   │   ├── guardrails/      # Citation validator and safety filters
│   │   ├── models/          # 10 database tables (instruments, quotes, financials, sources, etc.)
│   │   ├── providers/       # Upstox and Mock market data adapters
│   │   ├── research/        # Objective research report generator
│   │   ├── schemas/         # Pydantic v2 validation models
│   │   ├── services/        # Business logic services
│   │   └── workers/         # Background periodic news crawler
│   ├── alembic/             # Database migration scripts
│   ├── tests/               # 18 unit and workflow pytest test suites
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js 14 App Router pages (/, /stocks/[id], /evaluation)
│   ├── components/          # StockSearch, StockChart, ResearchChat, ResearchReportModal, Navbar
│   ├── lib/                 # Typed API client
│   ├── Dockerfile
│   └── package.json
├── data/
│   └── evaluation/          # Benchmark dataset JSON (12 curated question scenarios)
├── docs/
│   ├── architecture.md      # Detailed system architecture and sequence flows
│   └── deployment.md        # Local development and cloud deployment guides
├── .env.example             # Complete environment variables template
├── docker-compose.yml       # Multi-container orchestration
└── pytest.ini
```

---

## Quickstart

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # On Windows (.venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
python app/db/init_db.py     # Creates database schema and seeds initial Indian equities
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## Running Verification & Tests

### Backend Unit & Workflow Tests
```bash
backend\.venv\Scripts\pytest -v
```
All **18 automated tests** pass, validating price change formulas, SMA/RSI bounds, drawdown, financial ratios, HTML normalization, prompt injection defusal, citation validation, and LangGraph workflow routing.

### AI Benchmark Evaluation Run
```bash
backend\.venv\Scripts\python run_benchmark.py
```
Output:
- **Questions**: 12 / 12 passed (**100.0% Pass Rate**)
- **Average Fact Correctness**: **94.4%**
- **Citation Precision**: **100.0%** (0 unverified citations)
- **Average Latency**: **20.46 ms** (P50: 18.34 ms, P95: 38.88 ms)

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/stocks/search?q={query}` | Search Indian equities by name or ticker |
| `GET` | `/api/v1/stocks/{id}/overview` | Latest price, 52W range, valuation ratios |
| `GET` | `/api/v1/stocks/{id}/history` | Historical daily OHLCV bars |
| `GET` | `/api/v1/stocks/{id}/financials` | Quarterly, annual, and TTM reported metrics |
| `GET` | `/api/v1/stocks/{id}/news` | Syndicated news articles and disclosures |
| `GET` | `/api/v1/stocks/{id}/report` | Synthesized objective equity research report |
| `POST` | `/api/v1/research/ask` | Natural language Q&A with verifiable citations |
| `GET` | `/api/v1/research/sources/{id}` | Source attribution metadata |
| `POST` | `/api/v1/evaluation/run` | Trigger evaluation benchmark |
| `GET` | `/api/v1/evaluation/runs` | List evaluation run history |
| `GET` | `/health` | System health and configured provider status |

---

## License
MIT

