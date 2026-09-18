# Write-up template

Half a page to one page. The brief says they're evaluating *how you think*, so this document is worth disproportionate effort relative to its length. Write it last, after you've hit real problems worth reporting.

Structure, roughly 5 short sections:

---

## 1. Dataset choice (2–3 sentences)

Justify it in terms of what the *agent* needed, not what the data was like. Something close to: the four sample questions in the brief span ranking, seasonality, regional comparison and anomaly detection; Global Superstore carries all four dimensions in one file, so tool-design time went into the routing problem rather than a join-planning problem. Note that you considered Olist and why you didn't take it.

## 2. Why the graph looks like this (the core section)

The most valuable thing you can explain is **why planning is a separate node from execution**. The easy version of this assignment is a ReAct loop where the model thinks and acts in one opaque step. Separating them gives you: a plan that exists in state before any tool fires, a route you can assert on in tests, and a reasoning trace that's structured data rather than scraped prose.

Also worth covering:
- Why two conditional edges instead of the required one — routing *whether* to use tools and routing *whether to continue* are different decisions and collapsing them made the planner prompt do too much.
- Why one tool per `tool_executor` visit rather than a batch — it makes multi-step sequences visible as distinct iterations in the trace, which is the thing being evaluated.

## 3. The trade-off you'd most expect to be challenged on

Pick one and own it. Candidates:

**Structured tool params over generated code.** You gave up the ability to answer arbitrary questions in exchange for tools that fail recoverably instead of silently. A `query_data` call with a bad column name returns a correctable error and the agent re-plans; a generated `df.query()` string either crashes or quietly returns the wrong rows. Note what this costs — genuinely novel analyses that don't fit the parameter schema fall through to the refusal path.

**Render Starter vs Free tier.** The free tier's 512 MB RAM cap is a real constraint for a stack that loads pandas, LangGraph, psycopg, and plotly into the same process. Upgrading to the Starter plan eliminated cold starts and OOM crashes for a $7 cost — a deliberate trade-off of money for reliability during evaluation. In production, the right fix is containerising the data loading into a separate lightweight service so the web process stays small.

Say which one you'd revisit first.

## 4. What broke and what you did about it

One or two real problems. Be specific — this is the section that distinguishes people who built it from people who prompted it. Likely candidates from this build:

- The planner routing everything to `tools` including greetings, fixed by [what you did to the prompt/schema]
- Date handling for relative phrases like "last quarter" — no "today" exists inside a static dataset, so you anchored to the dataset's latest complete period and surfaced that assumption in the answer
- Multi-step chaining not triggering until `data_ref` let the second tool consume the first tool's output

## 5. What you'd do with more time

Ranked, 4–5 items, each one sentence. Show that you know what "production" would mean:

1. An eval harness — a labelled set of ~40 queries with expected routes and tools, scored on selection accuracy, so prompt changes can be measured rather than eyeballed.
2. Streaming token output from the synthesizer (FastAPI `StreamingResponse` sending individual tokens) rather than the current whole-message flush when synthesis completes.
3. Schema-agnostic ingestion so the same graph works on an uploaded CSV, with `schema.py` regenerated at upload time from the actual file columns.
4. A caching layer on `query_data` — identical filter+group+agg combinations are re-computed on every follow-up; a simple LRU cache keyed on the args hash would eliminate most repeat work.
5. Migrate from `PostgresSaver` to a proper conversation store that also persists rendered chart specs and allows users to name and share threads.

---

**Tone note:** don't oversell. The reviewers said explicitly they care about reasoning over polish, and a write-up that names two real weaknesses reads far stronger than one that claims everything worked.
