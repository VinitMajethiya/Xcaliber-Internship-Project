# 08 — Fix Guide (Audit Response)

Current score: **85/100**. Tasks 1–3 alone recover 12 points and take under 40 minutes combined — do those first, in this order, then decide whether Tasks 4–6 are worth the remaining time.

---

## Fix 1 — README: Known Limitations & Assumptions (+2 pts, ~5 min)

Append this to `README.md`. Adjust anything bracketed or that doesn't match your actual build — this is written from what the audit could see (Neon-backed checkpointer, 4-iteration cap, the specific tools you shipped), but you know the code better than an outside read of it does.

```markdown
## Assumptions

- Relative time phrases ("recent", "last quarter") resolve against the dataset's own
  date range, not today's calendar date, since the dataset is static — the agent
  surfaces this resolution back to the user rather than silently guessing.
- Numeric questions about revenue/payment totals are answered against the dataset's
  own payment columns as provided, with no currency conversion or inflation adjustment.
- When a question is ambiguous but reasonably answerable, the agent picks the most
  likely interpretation and proceeds rather than blocking on a clarifying question.

## Known limitations

- Conversation history persists via a Postgres checkpointer (Neon) when `DATABASE_URL`
  is set, falling back to an in-process `MemorySaver` otherwise — in the fallback case,
  history is lost on backend restart.
- The tool set and reasoning are scoped to this one dataset; there's no schema-agnostic
  ingestion for a different uploaded dataset.
- No automated eval harness exists yet — tool-selection accuracy was verified manually
  against the fixed query set in `scripts/final_routing_check.py`, not a labeled benchmark.
- Tool chains are capped at 4 iterations; a question genuinely needing a 5th step gets
  a partial answer, with that gap acknowledged in the response rather than hidden.
- `make_chart` covers the chart types implemented in `ChartCanvas.tsx` — not every
  possible visualization request is supported.
```

---

## Fix 2 — Synthesizer negative constraint (+2 pts, ~3 min)

In `backend/src/prompts.py`, find `SYNTHESIZER_SYSTEM_PROMPT` (the one with the "1. Direct Answer / 2. Supporting Numbers / 3. Strategic Takeaway" structure the audit quoted) and add this line right after that three-part structure is defined:

```python
IMPORTANT: Never reproduce tool output as a raw table, a bullet-per-row list, or a
JSON dump. Weave every number into the prose of the three sections above. Only
produce a markdown table if the user explicitly asked for a table.
```

This is a one-line insertion — no restructuring needed since the three-part shape is already working (the live output example in the audit proves that). This just closes the gap where the prompt *hopes* the model won't dump raw output instead of *forbidding* it.

---

## Fix 3 — Deploy both services (+8 pts, ~30 min)

This is the highest-value item by a wide margin. The 404 with `x-render-routing: no-server` means Render has no live service at that URL at all — not sleeping, not deployed. Fastest path to fix:

**Backend on Render:**
1. Render dashboard → New → Web Service → connect the GitHub repo, root directory `backend/`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT` (Render injects `$PORT`, don't hardcode 8000/7860)
4. Environment → add `GOOGLE_API_KEY` and `DATABASE_URL` (your Neon connection string) as secrets — never in `render.yaml` or committed config
5. Deploy, then wait for the build to go green, then hit `https://<your-service>.onrender.com/health` yourself and confirm `200`, not 404, before moving on

**Frontend on Vercel:**
1. Vercel dashboard → New Project → same repo, root directory `frontend/`
2. Environment variable: `NEXT_PUBLIC_API_URL` = the live Render URL from step above
3. Deploy, then open the resulting URL yourself and confirm it says "Insight Copilot" and not a stale/unrelated cached project — if `insight-copilot.vercel.app` is genuinely owned by something else, deploy under a fresh project name rather than fighting for that slug

**Then, not before:**
4. Update the backend's CORS `FRONTEND_ORIGIN` env var on Render to the *actual* Vercel URL you just got (not a placeholder) — a mismatched origin here silently breaks every request even though both services individually look "up"
5. Update `README.md`'s hosted URLs at the top — replace both placeholders with the real, tested links
6. Re-run the demo query list from `00_ROADMAP.md` against the **live** URLs, not localhost, before considering this done

