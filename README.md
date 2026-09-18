# Insight Copilot — AI Business Intelligence Analyst

A reasoning, tool-using analyst agent built with **LangGraph**, **FastAPI**, and **Next.js**. Ask questions about the **Brazilian E-Commerce (Olist)** dataset in plain English; the agent plans its approach, picks the analytical tools it needs, visualizes findings, and answers with executive-level clarity rather than raw database dumps.

---

## System Architecture

```mermaid
graph TD
    User([User Query]) --> Planner[Planner Node<br/>LLM + Schema Context]
    
    Planner -->|route == 'direct_answer'| Direct[Direct Answer Node<br/>Greetings / Capabilities]
    Planner -->|route == 'unsupported'| Unsupported[Unsupported Node<br/>Honest Refusal & Suggestions]
    Planner -->|route == 'tools'| ToolExec[Tool Executor Node<br/>Sequential Tool Runner]
    
    ToolExec -->|tool == 'query_data'| T1[query_data<br/>Pandas structured params]
    ToolExec -->|tool == 'compute_metrics'| T2[compute_metrics<br/>Stats, CV Seasonality, Outliers]
    ToolExec -->|tool == 'make_chart'| T3[make_chart<br/>Plotly figure JSON spec]
    ToolExec -->|tool == 'web_search'| T4[web_search<br/>DuckDuckGo live context]
    
    T1 --> LoopRouter{should_continue<br/>remaining tools or max 4 iterations}
    T2 --> LoopRouter
    T3 --> LoopRouter
    T4 --> LoopRouter
    
    LoopRouter -->|more tools in plan| ToolExec
    LoopRouter -->|error encountered| ErrHandler[Error Handler Node<br/>Graceful Diagnostic Guidance]
    LoopRouter -->|plan complete| Synthesizer[Synthesizer Node<br/>3-Part Executive Answer]
    
    Synthesizer --> Output([Final Answer + Reasoning Trace + Chart Spec])
    Direct --> Output
    Unsupported --> Output
    ErrHandler --> Output
```

### Graph Nodes & State Flow
- **`planner`**: Analyzes the question with an injected schema profile and emits structured JSON: `rationale`, `route`, and an ordered `tool_plan`.
- **`route_after_plan`** (Conditional Edge): Directs execution to `tool_executor`, `direct_answer`, or `unsupported`.
- **`tool_executor`**: Executes queued tools sequentially, feeds previous results to downstream tools via `data_ref`, and stores chart definitions directly in `state["chart_spec"]`.
- **`should_continue`** (Conditional Edge): Enables multi-step tool loops (capped at 4 iterations) and routes to `synthesizer` or `error_handler`.
- **`synthesizer`**: Produces a structured 3-part answer:
  1. **Direct Answer**: Concise, unambiguous answer upfront.
  2. **Supporting Numbers**: Metrics, percentages, and group breakdowns woven into prose.
  3. **Strategic Takeaway / Why it Matters**: Operational implications and anomalies worth noting.
- **State Persistence**: Tracked per session `thread_id` using `MemorySaver` (local) and `PostgresSaver` (Neon PostgreSQL).

---

## Analytical Tools

| Tool | What it does | When the agent picks it |
|---|---|---|
| `query_data` | Filter, group, aggregate, and rank records via validated structured parameters | Questions asking for totals, counts, top/bottom rankings, state/category breakdowns |
| `compute_metrics` | Growth rates, share of total, descriptive stats, correlation, IQR outlier detection, trend slope, seasonality | Derived mathematical analysis on top of a query slice or raw table |
| `make_chart` | Returns interactive Plotly figure specifications (`json.loads(fig.to_json())`) | Explicit or implied requests for visual charts (line, bar, scatter, area) |
| `web_search` | DuckDuckGo web search via `ddgs` | External macroeconomic context, exchange rates, or industry benchmarks |

> **Honest Refusal (`unsupported` node)**: Out-of-scope inquiries (e.g. flight bookings, weather, cryptocurrency) receive an honest explanation of domain boundaries with recommended e-commerce analytical queries rather than hallucinations.

---

## Dataset: Brazilian E-Commerce (Olist)

