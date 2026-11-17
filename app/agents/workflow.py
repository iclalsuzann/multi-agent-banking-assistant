"""LangGraph Multi-Agent Workflow and Supervisor Graph Definition."""
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from app.agents.orchestrator import orchestrator_agent
from app.agents.transaction_agent import transaction_agent
from app.agents.finance_agent import finance_agent
from app.agents.document_agent import document_agent
from app.agents.support_agent import support_agent


class BankingState(TypedDict):
    """Shared state for the LangGraph multi-agent banking assistant."""
    query: str
    customer_number: str
    plan: List[str]
    current_step: int
    agent_outputs: Dict[str, Any]
    active_agents: List[str]
    final_response: Optional[str]


# ---------------------------------------------------------
# Node Functions
# ---------------------------------------------------------

def orchestrator_node(state: BankingState) -> Dict[str, Any]:
    """
    Supervisor node that plans the execution order and synthesizes the final response.
    """
    plan = state.get("plan", [])
    agent_outputs = state.get("agent_outputs", {})
    current_step = state.get("current_step", 0)
    query = state.get("query", "")

    # Planlama henüz yapılmadıysa planı oluştur
    if not plan:
        plan = orchestrator_agent.route_query(query)
        current_step = 0

    # Tüm planlanan ajanlar çalıştırıldıysa nihai sentezi yap
    if current_step >= len(plan):
        final_text = orchestrator_agent.synthesize_response(
            query=query,
            agent_outputs=agent_outputs,
        )
        return {
            "plan": plan,
            "current_step": current_step,
            "final_response": final_text,
        }

    return {
        "plan": plan,
        "current_step": current_step,
    }


def transaction_node(state: BankingState) -> Dict[str, Any]:
    """Runs the Transaction Agent."""
    query = state.get("query", "")
    cust_num = state.get("customer_number", "CUST-1001")
    outputs = dict(state.get("agent_outputs", {}))
    active = list(state.get("active_agents", []))

    res = transaction_agent.run(query=query, customer_number=cust_num)
    outputs["transaction_agent"] = res
    if "Transaction Agent" not in active:
        active.append("Transaction Agent")

    return {
        "agent_outputs": outputs,
        "active_agents": active,
        "current_step": state.get("current_step", 0) + 1,
    }


def finance_node(state: BankingState) -> Dict[str, Any]:
    """Runs the Finance Agent, utilizing transaction outputs if available."""
    query = state.get("query", "")
    outputs = dict(state.get("agent_outputs", {}))
    active = list(state.get("active_agents", []))
    tx_context = outputs.get("transaction_agent")

    res = finance_agent.run(query=query, transaction_context=tx_context)
    outputs["finance_agent"] = res
    if "Finance Agent" not in active:
        active.append("Finance Agent")

    return {
        "agent_outputs": outputs,
        "active_agents": active,
        "current_step": state.get("current_step", 0) + 1,
    }


def document_node(state: BankingState) -> Dict[str, Any]:
    """Runs the Document Agent."""
    query = state.get("query", "")
    outputs = dict(state.get("agent_outputs", {}))
    active = list(state.get("active_agents", []))

    res = document_agent.run(query=query)
    outputs["document_agent"] = res
    if "Document Agent" not in active:
        active.append("Document Agent")

    return {
        "agent_outputs": outputs,
        "active_agents": active,
        "current_step": state.get("current_step", 0) + 1,
    }


def support_node(state: BankingState) -> Dict[str, Any]:
    """Runs the Support Agent."""
    query = state.get("query", "")
    cust_num = state.get("customer_number", "CUST-1001")
    outputs = dict(state.get("agent_outputs", {}))
    active = list(state.get("active_agents", []))

    res = support_agent.run(query=query, customer_number=cust_num)
    outputs["support_agent"] = res
    if "Support Agent" not in active:
        active.append("Support Agent")

    return {
        "agent_outputs": outputs,
        "active_agents": active,
        "current_step": state.get("current_step", 0) + 1,
    }


# ---------------------------------------------------------
# Router / Conditional Edge
# ---------------------------------------------------------

def supervisor_router(state: BankingState) -> str:
    """Decides whether to route to the next agent or finish the execution."""
    if state.get("final_response"):
        return END

    plan = state.get("plan", [])
    step = state.get("current_step", 0)

    if step < len(plan):
        return plan[step]

    return END


# ---------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------

def create_banking_graph():
    """Builds and compiles the multi-agent StateGraph with checkpointing."""
    graph = StateGraph(BankingState)

    # Add Nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("transaction_agent", transaction_node)
    graph.add_node("finance_agent", finance_node)
    graph.add_node("document_agent", document_node)
    graph.add_node("support_agent", support_node)

    # Add Edges
    graph.add_edge(START, "orchestrator")

    # Conditional routing from supervisor orchestrator
    graph.add_conditional_edges(
        "orchestrator",
        supervisor_router,
        {
            "transaction_agent": "transaction_agent",
            "finance_agent": "finance_agent",
            "document_agent": "document_agent",
            "support_agent": "support_agent",
            END: END,
        },
    )

    # Agents report back to orchestrator
    graph.add_edge("transaction_agent", "orchestrator")
    graph.add_edge("finance_agent", "orchestrator")
    graph.add_edge("document_agent", "orchestrator")
    graph.add_edge("support_agent", "orchestrator")

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Global compiled app
banking_agent_system = create_banking_graph()


def run_banking_assistant(
    query: str,
    customer_number: str = "CUST-1001",
    thread_id: str = "default_session",
) -> Dict[str, Any]:
    """
    Convenience runner for the multi-agent banking assistant graph.
    """
    initial_state: BankingState = {
        "query": query,
        "customer_number": customer_number,
        "plan": [],
        "current_step": 0,
        "agent_outputs": {},
        "active_agents": [],
        "final_response": None,
    }

    config = {"configurable": {"thread_id": thread_id}}
    result = banking_agent_system.invoke(initial_state, config=config)

    return {
        "query": query,
        "customer_number": customer_number,
        "thread_id": thread_id,
        "active_agents": result.get("active_agents", []),
        "final_response": result.get("final_response", ""),
        "agent_outputs": result.get("agent_outputs", {}),
    }
