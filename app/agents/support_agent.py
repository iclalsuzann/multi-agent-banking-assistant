"""Support Agent: Specializes in security operations, card blocking, disputes, and ticket management."""
from typing import Dict, Any, Optional
from app.agents.base import get_llm
from app.tools.support_tools import (
    block_card,
    create_dispute_ticket,
    check_support_ticket_status,
)

SUPPORT_AGENT_PROMPT = """Sen Multi-Agent Banking Assistant sisteminde görevli kıdemli bir **Müşteri Destek ve Güvenlik Ajanısın (Support Agent)**.

GÖREVLERİN:
1. Kart dondurma, kayıp/çalıntı bildirimlerini ve acil güvenlik taleplerini anında yerine getirmek.
2. Tanınmayan veya mükerrer harcamalar için resmi itiraz (Chargeback) bileti açmak.
3. Açılmış destek biletlerinin durumunu sorgulamak ve müşteriyi bilgilendirmek.

İletişim Tarzı:
- Hızlı, çözüm odaklı, güven verici ve sakinleştirici.
"""

SUPPORT_TOOLS = [block_card, create_dispute_ticket, check_support_ticket_status]


class SupportAgent:
    """Specialized agent for support actions and banking security operations."""

    def __init__(self):
        self.name = "Support Agent"
        self.llm = get_llm()
        self.tools = SUPPORT_TOOLS

    def run(
        self,
        query: str,
        customer_number: str = "CUST-1001",
        card_last_four: Optional[str] = "4589",
        transaction_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes support actions such as card blocking, disputing a transaction, or checking ticket status.
        """
        lower_q = query.lower()

        # Kart bloke / kayıp / çalıntı
        if any(w in lower_q for w in ["bloke", "kartımı dondur", "kayıp", "çalıntı", "kartı kapat", "kartımı kaybettim"]):
            res = block_card.invoke({
                "customer_number": customer_number,
                "card_last_four": card_last_four,
                "reason": query,
            })

            summary = (
                f"🛡️ **Kart Güvenlik İşlemi Gerçekleştirildi:**\n"
                f"- **Durum:** {res.get('message')}\n"
                f"- **Takip Numarası:** `{res.get('ticket_number')}`\n"
                f"- **Bilgilendirme:** {res.get('security_advice')}"
            )
            return {
                "agent": self.name,
                "status": "SUCCESS",
                "summary": summary,
                "raw_data": res,
            }

        # Harcama itirazı / chargeback
        if any(w in lower_q for w in ["itiraz", "ben yapmadım", "şüpheli harcama", "mükerrer", "tanımıyorum"]):
            target_tx_id = transaction_id or 1  # Varsayılan son işlem veya verilen ID
            res = create_dispute_ticket.invoke({
                "transaction_id": target_tx_id,
                "reason": query,
                "customer_number": customer_number,
            })

            summary = (
                f"📋 **Harcama İtiraz Talebi Oluşturuldu:**\n"
                f"- **Mesaj:** {res.get('message')}\n"
                f"- **Takip Bilet No:** `{res.get('ticket_number')}`\n"
                f"- **İnceleme Durumu:** {res.get('ticket_status')}"
            )
            return {
                "agent": self.name,
                "status": "SUCCESS",
                "summary": summary,
                "raw_data": res,
            }

        # Bilet sorgulama
        if "bilet" in lower_q or "durum" in lower_q:
            res = check_support_ticket_status.invoke({"ticket_number": "TCK-2026-1082"})
            summary = (
                f"🎫 **Destek Bileti Durumu ({res.get('ticket_number')}):**\n"
                f"- **Konu:** {res.get('subject')}\n"
                f"- **Durum:** {res.get('status')}\n"
                f"- **Açıklama:** {res.get('description')}"
            )
            return {
                "agent": self.name,
                "status": "SUCCESS",
                "summary": summary,
                "raw_data": res,
            }

        # Genel destek yönlendirmesi
        return {
            "agent": self.name,
            "status": "INFO",
            "summary": "Müşteri Destek ekibimiz 7/24 hizmetinizdedir. Kart bloke, itiraz veya bilet takibi talebinizi belirtebilirsiniz.",
            "raw_data": {},
        }


# Singleton instance
support_agent = SupportAgent()
