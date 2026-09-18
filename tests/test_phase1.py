import sys
from pathlib import Path

# Configure utf-8 standard output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.src.data import get_dataset, load_and_clean_dataset
from backend.src.schema import get_dataset_profile, get_schema_prompt_text
from backend.src.graph import build_graph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage


def test_data_loading():
    print("--- 1. Testing Data Loading & Memory Footprint ---")
    df = get_dataset()
    row_count = len(df)
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"Rows: {row_count:,}")
    print(f"Columns: {list(df.columns)}")
    print(f"Memory Footprint: {mem_mb:.2f} MB")
    
    assert row_count > 50000, f"Expected >50,000 rows, got {row_count}"
    assert mem_mb < 35.0, f"Expected <35.0 MB RAM, got {mem_mb:.2f} MB"
    assert "order_year" in df.columns, "Derived column order_year missing"
    assert ("delivery_days" in df.columns or "profit_margin" in df.columns), "Derived analytics metric missing"
    print("[PASS] Data loading test PASSED (< 35 MB RAM).\n")


def test_schema_profiler():
    print("--- 2. Testing Schema Profiler ---")
    profile = get_dataset_profile()
    prompt_text = get_schema_prompt_text()
    
    assert profile["total_rows"] > 50000
    assert "category" in profile["categories"] or "Category" in profile["categories"]
    assert len(prompt_text) > 100
    print(f"Dataset name: {profile['dataset_name']}")
    print(f"Categories found: {list(profile['categories'].keys())}")
    print(f"Date range: {profile['date_range']}")
    print("[PASS] Schema profiler test PASSED.\n")


def test_graph_skeleton():
    print("--- 3. Testing LangGraph Skeleton Execution ---")
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": "test-session-1"}}
    
    # Test 1: Direct greeting
    inputs = {
        "messages": [HumanMessage(content="Hello! What can you do?")],
        "user_query": "Hello! What can you do?",
        "plan": "",
        "route": "direct_answer",
        "tool_plan": [],
        "tool_results": [],
        "iterations": 0,
        "reasoning_trace": [],
        "chart_spec": None,
        "final_answer": "",
        "error": None,
    }
    
    result = graph.invoke(inputs, config=config)
    print("Direct answer result final_answer snippet:", result["final_answer"][:80], "...")
    print(f"Reasoning trace steps: {len(result['reasoning_trace'])}")
    assert len(result["reasoning_trace"]) >= 2, "Expected plan and synthesis steps in trace"
    
    # Test 2: Tools route (stub execution in Phase 1)
    config2 = {"configurable": {"thread_id": "test-session-2"}}
    inputs2 = {
        "messages": [HumanMessage(content="What are the top 5 product categories by total sales in SP?")],
        "user_query": "What are the top 5 product categories by total sales in SP?",
        "plan": "",
        "route": "tools",
        "tool_plan": [],
        "tool_results": [],
        "iterations": 0,
        "reasoning_trace": [],
        "chart_spec": None,
        "final_answer": "",
        "error": None,
    }
    result2 = graph.invoke(inputs2, config=config2)
    print("Tool query result final_answer snippet:", result2["final_answer"][:80], "...")
    print(f"Tool query reasoning trace steps: {len(result2['reasoning_trace'])}")
    assert len(result2["reasoning_trace"]) >= 3, "Expected plan, tool_call, tool_result, and synthesis steps"
    print("[PASS] LangGraph skeleton execution test PASSED.\n")


if __name__ == "__main__":
    test_data_loading()
    test_schema_profiler()
    test_graph_skeleton()
    print("ALL PHASE 1 BACKEND TESTS PASSED SUCCESSFULLY WITH OLIST DATASET!")
