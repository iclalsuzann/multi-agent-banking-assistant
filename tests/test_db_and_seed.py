"""Unit tests for database initialization, models, and seed data."""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.models import User, Account, Transaction, DocumentChunk, SupportTicket, utcnow
from app.db.seed import seed_database


def test_models_and_relationships():
    """Verify that models and relationships function as expected in an isolated in-memory DB."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(bind=test_engine)
    db = TestingSessionLocal()

    # Create user
    user = User(
        customer_number="CUST-TEST",
        full_name="Test Customer",
        email="test@example.com",
        monthly_income=50000.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.customer_number == "CUST-TEST"

    # Create account
    account = Account(
        user_id=user.id,
        account_number="TR0000TEST12345",
        account_type="CHECKING",
        balance=10000.0,
        currency="TRY",
        card_last_four="9999",
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    assert len(user.accounts) == 1
    assert user.accounts[0].card_last_four == "9999"

    # Create transaction
    tx = Transaction(
        account_id=account.id,
        amount=-250.0,
        category="Restoran & Yeme İçme",
        merchant="Test Cafe",
        description="Coffee and snacks",
        transaction_date=utcnow(),
    )
    db.add(tx)
    db.commit()

    assert len(account.transactions) == 1
    assert account.transactions[0].amount == -250.0

    # Create DocumentChunk
    doc = DocumentChunk(
        title="Test Policy",
        category="Kredi Kartı",
        content="Test policy content for verification.",
    )
    db.add(doc)
    db.commit()
    assert doc.id is not None

    # Create SupportTicket
    ticket = SupportTicket(
        user_id=user.id,
        ticket_number="TCK-TEST-01",
        ticket_type="CARD_BLOCK",
        subject="Lost Card",
        description="Card was misplaced.",
    )
    db.add(ticket)
    db.commit()
    assert len(user.tickets) == 1

    db.close()


def test_seed_database_execution():
    """Verify that the seed_database function populates all required entities for the scenario."""
    from app.db.session import SessionLocal, engine

    # Run seed
    seed_database()

    db = SessionLocal()
    try:
        # Check customer Ali Yılmaz
        customer = db.query(User).filter(User.customer_number == "CUST-1001").first()
        assert customer is not None
        assert customer.full_name == "Ali Yılmaz"
        assert len(customer.accounts) >= 2

        # Check transactions exist
        checking_acc = next(a for a in customer.accounts if a.account_type == "CHECKING")
        tx_count = db.query(Transaction).filter(Transaction.account_id == checking_acc.id).count()
        assert tx_count > 10, f"Expected > 10 transactions, got {tx_count}"

        # Verify spending spike in Restoran category
        now = utcnow()
        last_month_start = now - timedelta(days=30)
        baseline_start = now - timedelta(days=60)

        last_month_restaurant_sum = sum(
            abs(t.amount)
            for t in db.query(Transaction)
            .filter(
                Transaction.account_id == checking_acc.id,
                Transaction.category == "Restoran & Yeme İçme",
                Transaction.transaction_date >= last_month_start,
                Transaction.amount < 0,
            )
            .all()
        )

        baseline_restaurant_sum = sum(
            abs(t.amount)
            for t in db.query(Transaction)
            .filter(
                Transaction.account_id == checking_acc.id,
                Transaction.category == "Restoran & Yeme İçme",
                Transaction.transaction_date < last_month_start,
                Transaction.transaction_date >= baseline_start,
                Transaction.amount < 0,
            )
            .all()
        )

        # Confirm there is an evident spike for the agent scenario
        assert last_month_restaurant_sum > baseline_restaurant_sum, (
            f"Expected last month restaurant spending ({last_month_restaurant_sum}) "
            f"to exceed baseline ({baseline_restaurant_sum})"
        )

        # Check documents exist
        docs = db.query(DocumentChunk).all()
        assert len(docs) >= 4

    finally:
        db.close()
