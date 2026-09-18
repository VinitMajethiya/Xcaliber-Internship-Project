# Insight Copilot — Build Roadmap

**Deadline:** 5 calendar days from receipt.
**Rule of thumb from the brief:** a rough UI over a genuinely well-structured LangGraph agent beats a beautiful UI over a hidden prompt. Spend your time on the graph and the reasoning trace, not on CSS.

---

## Decisions locked before any code

| Decision | Choice | Why |
|---|---|---|
| Dataset | **Olist Brazilian E-Commerce (112,650 records)** | Real-world Kaggle e-commerce fact table (`olist_master.csv`) with English product categories, customer/seller states, delivery lead times, review scores, freight, and payments. Unified table consumes only **19.71 MB RAM** (<40 MB limit). |
| LLM | **Gemini 2.x Flash** (free tier), Groq Llama as fallback | Free, fast, reliable structured output. Keep the provider behind one `get_llm()` factory so swapping is a one-line change. |
| Orchestration | **LangGraph 1.2.x** `StateGraph` + `PostgresSaver` | Required. Pin `langgraph>=1.2,<2`. Checkpointer swapped from in-process `MemorySaver` to `PostgresSaver` backed by Neon.tech so conversation context survives server restarts and satisfies the multi-turn context requirement. |
| UI | **Next.js (React)** | Proper decoupled frontend; custom collapsible reasoning panel, streaming SSE chat, inline Plotly charts, conversation history sidebar. Deployed to Vercel (free). |
| Backend | **FastAPI (Python 3.11)** | Async API layer that hosts the LangGraph agent, streams SSE responses, and manages thread lifecycle. Deployed to Render.com. |
| Frontend Hosting | **Vercel** | Free, zero-config GitHub CI/CD, perfect for Next.js. |
| Backend Hosting | **Render.com — Starter plan ($7/month)** | **Strongly recommended for evaluation week.** Free tier sleeps after 15 min (30–60 s cold start) and caps at 512 MB RAM — pandas + LangGraph + psycopg regularly breach that cap and crash silently. Starter gives 2 GB RAM, no sleep, no cold starts. Cancel after evaluation. If budget is truly $0, the Free tier works with RAM optimizations in `data.py` plus a cold-start spinner in the frontend — see mitigation notes in Day 4. |
| Conversation Persistence | **PostgreSQL on Neon.tech** (free serverless tier) | LangGraph `PostgresSaver` writes the full `AgentState` per checkpoint. Context genuinely survives across browser sessions and server restarts — a hard requirement for multi-turn follow-ups. |
| Dataset storage | Bundled `data/global_superstore.csv`, loaded once in FastAPI startup, cached | Brief explicitly allows it. |

If you want a harder dataset, swap to Olist — but only if you finish the graph by end of Day 2. See the note at the bottom.

---

## Day plan

### Day 1 — Skeleton and data floor
Goal: a graph that runs end to end with one real tool.

- [x] Repo created with `backend/` and `frontend/` top-level directories; `.gitignore` includes `.env`, `frontend/.env.local`, `backend/.env`
- [x] `backend/requirements.txt` pinned; `frontend/package.json` initialized
- [x] Dataset cleaned via `scripts/prepare_olist.py` and saved to `data/olist_master.csv` (112,650 rows, 19.71 MB RAM after downcasting)
- [x] `backend/src/data.py` — cached loader, **aggressive dtype optimization** (downcast int64→int32, float64→float32, object→category for Region/Category/Segment/Ship Mode; target <40 MB in RAM), derived columns (`order_year`, `order_quarter`, `order_month`)
- [x] `backend/src/schema.py` — a **dataset profile** dict (columns, dtypes, distinct values for low-cardinality columns, date range). This gets injected into the planner prompt so the agent knows what it can ask for.
- [x] `AgentState` TypedDict defined in `backend/src/state.py`
- [x] `planner` → `synthesizer` graph compiles and runs with one hardcoded tool result
- [x] `backend/main.py` exposes `/health` + `/api/chat` (stub) and echoes graph output

### Day 2 — Tools and routing
Goal: all four tools real, conditional edge working.

- [x] `query_data` implemented with a **structured-params** contract (not free-form code)
- [x] `compute_metrics` implemented
- [x] `make_chart` implemented, returns a spec not an image
- [x] `web_search` implemented
- [x] Planner emits structured JSON: `rationale`, `route`, `tool_plan`
- [x] `route_after_plan` conditional edge routes to `tool_executor` / `direct_answer` / `unsupported`
- [x] `should_continue` conditional edge enables multi-tool sequences (cap at 4 iterations)
- [x] `unsupported` node returns an honest "I don't have a tool for that"

### Day 3 — Reasoning surface and insight quality
Goal: an evaluator can see the agent think.

- [ ] Reasoning trace accumulated in state as structured steps (`list[ReasoningStep]`), not a blob of text
- [ ] Next.js `ReasoningPanel` component renders: plan → tool chosen + why → args → result summary
- [ ] Synthesizer prompt enforces the three-part answer shape (answer / numbers / why it matters)
- [ ] Plotly charts render inline in `ChartCanvas` component when `chart_spec` is present in SSE stream
- [ ] `PostgresSaver` (Neon.tech) checkpointer + `thread_id` (stored in `localStorage`) so follow-ups resolve pronouns ("what about the other region?") even after Render restarts
- [ ] Error handling: tool exception → `error_handler` node → graceful JSON error response → user-facing message in UI, never a raw traceback

### Day 4 — Deploy and harden

