"""Integration tests for LangGraph Multi-Agent Workflow and Supervisor Orchestrator."""
import pytest
from app.db.seed import seed_database
from app.agents.workflow import run_banking_assistant, create_banking_graph


@pytest.fixture(autouse=True)
def setup_seed_db():
    """Ensure database has seed data prior to testing workflow."""
    seed_database()


def test_composite_scenario_spending_and_savings():
    """
    Test user request: 'Geçen ay harcamalarım neden arttı ve nasıl tasarruf edebilirim?'
    Must invoke both Transaction Agent and Finance Agent, coordinated by Orchestrator.
    """
    query = "Geçen ay harcamalarım neden arttı ve nasıl tasarruf edebilirim?"
    result = run_banking_assistant(
        query=query,
        customer_number="CUST-1001",
        thread_id="test_thread_composite",
    )

    assert result["customer_number"] == "CUST-1001"
    active_agents = result["active_agents"]

    # 1. Her iki ajanın da aktifleştiği doğrulanmalı
    assert "Transaction Agent" in active_agents, "Transaction Agent should be active"
    assert "Finance Agent" in active_agents, "Finance Agent should be active"

    # 2. Ara çıktılar mevcut olmalı
    outputs = result["agent_outputs"]
    assert "transaction_agent" in outputs
    assert "finance_agent" in outputs

    # 3. Nihai yanıt her iki ajanın sentezini içermeli
    final_resp = result["final_response"]
    assert "Harcama Analiz Raporu" in final_resp
    assert "Restoran & Yeme İçme" in final_resp
    assert "Tasarruf Potansiyeli Özeti" in final_resp
    assert "Aylık Tasarruf Hedefi" in final_resp


def test_document_routing_workflow():
    """Verify queries regarding banking terms and interest rates route to Document Agent."""
    query = "Kredi kartı aidatımı geri alabilir miyim ve şartları nelerdir?"
    result = run_banking_assistant(
        query=query,
        customer_number="CUST-1001",
        thread_id="test_thread_doc",
    )

    assert "Document Agent" in result["active_agents"]
    assert "Mevzuat ve Politika" in result["final_response"]
    assert "Kredi Kartı Yıllık Üyelik Ücreti" in result["final_response"]


def test_support_routing_workflow():
    """Verify security and card management queries route to Support Agent."""
    query = "Kartımı kaybettim, lütfen kartımı bloke edin"
    result = run_banking_assistant(
        query=query,
        customer_number="CUST-1001",
        thread_id="test_thread_support",
    )

    assert "Support Agent" in result["active_agents"]
    assert "Kart Güvenlik İşlemi" in result["final_response"]
    assert "TCK-BLK-" in result["final_response"]


def test_graph_state_isolation_across_threads():
    """Verify that multiple sessions maintain isolated states via thread_id."""
    graph = create_banking_graph()

    state1 = {
        "query": "Kartımı bloke et",
        "customer_number": "CUST-1001",
        "plan": [],
        "current_step": 0,
        "agent_outputs": {},
        "active_agents": [],
        "final_response": None,
    }
    config1 = {"configurable": {"thread_id": "session_alpha"}}
    res1 = graph.invoke(state1, config=config1)
    assert "Support Agent" in res1["active_agents"]

    state2 = {
        "query": "Vadeli mevduat faiz oranları nedir?",
        "customer_number": "CUST-1001",
        "plan": [],
        "current_step": 0,
        "agent_outputs": {},
        "active_agents": [],
        "final_response": None,
    }
    config2 = {"configurable": {"thread_id": "session_beta"}}
    res2 = graph.invoke(state2, config=config2)
    assert "Document Agent" in res2["active_agents"]
    assert "Support Agent" not in res2["active_agents"]