Skipping step 6 is how a deployment looks done and isn't — the earlier audit round almost certainly would have passed if someone had actually clicked the link once.

---

## Fix 4 — Reorganize `docs/` (+1 pt, ~5 min)

```bash
mkdir -p docs
git mv 00_ROADMAP.md 01_ARCHITECTURE.md 02_TOOLS_SPEC.md \
       03_ANTIGRAVITY_CONTEXT.md 04_README_TEMPLATE.md \
       05_WRITEUP_TEMPLATE.md 06_PLANNER.md 07_PROJECT_AUDIT_PROMPT.md \
       DESIGN.md docs/
```

Then create `docs/graph.mmd` containing just the Mermaid block (the fenced code between ` ```mermaid ` and ` ``` `) already embedded in your README — extract it into its own file so it matches what `01_ARCHITECTURE.md` promises exists. Commit both moves together so the diff is legible.

---

## Fix 5 — Correct `.env.example` paths (+1 pt, ~2 min)

```bash
cp .env.example backend/.env.example
cp frontend/.env.local.example frontend/.env.example
git add backend/.env.example frontend/.env.example
```

Leave the originals in place too if any local dev script or `.gitignore` entry references them by their current names — this fix is additive, not a rename, so nothing breaks by having both.

---

## Fix 6 — Visually split the three insight sections (+1 pt, ~20 min, lowest ROI)

The model is already outputting the three-header markdown shape (proven by the audit's live example) — the fix is parsing that in `MessageBubble.tsx` instead of restructuring the backend state. A backend field split (`finding`/`metrics`/`why_it_matters`) would be the "correct" long-term fix per `DESIGN.md` §2.1, but it's not worth it for 1 point this close to submission — parse the markdown you already have instead.

```tsx
// frontend/src/lib/parseAnalystAnswer.ts
export function parseAnalystAnswer(markdown: string) {
  const sections = { finding: "", metrics: "", whyItMatters: "" };
  const parts = markdown.split(/^### /m).filter(Boolean);
  for (const part of parts) {
    const [headerLine, ...rest] = part.split("\n");
    const body = rest.join("\n").trim();
    const header = headerLine.toLowerCase();
    if (header.includes("direct answer")) sections.finding = body;
    else if (header.includes("supporting")) sections.metrics = body;
    else if (header.includes("takeaway") || header.includes("matters")) {
      sections.whyItMatters = body;
    }
  }
  // Fall back to the raw markdown as `finding` if headers weren't found,
  // so an off-format response still renders instead of showing nothing.
  if (!sections.finding && !sections.metrics && !sections.whyItMatters) {
    sections.finding = markdown;
  }
  return sections;
}
```

In `MessageBubble.tsx`, replace the single `.analyst-prose` block with three, reusing whatever dark-theme tokens `globals.css` already defines (don't introduce new colors — match the existing graphite/hairline-border look):

```tsx
const { finding, metrics, whyItMatters } = parseAnalystAnswer(message.finalAnswer);

<div className="space-y-3">
  {finding && <p className="text-[15px] font-semibold leading-snug">{finding}</p>}
  {metrics && (
    <div className="analyst-prose rounded-md border border-border bg-surface-2 p-3 text-sm">
      <ReactMarkdown>{metrics}</ReactMarkdown>
    </div>
  )}
  {whyItMatters && (
    <div className="rounded-r-md border-l-2 border-accent bg-background/40 px-3 py-2 text-sm text-muted-foreground">
      💡 {whyItMatters}
    </div>
  )}
</div>
```

If the header text the model actually produces doesn't exactly match `"Direct Answer"` / `"Supporting"` / `"Takeaway"` (it's LLM-generated prose, so it can drift), loosen the `.includes()` checks or, better, pin the exact three header strings in the synthesizer prompt so parsing is reliable rather than fuzzy-matched.

---

## After all six

Re-run the audit prompt from `docs/07_PROJECT_AUDIT_PROMPT.md` against the repo once more — specifically re-check Section A (deliverables) and Section G (hosting), since those are the two that depend on live infrastructure rather than code, and are exactly the two most likely to still be wrong even after you believe they're fixed.