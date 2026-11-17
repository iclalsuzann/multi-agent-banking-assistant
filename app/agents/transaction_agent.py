"""Transaction Agent: Specializes in analyzing account ledger, spending trends, and category spikes."""
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.agents.base import get_llm
from app.tools.transaction_tools import get_customer_transactions, analyze_spending_trends

TRANSACTION_AGENT_PROMPT = """Sen Multi-Agent Banking Assistant sisteminde görevli kıdemli bir **Harcama ve Hesap Analiz Ajanısın (Transaction Agent)**.

GÖREVLERİN:
1. Müşterinin hesap hareketlerini, ekstrelerini ve harcama kategorilerini incelemek.
2. Harcama artışlarının (spikes) ve trend değişimlerinin nedenlerini net verilerle tespit etmek.
3. Hangi kategorilerde (Örn: Restoran, Faturalar, Market) ve hangi işyerlerinde ne kadar artış olduğunu TL ve yüzde (%) olarak sunmak.

İletişim Tarzı:
- Profesyonel, net, analitik ve veriye dayalı.
- Müşteriyi rakam karmaşasında boğmadan en önemli artış etkenlerini (primary drivers) vurgula.
"""

TRANSACTION_TOOLS = [get_customer_transactions, analyze_spending_trends]


class TransactionAgent:
    """Specialized agent for transaction ledger and spending trend analysis."""

    def __init__(self):
        self.name = "Transaction Agent"
        self.llm = get_llm()
        self.tools = TRANSACTION_TOOLS

    def run(self, query: str, customer_number: str = "CUST-1001") -> Dict[str, Any]:
        """
        Executes analysis on transaction records based on the user's inquiry.
        """
        lower_q = query.lower()

        # Trend / artış / neden arttı sorguları
        if any(w in lower_q for w in ["arttı", "artış", "neden", "trend", "fark", "kıyas", "geçen ay"]):
            trend_data = analyze_spending_trends.invoke({"customer_number": customer_number})

            # Format human-readable summary
            spikes = trend_data.get("significant_spikes", [])
            spike_summary = []
            for s in spikes:
                top_m = ", ".join([f"{m['merchant']} ({m['amount']} TL)" for m in s.get("top_merchants", [])])
                spike_summary.append(
                    f"- **{s['category']}**: Geçen ay {s['last_month_spending']} TL harcandı "
                    f"(Önceki aya göre +{s['difference']} TL, %{s['percentage_change']} artış). "
                    f"Öne çıkan harcamalar: {top_m}"
                )

            summary_text = (
                f"📊 **Harcama Analiz Raporu ({trend_data.get('customer_name', customer_number)}):**\n"
                f"- **Son 30 Gün Toplam Harcama:** {trend_data.get('last_month_total_spending')} TL\n"
                f"- **Önceki Dönem Toplam Harcama:** {trend_data.get('previous_month_total_spending')} TL\n"
                f"- **Net Harcama Artışı:** +{trend_data.get('net_spending_increase')} TL "
                f"(%{trend_data.get('percentage_increase')})\n\n"
                f"🔍 **Harcama Artışının Başlıca Nedenleri:**\n" + "\n".join(spike_summary)
            )

            return {
                "agent": self.name,
                "status": "SUCCESS",
                "raw_data": trend_data,
                "summary": summary_text,
            }

        # Standart hareket listesi sorgusu
        tx_data = get_customer_transactions.invoke({"customer_number": customer_number, "days": 30})
        return {
            "agent": self.name,
            "status": "SUCCESS",
            "raw_data": tx_data,
            "summary": (
                f"Son 30 günde toplam {tx_data.get('transaction_count')} adet işlemde "
                f"{tx_data.get('total_expense')} TL harcama tespit edildi."
            ),
        }


# Singleton instance for workflow integration
transaction_agent = TransactionAgent()
