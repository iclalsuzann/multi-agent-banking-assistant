"""Integration tests for FastAPI REST API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.seed import seed_database


@pytest.fixture(scope="module", autouse=True)
def init_data():
    """Ensure seed data is ready before API tests."""
    seed_database()


client = TestClient(app)


def test_root_dashboard_and_metadata_endpoints():
    """Verify root endpoint serves the HTML dashboard and /api serves metadata."""
    # Test HTML dashboard
    res_ui = client.get("/")
    assert res_ui.status_code == 200
    assert "text/html" in res_ui.headers.get("content-type", "")
    assert "Multi-Agent Banking Assistant" in res_ui.text

    # Test JSON metadata
    res_api = client.get("/api")
    assert res_api.status_code == 200
    data = res_api.json()
    assert "docs_url" in data
    assert data["docs_url"] == "/docs"


def test_health_check_endpoint():
    """Verify health check endpoint returns OK status and database connection."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OK"
    assert data["database"] == "UP"
    assert data["agents_ready"] is True


def test_list_agents_endpoint():
    """Verify agents endpoint lists all 5 specialized agents."""
    res = client.get("/api/v1/agents")
    assert res.status_code == 200
    data = res.json()
    assert data["total_agents"] == 5
    agent_names = [a["name"] for a in data["agents"]]
    assert "Orchestrator Agent" in agent_names
    assert "Transaction Agent" in agent_names
    assert "Finance Agent" in agent_names
    assert "Document Agent" in agent_names
    assert "Support Agent" in agent_names


def test_transactions_endpoint():
    """Verify transactions endpoint returns customer ledger records."""
    res = client.get("/api/v1/transactions?customer_number=CUST-1001&days=30")
    assert res.status_code == 200
    data = res.json()
    assert data["customer_number"] == "CUST-1001"
    assert data["transaction_count"] > 0
    assert data["total_expense"] > 0


def test_spending_trends_endpoint():
    """Verify spending trends analytics endpoint calculates comparisons and spikes."""
    res = client.get("/api/v1/analytics/spending-trends?customer_number=CUST-1001")
    assert res.status_code == 200
    data = res.json()
    assert "net_spending_increase" in data
    assert len(data["significant_spikes"]) >= 1


def test_chat_composite_query_endpoint():
    """Verify chat endpoint with composite scenario (spending analysis + savings)."""
    payload = {
        "query": "Geçen ay harcamalarım neden arttı ve nasıl tasarruf edebilirim?",
        "customer_number": "CUST-1001",
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["customer_number"] == "CUST-1001"
    assert "Transaction Agent" in data["active_agents"]
    assert "Finance Agent" in data["active_agents"]
    assert "Harcama Analiz Raporu" in data["response"]
    assert "Tasarruf Potansiyeli Özeti" in data["response"]


def test_chat_support_query_endpoint():
    """Verify chat endpoint with support card blocking query."""
    payload = {
        "query": "Kartımı kaybettim, lütfen kartımı bloke edin",
        "customer_number": "CUST-1001",
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "Support Agent" in data["active_agents"]
    assert "TCK-BLK-" in data["response"]
