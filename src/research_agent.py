"""
Web research graph with LangGraph.

    START -> understand_goal -> create_plan -> search_web -> write_report -> END

Given a question such as "How is the EV market in India?", the graph:
  1. understand_goal : turns the question into a research goal   (deterministic)
  2. create_plan     : turns the goal into a list of search queries (deterministic)
  3. search_web      : runs each query on the internet and collects results
  4. write_report    : summarises the results into a cited answer (LLM)

Each node prints its input context and output. The LLM report stage also
prints input/output token counts from the model response.

Install:
    pip install langgraph ddgs langchain-anthropic

Set your key (only needed for the LLM report; without it a simple
snippet-based report is produced instead):
    export ANTHROPIC_API_KEY="sk-ant-..."

Run:
    python web_research_graph.py
    python web_research_graph.py "How is the EV market in India?"
"""

import os
import re
import sys
from datetime import date
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph


# ---------------------------------------------------------------------------
# 1. State
# ---------------------------------------------------------------------------
class ResearchState(TypedDict):
    question: str                  # input from the user
    topic: str                     # written by understand_goal
    goal: str                      # written by understand_goal
    plan: List[str]                # written by create_plan (search queries)
    search_results: List[Dict]     # written by search_web
    report: str                    # written by write_report
    model_calls: List[Dict]        # token usage for every LLM call


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
def _truncate(value: Any, limit: int = 500) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [{len(text) - limit} more chars]"


