from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from backend.app.graph.state import AnalysisState
from backend.app.agents.document_agent import document_agent_node
from backend.app.agents.extraction_agent import extraction_agent_node
from backend.app.agents.red_flag_agent import red_flag_agent_node
from backend.app.agents.comparison_agent import comparison_agent_node
from backend.app.agents.research_agent import research_agent_node
from backend.app.agents.report_agent import report_agent_node
from backend.app.utils.logging import logger

def route_request(state: AnalysisState) -> Literal[
    "document_agent",
    "extraction_agent",
    "red_flag_agent",
    "comparison_agent",
    "research_agent",
    "report_agent"
]:
    """
    Dynamically routes user requests strictly to the required agent,
    preventing unnecessary agent execution to conserve CPU/RAM.
    """
    req_type = state.get("request_type", "research")
    logger.info(f"[Workflow Router] Routing request_type: '{req_type}'")

    if req_type == "document":
        return "document_agent"
    elif req_type == "metrics":
        return "extraction_agent"
    elif req_type == "red_flags":
        return "red_flag_agent"
    elif req_type == "comparison":
        return "comparison_agent"
    elif req_type == "report":
        # Report pipeline runs extraction -> red_flag -> report
        return "extraction_agent"
    else:
        return "research_agent"

def build_workflow():
    builder = StateGraph(AnalysisState)

    # Register all 6 logical agents as nodes
    builder.add_node("document_agent", document_agent_node)
    builder.add_node("extraction_agent", extraction_agent_node)
    builder.add_node("red_flag_agent", red_flag_agent_node)
    builder.add_node("comparison_agent", comparison_agent_node)
    builder.add_node("research_agent", research_agent_node)
    builder.add_node("report_agent", report_agent_node)

    # Conditional start routing
    builder.add_conditional_edges(
        START,
        route_request,
        {
            "document_agent": "document_agent",
            "extraction_agent": "extraction_agent",
            "red_flag_agent": "red_flag_agent",
            "comparison_agent": "comparison_agent",
            "research_agent": "research_agent",
            "report_agent": "report_agent",
        }
    )

    # Edge logic for standalone agents vs report pipeline
    builder.add_edge("document_agent", END)
    builder.add_edge("comparison_agent", END)
    builder.add_edge("research_agent", END)
    builder.add_edge("report_agent", END)

    # Conditional route after extraction_agent: if part of report pipeline, proceed to red_flag_agent; else END
    def after_extraction(state: AnalysisState) -> str:
        if state.get("request_type") == "report":
            return "red_flag_agent"
        return END

    builder.add_conditional_edges(
        "extraction_agent",
        after_extraction,
        {
            "red_flag_agent": "red_flag_agent",
            END: END
        }
    )

    # Conditional route after red_flag_agent: if part of report pipeline, proceed to report_agent; else END
    def after_red_flag(state: AnalysisState) -> str:
        if state.get("request_type") == "report":
            return "report_agent"
        return END

    builder.add_conditional_edges(
        "red_flag_agent",
        after_red_flag,
        {
            "report_agent": "report_agent",
            END: END
        }
    )

    return builder.compile()

# Cached compiled workflow graph
_compiled_workflow = None

def get_workflow():
    global _compiled_workflow
    if _compiled_workflow is None:
        _compiled_workflow = build_workflow()
    return _compiled_workflow

def run_analysis_workflow(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the LangGraph multi-agent workflow."""
    workflow = get_workflow()
    result = workflow.invoke(initial_state)
    return result
