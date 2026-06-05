# agent_finadvisor.py
print(">>> LOADED agent_finadvisor.py FROM:", __file__)
from typing import List, TypedDict, Annotated
import operator

from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition


# ---------------------------------------------------
# 1. Tools (plain-text input)
# ---------------------------------------------------

@tool
def calculate_risk(text: str) -> str:
    """Analyze portfolio risk from a plain-text description."""
    # TODO: replace this placeholder with real parsing + risk logic
    return f"[calculate_risk] Analyzed risk for: {text[:200]}..."

@tool
def summarize_portfolio(text: str) -> str:
    """Summarize a portfolio from a plain-text description."""
    # TODO: replace this placeholder with real summarization logic
    return f"[summarize_portfolio] Summary for: {text[:200]}..."

tools = [calculate_risk, summarize_portfolio]


# ---------------------------------------------------
# 2. LLMs (Groq)
# ---------------------------------------------------

# ReAct agent LLM: tool-calling enabled
react_llm = ChatGroq(
    model="llama-3.1-70b-versatile",
    groq_api_key="gsk_your_actual_key_here"  # <--- Done!,
).bind_tools(tools)

# Planner agent LLM: no tools, just structured reasoning
planner_llm = ChatGroq(
    model="llama-3.1-70b-versatile",
    groq_api_key="YOUR_GROQ_API_KEY_HERE",
)


# ---------------------------------------------------
# 3. ReAct Agent (LangGraph) — STEP 1
# ---------------------------------------------------

class ReactState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]


def react_call_model(state: ReactState) -> ReactState:
    """Core ReAct-style step: LLM thinks, may call tools, or answer."""
    response = react_llm.invoke(state["messages"])
    return {"messages": [response]}


react_tool_node = ToolNode(tools)

react_builder = StateGraph(ReactState)

react_builder.add_node("agent", react_call_model)
react_builder.add_node("tools", react_tool_node)

react_builder.add_conditional_edges(
    "agent",
    tools_condition,          # decides: call tools or finish
    {
        "tools": "tools",
        "end": END,
    },
)

react_builder.add_edge("tools", "agent")
react_builder.set_entry_point("agent")

react_graph = react_builder.compile()


def run_react_agent(text: str) -> str:
    """
    STEP 1:
    ReAct-style agent using LangGraph.
    - Input: plain-text portfolio description
    - Behavior: LLM decides when to call tools.
    """
    initial_state: ReactState = {
        "messages": [HumanMessage(content=text)]
    }
    final_state = react_graph.invoke(initial_state)
    last_message = final_state["messages"][-1]
    return last_message.content


# ---------------------------------------------------
# 4. Planner Agent (LangGraph) — STEP 2
#    Structured step-by-step reasoning (no tools)
# ---------------------------------------------------

class PlannerState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]


def planner_node(state: PlannerState) -> PlannerState:
    """
    Planner-style node:
    - Creates a clear, numbered plan
    - Then executes it logically in the same response
    """
    system_msg = SystemMessage(
        content=(
            "You are a financial planning assistant. "
            "Given the user's portfolio description, first create a clear, numbered plan "
            "(Step 1, Step 2, Step 3...), then execute that plan in detail. "
            "Always end with a concise 'Final Recommendation' section."
        )
    )
    messages = [system_msg] + state["messages"]
    response = planner_llm.invoke(messages)
    return {"messages": [response]}


planner_builder = StateGraph(PlannerState)
planner_builder.add_node("planner", planner_node)
planner_builder.set_entry_point("planner")
planner_builder.add_edge("planner", END)

planner_graph = planner_builder.compile()


def run_planner_agent(text: str) -> str:
    """
    STEP 2:
    Planner-style agent using LangGraph.
    - Input: plain-text portfolio description
    - Behavior: produces a structured plan + execution + final recommendation.
    """
    initial_state: PlannerState = {
        "messages": [HumanMessage(content=text)]
    }
    final_state = planner_graph.invoke(initial_state)
    last_message = final_state["messages"][-1]
    return last_message.content
