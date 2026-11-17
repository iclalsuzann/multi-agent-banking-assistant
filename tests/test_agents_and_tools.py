"""Unit tests for specialized banking agents and their respective tool suites."""
import pytest
from app.db.seed import seed_database
from app.agents import (
    transaction_agent,
    finance_agent,
    document_agent,
    support_agent,
)
from app.tools import (
    get_customer_transactions,
    analyze_spending_trends,
    calculate_savings_potential,
    get_budget_recommendations,
    search_banking_documents,
    block_card,
    create_dispute_ticket,
)


@pytest.fixture(autouse=True)
def setup_seed_db():
    """Ensure database has seed data prior to testing agents."""
    seed_database()


def test_transaction_tools_and_agent():
    """Verify transaction tools and TransactionAgent spending spike analysis."""
    # Test tool directly
    tx_res = get_customer_transactions.invoke({"customer_number": "CUST-1001", "days": 30})
    assert "transactions" in tx_res
    assert tx_res["transaction_count"] > 0
    assert tx_res["total_expense"] > 0

    # Test trend analysis tool
    trend_res = analyze_spending_trends.invoke({"customer_number": "CUST-1001"})
    assert trend_res["net_spending_increase"] > 0
    assert len(trend_res["significant_spikes"]) >= 1

    # Check that restaurant spending was identified as the main spike
    spikes = trend_res["significant_spikes"]
    categories = [s["category"] for s in spikes]
    assert any("Restoran" in c for c in categories)

    # Test agent run
    agent_res = transaction_agent.run("Geçen ay harcamalarım neden arttı?", customer_number="CUST-1001")
    assert agent_res["status"] == "SUCCESS"
    assert "Harcama Analiz Raporu" in agent_res["summary"]
    assert "Restoran & Yeme İçme" in agent_res["summary"]


def test_finance_tools_and_agent():
    """Verify savings calculation tools and FinanceAgent recommendations."""
    # Test savings calculation tool
    calc_res = calculate_savings_potential.invoke({
        "dining_spending": 16850.0,
        "subscriptions_spending": 6900.0,
        "savings_account_rate": 45.0,
    })
    assert calc_res["monthly_savings_potential"] > 0
    assert calc_res["annual_savings_potential"] > calc_res["monthly_savings_potential"]
    assert calc_res["projected_total_wealth_in_1_year"] > calc_res["annual_savings_potential"]

    # Test budget recommendations tool
    budget_res = get_budget_recommendations.invoke({
        "monthly_income": 65000.0,
        "current_total_expenses": 48000.0,
    })
    assert budget_res["monthly_income"] == 65000.0
    assert "ideal_50_30_20_targets" in budget_res

    # Test agent run with transaction context
    agent_res = finance_agent.run("Nasıl tasarruf edebilirim?")
    assert agent_res["status"] == "SUCCESS"
    assert "Tasarruf Potansiyeli Özeti" in agent_res["summary"]
    assert "Vadeli Mevduat Faizi Getirisi" in agent_res["summary"]


def test_document_tools_and_agent():
    """Verify document search tool and DocumentAgent knowledge extraction."""
    # Test search tool for card fee refund
    search_res = search_banking_documents.invoke({"query": "kart aidatı iade"})
    assert search_res["match_count"] >= 1
    doc = search_res["documents"][0]
    assert "aidat" in doc["content"].lower() or "ücret" in doc["title"].lower()

    # Test search for deposit interest
    interest_res = search_banking_documents.invoke({"query": "vadeli mevduat faiz oranları"})
    assert interest_res["match_count"] >= 1
    assert "faiz" in interest_res["documents"][0]["content"].lower()

    # Test agent run
    agent_res = document_agent.run("Kredi kartı aidatımı nasıl geri alabilirim?")
    assert agent_res["status"] == "SUCCESS"
    assert "Mevzuat" in agent_res["summary"]


def test_support_tools_and_agent():
    """Verify card blocking, dispute creation, and SupportAgent actions."""
    # Test block card tool
    block_res = block_card.invoke({
        "customer_number": "CUST-1001",
        "card_last_four": "4589",
        "reason": "Kayıp kart bildirimi",
    })
    assert block_res["status"] == "SUCCESS"
    assert block_res["is_blocked"] is True
    assert block_res["ticket_number"].startswith("TCK-BLK-")

    # Test dispute tool
    dispute_res = create_dispute_ticket.invoke({
        "transaction_id": 1,
        "reason": "Harcama tutarı hatalı",
        "customer_number": "CUST-1001",
    })
    assert dispute_res["status"] == "DISPUTE_SUBMITTED"
    assert dispute_res["ticket_number"].startswith("TCK-DSP-")

    # Test support agent run
    agent_res = support_agent.run("Kartımı kaybettim lütfen acil bloke edin", customer_number="CUST-1001")
    assert agent_res["status"] == "SUCCESS"
    assert "Kart Güvenlik İşlemi" in agent_res["summary"]
