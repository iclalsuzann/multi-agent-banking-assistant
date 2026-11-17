"""Customer support, card management, and dispute tools for Support Agent."""
import random
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.models import User, Account, Transaction, SupportTicket, utcnow


@tool
def block_card(
    customer_number: str = "CUST-1001",
    card_last_four: Optional[str] = "4589",
    reason: str = "Kullanıcı talebiyle şüpheli işlem / kayıp bildirimi",
) -> Dict[str, Any]:
    """
    Müşterinin banka veya kredi kartını güvenlik sebebiyle derhal kullanıma kapatır (bloke eder) ve destek bileti oluşturur.
    
    Args:
        customer_number: Müşteri numarası (Örn: 'CUST-1001').
        card_last_four: Bloke edilecek kartın son 4 hanesi.
        reason: Kartın bloke edilme gerekçesi (Örn: 'Kayıp/çalıntı', 'Şüpheli işlem').
    """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.customer_number == customer_number).first()
        if not user:
            return {"error": f"Müşteri bulunamadı: {customer_number}"}

        # Find matching account
        target_account = None
        for acc in user.accounts:
            if card_last_four and acc.card_last_four == card_last_four:
                target_account = acc
                break
            elif not card_last_four and acc.card_last_four:
                target_account = acc
                break

        if not target_account:
            return {"error": f"Son 4 hanesi {card_last_four} olan aktif bir kart bulunamadı."}

        target_account.is_blocked = True

        # Generate ticket
        ticket_number = f"TCK-BLK-{random.randint(10000, 99999)}"
        ticket = SupportTicket(
            user_id=user.id,
            ticket_number=ticket_number,
            ticket_type="CARD_BLOCK",
            status="RESOLVED",
            subject=f"Kart Bloke Bildirimi (Son 4 hane: {target_account.card_last_four})",
            description=f"Kart başarıyla donduruldu. Gerekçe: {reason}",
            created_at=utcnow(),
        )
        db.add(ticket)
        db.commit()

        return {
            "status": "SUCCESS",
            "message": f"Son 4 hanesi {target_account.card_last_four} olan kartınız anında bloke edilmiş ve tüm işlemlere kapatılmıştır.",
            "card_last_four": target_account.card_last_four,
            "account_number": target_account.account_number,
            "is_blocked": target_account.is_blocked,
            "ticket_number": ticket_number,
            "security_advice": "Yeni kartınız en geç 3 iş günü içerisinde kayıtlı adresinize kurye ile teslim edilecektir.",
        }
    finally:
        db.close()


@tool
def create_dispute_ticket(
    transaction_id: int,
    reason: str,
    customer_number: str = "CUST-1001",
) -> Dict[str, Any]:
    """
    Müşterinin tanımadığı veya itiraz etmek istediği bir harcama için resmi harcama itirazı (Chargeback) bileti açar.
    
    Args:
        transaction_id: İtiraz edilen işlemin ID numarası.
        reason: İtiraz gerekçesi (Örn: 'Bu harcamayı ben yapmadım', 'Mükerrer çekim yapıldı').
        customer_number: Müşteri numarası.
    """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.customer_number == customer_number).first()
        if not user:
            return {"error": f"Müşteri bulunamadı: {customer_number}"}

        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return {"error": f"İşlem bulunamadı: ID {transaction_id}"}

        tx.is_disputed = True

        ticket_number = f"TCK-DSP-{random.randint(10000, 99999)}"
        ticket = SupportTicket(
            user_id=user.id,
            ticket_number=ticket_number,
            ticket_type="DISPUTE",
            status="PENDING_REVIEW",
            subject=f"Harcama İtirazı: {tx.merchant} ({tx.amount} {tx.currency})",
            description=f"İşlem ID: {tx.id}, İşyeri: {tx.merchant}, Tutar: {tx.amount} {tx.currency}. İtiraz nedeni: {reason}",
            created_at=utcnow(),
        )
        db.add(ticket)
        db.commit()

        return {
            "status": "DISPUTE_SUBMITTED",
            "ticket_number": ticket_number,
            "transaction_id": tx.id,
            "merchant": tx.merchant,
            "disputed_amount": abs(tx.amount),
            "currency": tx.currency,
            "ticket_status": "PENDING_REVIEW",
            "message": f"{tx.merchant} işyerine ait {abs(tx.amount)} {tx.currency} tutarındaki harcama için itiraz talebiniz alındı. Güvenlik birimimiz işlemi incelemektedir.",
        }
    finally:
        db.close()


@tool
def check_support_ticket_status(
    ticket_number: str,
) -> Dict[str, Any]:
    """
    Daha önce oluşturulmuş bir destek veya itiraz biletinin güncel durumunu sorgular.
    
    Args:
        ticket_number: Bilet takip numarası (Örn: 'TCK-2026-1082', 'TCK-DSP-48192').
    """
    db: Session = SessionLocal()
    try:
        ticket = db.query(SupportTicket).filter(SupportTicket.ticket_number == ticket_number).first()
        if not ticket:
            return {"error": f"Bilet bulunamadı: {ticket_number}"}

        return {
            "ticket_number": ticket.ticket_number,
            "ticket_type": ticket.ticket_type,
            "status": ticket.status,
            "subject": ticket.subject,
            "description": ticket.description,
            "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
        }
    finally:
        db.close()
