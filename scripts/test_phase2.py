import sys
sys.path.insert(0, ".")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.src.graph import build_graph

def run_tests():
    graph = build_graph()

    test_cases = [
        ("Direct Greeting", "Hello! What can you help me with?"),
        ("Out-of-Scope Refusal", "Can you book me a flight to Rio de Janeiro?"),
        ("Single Tool (query_data)", "What are the top 3 product categories by total payment?"),
        ("Multi-Tool (query_data -> make_chart)", "Plot monthly payment volume over time."),
        ("Multi-Tool (query_data -> compute_metrics seasonality)", "Is there any seasonal trend in order volume?"),
        ("Multi-Tool (query_data -> compute_metrics comparison)", "Compare payment volume across top customer states."),
        ("Anomaly Detection (compute_metrics outliers)", "Summarize any unusual outliers in freight values."),
    ]

    all_passed = True

    for name, q in test_cases:
        print(f"\n{'='*20} Testing: {name} {'='*20}")
        print(f"Query: '{q}'")
        initial_state = {
            "messages": [],
            "user_query": q,
            "plan": None,
            "route": None,
            "tool_plan": [],
            "tool_results": [],
            "reasoning_trace": [],
            "chart_spec": None,
            "final_answer": None,
            "error": None,
            "iterations": 0,
        }
        config = {"configurable": {"thread_id": f"test_thread_{name.replace(' ', '_')}"}}
        res = graph.invoke(initial_state, config=config)
        route = res.get("route")
        iterations = res.get("iterations")
        tool_results = res.get("tool_results", [])
        trace = res.get("reasoning_trace", [])
        chart_spec = res.get("chart_spec")
        final_answer = res.get("final_answer", "")

        print(f"Route: {route}")
        print(f"Iterations: {iterations}")
        print(f"Tools Executed: {len(tool_results)}")
        print(f"Chart Generated: {'Yes' if chart_spec else 'No'}")
        print(f"Trace Steps ({len(trace)}):")
        for step in trace:
            stage = step.get("stage")
            title = step.get("title")
            print(f"   [{stage}] {title}")
        print(f"Final Answer Preview:\n   {final_answer[:200]}...")

        # Assertions
        if name == "Direct Greeting":
            assert route == "direct_answer", f"Expected direct_answer, got {route}"
        elif name == "Out-of-Scope Refusal":
            assert route == "unsupported", f"Expected unsupported, got {route}"
        elif name == "Multi-Tool (query_data -> make_chart)":
            assert route == "tools"
            assert chart_spec is not None, "Expected chart_spec to be populated"
            assert len(tool_results) == 2, f"Expected 2 tools, got {len(tool_results)}"
        elif name == "Multi-Tool (query_data -> compute_metrics seasonality)":
            assert route == "tools"
            assert len(tool_results) == 2, f"Expected 2 tools, got {len(tool_results)}"

    print("\n" + "="*50)
    print("ALL PHASE 2 GRAPH ROUTING AND TOOL TESTS PASSED!")
    print("="*50)

if __name__ == "__main__":
    run_tests()
