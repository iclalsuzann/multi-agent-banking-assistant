"""FastAPI route definitions for the banking assistant."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.agents.workflow import run_banking_assistant
from app.tools.transaction_tools import get_customer_transactions, analyze_spending_trends
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    AgentListResponse,
    AgentInfo,
    HealthResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying application and database connectivity."""
    db_status = "UP"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"DOWN: {str(e)}"

    return HealthResponse(
        status="OK" if db_status == "UP" else "DEGRADED",
        app_name="Multi-Agent Banking Assistant",
        version="0.1.0",
        database=db_status,
        agents_ready=True,
    )


@router.post("/chat", response_model=ChatResponse, tags=["AI Agents"])
def chat_with_multi_agent_system(req: ChatRequest):
    """
    Main chat endpoint coordinating the multi-agent workflow.
    Routes queries to Orchestrator, Transaction, Finance, Document, and Support agents.
    """
    thread_id = req.thread_id or f"session_{uuid.uuid4().hex[:8]}"

    try:
        result = run_banking_assistant(
            query=req.query,
            customer_number=req.customer_number,
            thread_id=thread_id,
        )
        return ChatResponse(
            query=result["query"],
            customer_number=result["customer_number"],
            thread_id=result["thread_id"],
            response=result["final_response"],
            active_agents=result["active_agents"],
            agent_outputs=result["agent_outputs"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ajan çalıştırma hatası: {str(e)}")


@router.get("/agents", response_model=AgentListResponse, tags=["AI Agents"])
def list_system_agents():
    """Returns the list of all registered specialized agents and their active tools."""
    agents = [
        AgentInfo(
            name="Orchestrator Agent",
            role="Supervisor & Coordinator",
            description="Kullanıcı niyetini analiz eder, talebi alt görevlere böler ve uzman ajanları koordine eder.",
            tools=["route_query", "synthesize_response"],
        ),
        AgentInfo(
            name="Transaction Agent",
            role="Ledger & Spending Specialist",
            description="Hesap hareketlerini inceler, harcama artışlarını ve kategorik sapmaları tespit eder.",
            tools=["get_customer_transactions", "analyze_spending_trends"],
        ),
        AgentInfo(
            name="Finance Agent",
            role="Advisory & Budget Specialist",
            description="Tasarruf simülasyonları, 50/30/20 bütçe optimizasyonu ve vadeli mevduat faiz getirisi hesaplar.",
            tools=["calculate_savings_potential", "get_budget_recommendations"],
        ),
        AgentInfo(
            name="Document Agent",
            role="Policy & Knowledge Specialist",
            description="Banka mevzuatları, kredi ve kart sözleşmeleri, aidat iade kurallarından bilgi bulur.",
            tools=["search_banking_documents", "get_banking_document_details"],
        ),
        AgentInfo(
            name="Support Agent",
            role="Security & Support Specialist",
            description="Kart bloke etme/dondurma, harcama itirazı (Chargeback) ve destek bileti işlemlerini yönetir.",
            tools=["block_card", "create_dispute_ticket", "check_support_ticket_status"],
        ),
    ]
    return AgentListResponse(total_agents=len(agents), agents=agents)


@router.get("/transactions", tags=["Banking Data"])
def get_transactions_endpoint(
    customer_number: str = Query(default="CUST-1001", description="Müşteri numarası"),
    days: int = Query(default=30, ge=1, le=365, description="Gün aralığı"),
    category: Optional[str] = Query(default=None, description="Kategori filtresi"),
):
    """Retrieve customer transactions with optional filtering."""
    return get_customer_transactions.invoke({
        "customer_number": customer_number,
        "days": days,
        "category": category,
    })


@router.get("/analytics/spending-trends", tags=["Banking Data"])
def get_spending_trends_endpoint(
    customer_number: str = Query(default="CUST-1001", description="Müşteri numarası"),
):
    """Retrieve comparative monthly spending trends and identify high-cost spikes."""
    return analyze_spending_trends.invoke({
        "customer_number": customer_number,
    })