**Hosting decision — make this call before deploying:**
> For evaluation week, upgrade to **Render Starter ($7/month)**: no sleep, 2 GB RAM, zero cold-start embarrassment. Cancel after evaluation. If using Free tier, apply the RAM mitigations in `data.py` (dtype downcast + category columns) and implement the cold-start spinner in the frontend.

- [ ] Provision Neon.tech PostgreSQL database (free serverless tier); copy the connection string as `DATABASE_URL`
- [ ] Deploy FastAPI backend to Render.com — connect `backend/` directory; set `GOOGLE_API_KEY` + `DATABASE_URL` in Render environment dashboard; start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Verify backend `/health` returns 200 on the Render public URL **before** wiring the frontend
- [ ] Deploy Next.js frontend to Vercel — connect `frontend/` directory; set `NEXT_PUBLIC_API_URL` to the Render backend URL
- [ ] Verify frontend loads in a cold incognito window and completes a full query round-trip
- [ ] **If on Free tier:** confirm the frontend cold-start spinner fires correctly (health-poll loop with "Waking up the backend (~30 s)" message)
- [ ] **Pre-warm check:** hit the app from your phone 5 minutes before evaluation; confirm Render is awake
- [ ] Run all 9 demo queries from the test table below against the **hosted** app (not localhost)
- [ ] `README.md` written from the template
- [ ] Mermaid architecture diagram rendering correctly on GitHub

### Day 5 — Write-up and buffer
- [ ] `WRITEUP.md` finished (design decisions, trade-offs, what's next)
- [ ] `docs/` folder committed so reviewers see your thinking
- [ ] Commit history is clean and tells a story — not one "initial commit" dump
- [ ] Reply to the email with: hosted URL, repo link, write-up

---

## Rubric-mapped acceptance checklist

Run through this before you submit. Each line is a point you're being scored on.

**LangGraph architecture (25%)**
- [ ] `StateGraph` with a `TypedDict` state, not a dict passed around
- [ ] At least **two** conditional edges (route_after_plan, should_continue) — the brief asks for one, give two
- [ ] Checkpointer wired, state genuinely persists across turns
- [ ] Nodes are single-responsibility and individually testable
- [ ] No node contains a giant prompt doing everything

**Reasoning quality (20%)**
- [ ] Plan is produced **before** any tool call, and stored in state
- [ ] Trace says *why* a tool was picked, not just which one
- [ ] Multi-step queries show a visible second iteration
- [ ] Trace is visible in the hosted UI without touching the code

**Tool selection (20%)**
- [ ] A greeting ("hi") calls **zero** tools
- [ ] "Plot revenue by month" calls the chart tool, not all four
- [ ] "Who won the World Cup" gets `unsupported` or `web_search`, never a hallucinated number
- [ ] At least one demo query chains two tools

**Insight generation (15%)**
- [ ] No raw DataFrame dumped as the final answer
- [ ] Every numeric answer carries its supporting figure
- [ ] Every answer ends with a takeaway line

**Engineering quality (10%)**
- [ ] Zero secrets in git history (check with `git log -p | grep -i "api_key"`)
- [ ] `src/` package structure, not one 900-line file
- [ ] Type hints and docstrings on tools (the docstrings ARE the tool descriptions the LLM reads)
- [ ] README covers setup, architecture, tools, limitations, assumptions

**Hosting & UX (10%)**
- [ ] Frontend public URL (Vercel) works cold, in incognito
- [ ] Backend public URL (Render) returns 200 on `/health` cold
- [ ] App doesn't crash on gibberish input
- [ ] Example questions shown as clickable starters in the UI
- [ ] Conversation context persists across browser refresh (PostgreSQL checkpointer via `thread_id` stored in localStorage)
- [ ] Cold-start spinner visible when Render backend is waking; no raw timeout error shown to user
- [ ] No secrets committed to git (`git log -p | grep -i "api_key\|DATABASE_URL"` returns nothing)

---

## Demo queries to test against (and to list in your README)

| Query | Expected route | Tools |
|---|---|---|
| "hi there" | direct_answer | none |
| "What were the top 3 products by revenue last quarter?" | tools | query_data |
| "Is there a seasonal trend in furniture sales?" | tools | query_data → compute_metrics |
| "Compare APAC and EMEA and tell me what's driving the difference" | tools | query_data → compute_metrics |
| "Plot monthly sales for 2014" | tools | query_data → make_chart |
| "Summarize anything unusual in this data" | tools | query_data → compute_metrics (outliers) |
| "What about the other one?" (follow-up) | tools | resolves via checkpointed context |
| "What's the weather in Mumbai?" | unsupported | none, or web_search |
| "Book me a flight" | unsupported | none |

---

## Scope discipline

**Cut first if you're behind:** web_search tool, code-execution tool, chart styling, multi-dataset support.
**Never cut:** the conditional edges, the visible reasoning trace, the PostgreSQL checkpointer, the README.

**Render Free tier RAM mitigations (if not on Starter):**
Apply all of these in `backend/src/data.py` at load time to keep the in-memory DataFrame under 40 MB:
```python
df["Sales"] = df["Sales"].astype("float32")
df["Profit"] = df["Profit"].astype("float32")
df["Quantity"] = df["Quantity"].astype("int16")
for col in ["Region", "Category", "Sub-Category", "Segment", "Ship Mode", "Country", "City"]:
    if col in df.columns:
        df[col] = df[col].astype("category")
```
Run `df.info(memory_usage="deep")` before and after — you should see a >50% reduction.

**Olist swap note:** only consider it if the graph is done by end of Day 2. It adds a join-planning problem that eats a full day and the rubric gives you nothing extra for it. Difficulty of dataset is not a scored criterion.
