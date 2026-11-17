"""SQLAlchemy Database Models for Multi-Agent Banking Assistant."""
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


def utcnow():
    """Return timezone-naive UTC timestamp for standard DB compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """Bank customer model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    customer_number = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    monthly_income = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.customer_number} - {self.full_name}>"


class Account(Base):
    """Customer bank or credit card account."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_number = Column(String(50), unique=True, index=True, nullable=False)
    account_type = Column(String(30), default="CHECKING")  # CHECKING, SAVINGS, CREDIT_CARD
    balance = Column(Float, default=0.0)
    currency = Column(String(10), default="TRY")
    card_last_four = Column(String(4), nullable=True)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Account {self.account_number} ({self.account_type}) - Balance: {self.balance} {self.currency}>"


class Transaction(Base):
    """Ledger transaction / spending record."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Negative for expenses, positive for credits
    currency = Column(String(10), default="TRY")
    category = Column(String(50), nullable=False, index=True)  # Market & Gıda, Restoran, Faturalar, etc.
    merchant = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    is_disputed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    account = relationship("Account", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.id}: {self.amount} {self.currency} - {self.category} ({self.merchant})>"


class DocumentChunk(Base):
    """Knowledge base chunk for Document Agent RAG and policy lookups."""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # Kredi, Kredi Kartı, Mevduat, Güvenlik
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    def __repr__(self) -> str:
        return f"<DocumentChunk {self.title} ({self.category})>"


class SupportTicket(Base):
    """Customer support tickets created by Support Agent."""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticket_number = Column(String(50), unique=True, index=True, nullable=False)
    ticket_type = Column(String(50), nullable=False)  # CARD_BLOCK, DISPUTE, GENERAL_INQUIRY
    status = Column(String(30), default="OPEN")  # OPEN, RESOLVED, PENDING_REVIEW
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    user = relationship("User", back_populates="tickets")

    def __repr__(self) -> str:
        return f"<SupportTicket {self.ticket_number} - {self.ticket_type} ({self.status})>"