- **Scale**: 112,650 consolidated customer orders across 2016–2018 (73 product categories, 27 Brazilian states).
- **Consolidated Master**: Flattened into `data/olist_master.csv` with derived date columns (`order_year`, `order_month`, `order_quarter`, `order_year_month`).
- **Memory Footprint**: Aggressive dtype downcasting (categoricals, `int8`/`int16`, `float32`) keeps active RAM usage at **~19.8 MB** (well below Render's 512MB free tier limit).

---

## Setup & Local Development

### 1. Backend (FastAPI + LangGraph)
```bash
# From workspace root
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env    # Configure GEMINI_API_KEY (optional) and DATABASE_URL
uvicorn main:app --reload --port 8000
```
Backend API will be live at: `http://localhost:8000` (`/health`, `/api/dataset/profile`, `/api/chat`).

### 2. Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be live at: `http://localhost:3000`.

### 3. Verification Suite
```bash
python scripts/test_phase2.py
python scripts/final_routing_check.py
```

---

## Production Deployment (Phase 4)

### 1. Database Checkpointer (Neon.tech PostgreSQL)
1. Create a free serverless PostgreSQL project at [Neon.tech](https://neon.tech).
2. Copy the connection string (e.g. `postgresql://user:password@ep-xyz.region.aws.neon.tech/neondb?sslmode=require`).
3. Set this as `DATABASE_URL` in your backend environment. LangGraph's `PostgresSaver` will automatically initialize tables on startup to maintain conversation history across server restarts.

### 2. Backend Deployment (Render.com)
1. In Render Dashboard, create a new **Web Service** and connect this repository:
   - **Root Directory**: `.`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
2. Add Environment Variables:
   - `GOOGLE_API_KEY`: Your Gemini API key
   - `DATABASE_URL`: Your Neon PostgreSQL connection string
   - `PYTHON_VERSION`: `3.11.9`
   - `BACKEND_CORS_ORIGINS`: `*`
3. Verify backend health once deployed: `curl https://<your-render-url>/health` (returns `{"status":"healthy","service":"insight-copilot"}`).

### 3. Frontend Deployment (Vercel)
1. In Vercel, import this repository:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
2. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL`: `https://<your-render-app>.onrender.com`
3. Deploy! The frontend includes cold-start detection that displays a smooth waking indicator if the backend is spinning up from idle.

---

## Evaluation Benchmark & Demo Queries

Insight Copilot is benchmarked against the 9 canonical evaluation queries:

| # | Query | Route | Expected Tools | Core Competency |
|---|---|---|---|---|
| 1 | *"hi there"* | `direct_answer` | *None* | Zero-tool greeting routing |
| 2 | *"What were the top 3 product categories by payment value?"* | `tools` | `query_data` | Structured aggregation & ranking |
| 3 | *"Is there a seasonal trend in bed_bath_table orders?"* | `tools` | `query_data` → `compute_metrics` | Multi-tool chained seasonality detection |
| 4 | *"Compare SP and RJ customer states by freight value and delivery time"* | `tools` | `query_data` → `compute_metrics` | Comparative metric synthesis |
| 5 | *"Plot monthly payment value for 2017"* | `tools` | `query_data` → `make_chart` | Inline interactive Plotly visual |
| 6 | *"Summarize anything unusual or anomalous in payment values"* | `tools` | `compute_metrics` | IQR outlier & skewness analysis |
| 7 | *"What about RJ?"* (follow-up) | `tools` | Resolves via checkpoint | Contextual pronoun resolution across turns |
| 8 | *"What's the weather in Mumbai?"* | `unsupported` | *None* | Domain boundary enforcement & honest refusal |
| 9 | *"Book me a flight"* | `unsupported` | *None* | Domain boundary enforcement & honest refusal |

---

## Key Design Principles
1. **Structured Tool Parameters over Arbitrary Code**: Prevents syntax errors, code injection, and hallucinated pandas functions.
2. **Transparent Reasoning Surface**: Exposes step-by-step thoughts, tool invocations, arguments, and summaries in the UI reasoning drawer.
3. **Graceful Error Recovery**: Tool validation errors provide closest-match suggestions (`difflib.get_close_matches`), enabling the agent to re-plan instead of throwing a traceback.
4. **Resilient Production Checkpointing**: Neon PostgreSQL `PostgresSaver` handles serverless cold-starts without losing user conversation context.