def _tokens_from_message(message: Any) -> Dict[str, int]:
    """Read input/output tokens from a LangChain AIMessage (Anthropic or others)."""
    usage = getattr(message, "usage_metadata", None) or {}
    if usage:
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (input_tokens + output_tokens))
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    meta = getattr(message, "response_metadata", None) or {}
    nested = meta.get("usage") or meta.get("token_usage") or {}
    input_tokens = int(
        nested.get("input_tokens")
        or nested.get("prompt_tokens")
        or 0
    )
    output_tokens = int(
        nested.get("output_tokens")
        or nested.get("completion_tokens")
        or 0
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def print_stage(
    name: str,
    context: Dict[str, Any],
    output: Dict[str, Any],
    tokens: Optional[Dict[str, Any]] = None,
) -> None:
    print(f"\n{'=' * 72}")
    print(f"STAGE: {name}")
    print("-" * 72)
    print("Context (input):")
    for key, value in context.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            print(f"  {key}: {len(value)} items")
            for i, item in enumerate(value, 1):
                title = item.get("title") or item.get("query") or item
                print(f"    {i}. {_truncate(title, 120)}")
        elif isinstance(value, list):
            print(f"  {key}:")
            for i, item in enumerate(value, 1):
                print(f"    {i}. {_truncate(item, 200)}")
        else:
            print(f"  {key}: {_truncate(value, 800)}")

    print("Output:")
    for key, value in output.items():
        if key == "model_calls":
            continue
        if isinstance(value, list) and value and isinstance(value[0], dict):
            print(f"  {key}: {len(value)} items")
            for i, item in enumerate(value, 1):
                title = item.get("title") or item.get("query") or item
                url = item.get("url", "")
                extra = f" ({url})" if url else ""
                print(f"    {i}. {_truncate(title, 120)}{extra}")
        elif isinstance(value, list):
            print(f"  {key}:")
            for i, item in enumerate(value, 1):
                print(f"    {i}. {_truncate(item, 200)}")
        else:
            print(f"  {key}: {_truncate(value, 800)}")

    if tokens:
        print(
            "Model tokens: "
            f"input={tokens['input_tokens']}  "
            f"output={tokens['output_tokens']}  "
            f"total={tokens['total_tokens']}  "
            f"model={tokens.get('model', 'unknown')}"
        )
    else:
        print("Model tokens: n/a (no LLM call in this stage)")
    print("=" * 72)


# ---------------------------------------------------------------------------
# 2. Nodes
# ---------------------------------------------------------------------------
def understand_goal(state: ResearchState) -> dict:
    """Reads: question   |   Updates: topic, goal   (deterministic)"""
    question = state["question"].strip()

    # Strip leading question words to get the subject: "How is the EV market
    # in India?" -> "EV market in India"
    topic = re.sub(
        r"^(how|what|why|when|where|who|which)\s+(is|are|was|were|do|does|did)?\s*(the)?\s*",
        "",
        question,
        flags=re.IGNORECASE,
    ).rstrip("?. ").strip()

    goal = f"Research the internet and give a well-sourced answer to: {question}"
    output = {"topic": topic or question, "goal": goal}
    print_stage("understand_goal", {"question": question}, output)
    return output


def create_plan(state: ResearchState) -> dict:
    """Reads: topic, question   |   Updates: plan   (deterministic)"""
    topic = state["topic"]
    year = date.today().year

    # Different angles so results are not all the same page
    plan = [
        state["question"],
        f"{topic} overview {year}",
        f"{topic} market size growth statistics {year}",
        f"{topic} key players market share",
        f"{topic} government policy incentives",
        f"{topic} challenges and outlook",
        f"{topic} latest news",
    ]
    output = {"plan": plan}
    print_stage(
        "create_plan",
        {"question": state["question"], "topic": topic, "year": year},
        output,
    )
    return output


def search_web(state: ResearchState) -> dict:
    """Reads: plan   |   Updates: search_results   (calls the internet)"""
    from ddgs import DDGS  # imported here so the file loads even if not installed

    results: List[Dict] = []
    seen_urls = set()

    with DDGS() as ddgs:
        for query in state["plan"]:
            try:
                hits = ddgs.text(query, max_results=5)
            except Exception as exc:  # network / rate-limit errors
                print(f"[search_web] '{query}' failed: {exc}")
                continue

            for hit in hits:
                url = hit.get("href")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                results.append(
                    {
                        "query": query,
                        "title": hit.get("title", ""),
                        "url": url,
                        "snippet": hit.get("body", ""),
                    }
                )

    output = {"search_results": results}
    print_stage("search_web", {"plan": state["plan"]}, output)
    return output


def write_report(state: ResearchState) -> dict:
    """Reads: question, goal, search_results   |   Updates: report"""
    results = state["search_results"]
    context = {
        "question": state["question"],
        "goal": state["goal"],
        "search_results": results,
    }
    prior_calls = list(state.get("model_calls") or [])

    if not results:
        output = {
            "report": "No search results were found. Check your network or try again.",
            "model_calls": prior_calls,
        }
        print_stage("write_report", context, output)
        return output

    # Number the sources so the model (or the fallback) can cite them
    sources_text = "\n\n".join(
        f"[{i}] {r['title']}\nURL: {r['url']}\n{r['snippet']}"
        for i, r in enumerate(results, start=1)
    )

    # Fallback: no API key -> return a plain digest of what was found
    if not os.getenv("ANTHROPIC_API_KEY"):
        lines = [f"Question: {state['question']}", "", "Top findings (no LLM key set):"]
        lines += [f"- [{i}] {r['title']}: {r['snippet'][:200]}" for i, r in enumerate(results[:8], 1)]
        lines += ["", "Sources:"] + [f"[{i}] {r['url']}" for i, r in enumerate(results, 1)]
        output = {"report": "\n".join(lines), "model_calls": prior_calls}
        print_stage("write_report", context, output)
        return output

    from langchain_anthropic import ChatAnthropic

    model_name = "claude-sonnet-5-5"
    llm = ChatAnthropic(model=model_name, max_tokens=1500)
    prompt = (
        f"Goal: {state['goal']}\n\n"
        "Using ONLY the numbered search results below, write a concise research "
        "report with: a short summary, key facts and figures, main players, "
        "policy/outlook, and open uncertainties. Cite sources like [1], [2]. "
        "If sources conflict or data is missing, say so.\n\n"
        f"SEARCH RESULTS:\n{sources_text}"
    )
    message = llm.invoke(prompt)
    answer = message.content
    token_usage = _tokens_from_message(message)
    prior_calls.append(
        {
            "stage": "write_report",
            "model": model_name,
            **token_usage,
        }
    )

    source_list = "\n".join(f"[{i}] {r['title']} - {r['url']}" for i, r in enumerate(results, 1))
    output = {
        "report": f"{answer}\n\nSources:\n{source_list}",
        "model_calls": prior_calls,
    }
    print_stage(
        "write_report",
        {**context, "prompt": prompt},
        output,
        tokens={"model": model_name, **token_usage},
    )
    return output


# ---------------------------------------------------------------------------
# 3. Build and compile the graph
# ---------------------------------------------------------------------------
builder = StateGraph[ResearchState, None, ResearchState, ResearchState](ResearchState)

builder.add_node("understand_goal", understand_goal)
builder.add_node("create_plan", create_plan)
builder.add_node("search_web", search_web)
builder.add_node("write_report", write_report)

builder.add_edge(START, "understand_goal")
builder.add_edge("understand_goal", "create_plan")
builder.add_edge("create_plan", "search_web")
builder.add_edge("search_web", "write_report")
builder.add_edge("write_report", END)

graph = builder.compile()


# ---------------------------------------------------------------------------
# 4. Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "How is the EV market in India?"

    final_state = graph.invoke(
        {
            "question": question,
            "topic": "",
            "goal": "",
            "plan": [],
            "search_results": [],
            "report": "",
            "model_calls": [],
        }
    )

    print("\n=== Final state ===")
    print(f"question       : {final_state['question']}")
    print(f"topic          : {final_state['topic']}")
    print(f"goal           : {final_state['goal']}")
    print("plan           :")
    for i, q in enumerate(final_state["plan"], 1):
        print(f"  {i}. {q}")
    print(f"search_results : {len(final_state['search_results'])} results")

    print("\n=== Token usage ===")
    calls = final_state.get("model_calls") or []
    if not calls:
        print("No LLM calls were made (deterministic stages, or ANTHROPIC_API_KEY is unset).")
    else:
        total_in = total_out = 0
        for i, call in enumerate(calls, 1):
            total_in += call["input_tokens"]
            total_out += call["output_tokens"]
            print(
                f"  {i}. stage={call['stage']}  model={call['model']}  "
                f"input={call['input_tokens']}  output={call['output_tokens']}  "
                f"total={call['total_tokens']}"
            )
        print(f"  All calls: input={total_in}  output={total_out}  total={total_in + total_out}")

    print("\n=== Report ===")
    print(final_state["report"])


# ---------------------------------------------------------------------------
# Which fields does each node read and update?
#
#   Node             | Reads                            | Updates
#   -----------------|----------------------------------|----------------
#   understand_goal  | question                         | topic, goal
#   create_plan      | topic, question                  | plan
#   search_web       | plan                             | search_results
#   write_report     | question, goal, search_results   | report, model_calls
# ---------------------------------------------------------------------------