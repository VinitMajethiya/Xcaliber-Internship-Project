# README template

Fill the bracketed parts. Every section here maps to something the rubric explicitly asks for — don't drop any.

---

# Insight Copilot

A reasoning, tool-using analyst chatbot built with LangGraph. Ask questions about the Global Superstore sales dataset in plain English; the agent plans its approach, picks the tools it needs, and answers like an analyst rather than a query engine.

**Live app (frontend):** [Vercel URL]  
**Backend API:** [Render URL]  
**Deployment:** Backend on Render Starter (2 GB RAM, no sleep). Frontend on Vercel (free). Conversation state persisted in PostgreSQL on Neon.tech.

## Demo

[One screenshot of a chat answer with the reasoning panel open. This is the single highest-value thing in the README — it shows reasoning visibility without the reviewer needing to load the app.]

Try these:
- What were the top 3 products by revenue last quarter?
- Is there a seasonal trend in furniture sales?
- Compare APAC and EMEA performance and tell me what's driving the difference.
- Summarize anything unusual in this data.

## Architecture

```mermaid
[paste docs/graph.mmd]
```

The agent is a LangGraph `StateGraph` with a typed state object and two conditional edges:

- **`planner`** — reads the question plus a profile of the dataset (columns, distinct values, date range) and emits a structured plan: a rationale, a route, and an ordered tool plan.
- **`route_after_plan`** (conditional) — sends the query to the tool path, a direct answer, or an honest refusal.
- **`tool_executor`** — runs one tool per visit and may extend the plan based on what it finds.
- **`should_continue`** (conditional) — loops back for multi-step queries, moves to synthesis when the plan is exhausted or the iteration cap is hit, or diverts to error handling.
- **`synthesizer`** — turns tool output into an analyst-style answer: direct answer, supporting numbers, one takeaway.

State is checkpointed with `MemorySaver` keyed by a per-session `thread_id`, so follow-up questions resolve against prior context.

## Tools

| Tool | What it does | When the agent picks it |
|---|---|---|
| `query_data` | Filter / group / aggregate over the dataset via validated structured params | Questions asking for numbers, rankings, breakdowns |
| `compute_metrics` | Growth rates, share of total, descriptive stats, correlation, outliers, trend, seasonality | Derived analysis on top of a slice |
| `make_chart` | Returns a Plotly spec rendered inline | Explicit or implied requests for a visual |
| `web_search` | DuckDuckGo lookup | Context the dataset can't supply |

Tools are not always called — greetings and capability questions take a zero-tool path, and out-of-scope questions get a refusal rather than an invented answer.

## Dataset

Global Superstore Sales ([link]). Chosen because it carries geography, category, segment and date dimensions in one file, which covers region comparison, seasonality and anomaly questions without a join layer competing for build time. [N] rows, [date range], bundled at `data/global_superstore.csv`.

Preprocessing: [what you did — dtype coercion, derived date columns, anything dropped].

## Setup

### Backend (FastAPI + LangGraph)
```bash
git clone [repo]
cd insight-copilot/backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env    # add GOOGLE_API_KEY and DATABASE_URL (Neon.tech connection string)
uvicorn main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd insight-copilot/frontend
npm install
cp .env.local.example .env.local    # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# open http://localhost:3000
```

### Deployment
- **Backend:** Connect `backend/` to a Render web service. Set `GOOGLE_API_KEY` and `DATABASE_URL` in the Render environment dashboard. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Frontend:** Connect `frontend/` to Vercel. Set `NEXT_PUBLIC_API_URL` to the Render backend public URL in Vercel's environment variables. Zero further config needed.
- **Database:** Provision a free PostgreSQL database on Neon.tech. Copy the connection string as `DATABASE_URL`. LangGraph's `PostgresSaver.setup()` creates the required tables on first backend startup.

## Assumptions

- [e.g. "last quarter" resolves against the dataset's latest complete quarter, not today's calendar date — stated back to the user in the answer]
- [e.g. revenue is the `Sales` column, net of nothing; `Profit` is treated separately]
- [anything else you decided for the user]

## Known limitations

- Single-dataset only; no schema discovery for arbitrary uploads — the agent would need a new `schema.py` generation step to work on any CSV.
- `PostgresSaver` persists state per `thread_id` in Neon.tech; if the Neon free tier is paused due to 5 days of total inactivity, a brief connection delay may occur on the next backend request.
- No eval harness; tool-selection accuracy verified manually against the 9 demo queries listed above.
- Chart types are limited to four (`line`, `bar`, `scatter`, `area`) — adding `heatmap` or `box` would require extending `MakeChartArgs` and the Plotly rendering in the frontend.
- The synthesizer produces its full answer before streaming the final message to the frontend; individual token streaming would require a second SSE channel alongside the state-snapshot stream.

Be specific and honest here. Naming a real limitation reads as engineering judgment; an empty section reads as not having looked.
