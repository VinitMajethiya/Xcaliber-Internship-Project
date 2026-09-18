import sys
sys.path.insert(0, ".")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.src.graph import build_graph
graph = build_graph()

tests = [
    ("hi there", "direct_answer"),
    ("Can you book me a flight to Paris?", "unsupported"),
    ("What is the weather in Mumbai?", "unsupported"),
    ("What are the top 3 categories by total payment?", "tools"),
    ("Is there a seasonal trend in total payment volume?", "tools"),
    ("Compare payment volume across customer states.", "tools"),
    ("Plot monthly payment volume over time.", "tools"),
    ("Summarize anything unusual in this data.", "tools"),
]

print("FULL DEMO QUERY ROUTING CHECK")
print("=" * 60)
all_pass = True
for name, expected_route in tests:
    state = {
        "messages": [], "user_query": name, "plan": None, "route": None,
        "tool_plan": [], "tool_results": [], "reasoning_trace": [],
        "chart_spec": None, "final_answer": None, "error": None, "iterations": 0,
    }
    config = {"configurable": {"thread_id": "final_check_" + name[:15].replace(" ", "_")}}
    res = graph.invoke(state, config=config)
    route = res.get("route")
    tools_used = [tr.get("tool") for tr in res.get("tool_results", [])]
    chart = res.get("chart_spec") is not None
    trace_has_why = any("Reason:" in step.get("detail", "") for step in res.get("reasoning_trace", []))

    ok = route == expected_route
    all_pass = all_pass and ok
    icon = "[PASS]" if ok else "[FAIL]"
    print(f"{icon} \"{name[:50]}\"")
    print(f"       route={route} (expected={expected_route}) | tools={tools_used} | chart={chart} | trace_has_why={trace_has_why}")

print()
print("RESULT:", "ALL PASS" if all_pass else "SOME FAILED")
