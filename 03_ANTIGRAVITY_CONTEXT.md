# AGENTS.md — Context for Antigravity

Drop this at the repo root as `AGENTS.md` so it's picked up automatically on every task. Keep `docs/01_ARCHITECTURE.md` and `docs/02_TOOLS_SPEC.md` in the repo and reference them in each prompt.

---

## Project

Building **Insight Copilot**: a LangGraph agent that answers natural-language questions about the Global Superstore sales dataset and returns analyst-style insights, wrapped in a Streamlit chat UI, deployed to Streamlit Community Cloud.

This is an internship assignment evaluated on agent *design*, not visual polish. The graph structure and the visible reasoning trace carry 45% of the grade.

## Stack — do not substitute

- Python 3.11
- `langgraph>=1.2,<2` (`StateGraph`, `add_conditional_edges`, `PostgresSaver`)
- `langchain-core` for tool definitions, `langchain-google-genai` for the LLM
- `fastapi` + `uvicorn` for the backend API (streaming SSE via `StreamingResponse`)
- `pandas` for data, `plotly` for chart specs, `pydantic` v2 for tool args
- `psycopg[binary]` + `langgraph-checkpoint-postgres` for persistent state (Neon.tech)
- **Next.js (React, TypeScript)** for the frontend, deployed to Vercel
- **Vercel** for frontend hosting (free, GitHub CI/CD)
- **Render.com** for backend hosting (free web service tier, persistent process)
- **Neon.tech** for PostgreSQL (free serverless tier, `DATABASE_URL` connection string)

## Non-negotiable constraints

1. **The graph shape in `docs/01_ARCHITECTURE.md` is fixed.** Do not collapse nodes, do not replace the graph with `create_react_agent`, do not use `AgentExecutor`. Both conditional edges must exist.
2. **State is a `TypedDict`**, defined once in `backend/src/state.py`, carried through every node.
3. **Tools take Pydantic-validated structured params.** No `eval`, no `exec`, no LLM-generated pandas strings, no LLM-generated SQL.
4. **No secrets in code or git.** Backend reads from environment variables (Render dashboard). Frontend reads from `.env.local` locally and Vercel environment variables in production. Ship `.env.example` and `frontend/.env.local.example` with empty values.
5. **`backend/main.py` contains no agent logic.** It imports `build_graph()` and renders state via FastAPI route handlers.
6. **Every tool returns the `ToolResult` envelope.** No bare DataFrames, no bare strings.
7. **The reasoning trace is structured data** (`list[ReasoningStep]`), never a formatted string built inside a node.
8. **Never let a traceback reach the chat.** Tool exceptions set `state["error"]` and route to `error_handler`.
9. **Use `PostgresSaver` (Neon.tech), not `MemorySaver`.** Conversation context must survive Render cold starts. The `thread_id` is sent by the frontend on every request and stored in the browser's `localStorage`.

## Style

- Type hints everywhere. Docstrings on every tool and node.
- One file, one responsibility. If a file passes ~200 lines, it's doing too much.
- Prompts live in `src/prompts.py` as named constants. No inline f-string prompts scattered through nodes.
- Commit after each working phase with a descriptive message. The commit history is part of what's evaluated.

## Build order — one prompt per phase

Give Antigravity these in sequence. Don't ask for the whole thing at once; the graph wiring needs to be reviewable before tools land on top of it.

**Phase 1 — foundation**
> Read `docs/01_ARCHITECTURE.md`. Create the repo structure, `requirements.txt` with pinned versions, `.gitignore`, `.env.example`, and `src/config.py` with a `get_llm()` factory reading `GOOGLE_API_KEY` from Streamlit secrets with an env fallback. Then implement `src/data.py` (cached CSV loader with dtype coercion and derived `order_year`/`order_quarter`/`order_month` columns) and `src/schema.py` (a `get_dataset_profile()` returning columns, dtypes, distinct values for low-cardinality columns, and the date range). No agent code yet.

**Phase 2 — graph skeleton**
> Implement `src/state.py`, `src/nodes.py`, `src/routers.py` and `src/graph.py` exactly as specified in `docs/01_ARCHITECTURE.md`. Tools are not built yet — have `tool_executor` return a stub result. The planner must use `with_structured_output` against a Pydantic `PlanModel`. Compile with `MemorySaver`. Add a `scripts/smoke_test.py` that invokes the graph with three queries ("hi", "top products by sales", "book me a flight") and prints the resulting state, so I can confirm routing works before tools exist.

**Phase 3 — tools**
> Implement all four tools per `docs/02_TOOLS_SPEC.md` in `src/tools/`, each returning the `ToolResult` envelope, each with `USE WHEN` / `DO NOT USE WHEN` docstrings. Build the `TOOL_REGISTRY` in `src/tools/__init__.py`. Wire `tool_executor` to dispatch against the registry and support `data_ref` chaining. Validate column names against the real dataframe and return a recoverable error on mismatch.

**Phase 4 — UI**
> Build the Next.js frontend per the UI contract in `docs/01_ARCHITECTURE.md` (section 6): sidebar with dataset summary (fetched from `/api/dataset/profile`) and clickable example question chips, chat window with streaming SSE responses from `/api/chat`, a collapsible reasoning panel rendering `reasoning_trace` step-by-step (plan → tool choice + why → result summary → synthesis), inline Plotly chart rendering when `chart_spec` is present in the streamed state, and a "New conversation" button that generates a fresh `uuid4` thread_id stored in `localStorage`. No agent logic in the frontend. Deploy frontend to Vercel and backend to Render; set `NEXT_PUBLIC_API_URL`, `GOOGLE_API_KEY`, and `DATABASE_URL` as environment variables on their respective platforms.

**Phase 5 — hardening**
> Add error handling across all tools, an `iterations` cap of 4, graceful handling of empty query results, and input guards for empty or very long messages. Then write `README.md` from `docs/04_README_TEMPLATE.md` and verify `docs/graph.mmd` renders.

## Review gates — check these yourself, don't trust the agent

After Phase 2: does `smoke_test.py` show three *different* routes for the three queries? If everything routes to `tools`, the planner prompt is wrong — fix it before adding tools.

After Phase 3: ask "plot monthly sales" and confirm exactly two tools fire, not four.

After Phase 4: open the app, ask a comparison question, and check the reasoning panel shows a second iteration. If multi-step never triggers, `should_continue` isn't re-planning.

Before deploy: `git log -p | grep -i "api_key\|AIza\|sk-"` must return nothing.
