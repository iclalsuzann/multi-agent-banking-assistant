"""Finance Agent: Specializes in budget optimization, savings strategies, and interest yield modeling."""
from typing import Dict, Any, Optional
from app.agents.base import get_llm
from app.tools.finance_tools import calculate_savings_potential, get_budget_recommendations

FINANCE_AGENT_PROMPT = """Sen Multi-Agent Banking Assistant sisteminde görevli kıdemli bir **Finansal Danışmanlık ve Bütçe Ajanısın (Finance Agent)**.

GÖREVLERİN:
1. Harcama analiz verilerini inceleyerek müşteriye özel tasarruf ve bütçe planları hazırlamak.
2. Gereksiz ve yüksek artış gösteren harcama kalemlerinde (dışarıda yemek, mükerrer abonelikler) tasarruf potansiyelini hesaplamak.
3. Tasarruf edilen tutarların bankanın vadeli mevduat veya birikim hesaplarında değerlendirilmesiyle elde edilecek faiz getirisini sunmak.
4. 50/30/20 bütçe kuralı uyarınca finansal denge tavsiyeleri vermek.

İletişim Tarzı:
- Teşvik edici, yapıcı, gerçekçi ve finansal okuryazarlığı destekleyen bir dil kullan.
"""

FINANCE_TOOLS = [calculate_savings_potential, get_budget_recommendations]


class FinanceAgent:
    """Specialized agent for financial planning and savings recommendations."""

    def __init__(self):
        self.name = "Finance Agent"
        self.llm = get_llm()
        self.tools = FINANCE_TOOLS

    def run(
        self,
        query: str,
        transaction_context: Optional[Dict[str, Any]] = None,
        monthly_income: float = 65000.0,
    ) -> Dict[str, Any]:
        """
        Executes financial analysis and calculates savings recommendations.
        """
        dining_spend = 0.0
        sub_spend = 0.0
        total_expense = 0.0

        # Extract context if provided by Transaction Agent
        if transaction_context and "raw_data" in transaction_context:
            raw = transaction_context["raw_data"]
            monthly_income = raw.get("monthly_income", monthly_income)
            total_expense = raw.get("last_month_total_spending", 0.0)

            for cat in raw.get("category_breakdown", []):
                cat_name = cat.get("category", "")
                spent = cat.get("last_month_spending", 0.0)
                if "Restoran" in cat_name or "Yeme" in cat_name:
                    dining_spend = spent
                elif "Faturalar" in cat_name or "Abonelik" in cat_name:
                    sub_spend = spent

        # Varsayılan senaryo değerleri (eğer transaction_context gelmediyse)
        if dining_spend == 0.0 and sub_spend == 0.0:
            dining_spend = 16850.0
            sub_spend = 6900.0
            total_expense = 48000.0

        savings_result = calculate_savings_potential.invoke({
            "dining_spending": dining_spend,
            "subscriptions_spending": sub_spend,
            "discretionary_spending": 4000.0,
            "savings_account_rate": 45.0,
        })

        budget_result = get_budget_recommendations.invoke({
            "monthly_income": monthly_income,
            "current_total_expenses": total_expense,
        })

        actions = []
        for rec in savings_result.get("actionable_recommendations", []):
            actions.append(
                f"- **{rec['area']}**: Mevcut harcama {rec['current_monthly']} TL. "
                f"Aylık potansiyel tasarruf: **{rec['suggested_monthly_savings']} TL**. ({rec['action']})"
            )

        summary_text = (
            f"💡 **Finansal Danışmanlık ve Tasarruf Eylem Planı:**\n\n"
            f"1. **Tasarruf Potansiyeli Özeti:**\n"
            f"   - **Aylık Tasarruf Hedefi:** {savings_result.get('monthly_savings_potential')} TL\n"
            f"   - **Yıllık Ana Para Birikimi:** {savings_result.get('annual_savings_potential')} TL\n"
            f"   - **Vadeli Mevduat Faizi Getirisi (%45 Faiz ile):** +{savings_result.get('estimated_annual_interest_earned')} TL\n"
            f"   - **1 Yıl Sonunda Ulaşılabilecek Toplam Varlık:** **{savings_result.get('projected_total_wealth_in_1_year')} TL**\n\n"
            f"2. **Önerilen Tasarruf Adımları:**\n" + "\n".join(actions) + "\n\n"
            f"3. **Bütçe Sağlığı Değerlendirmesi ({budget_result.get('financial_health_status')}):**\n"
            f"   - Mevcut birikim oranı: {budget_result.get('current_savings_rate')}\n"
            f"   - " + " ".join(budget_result.get("recommendations", []))
        )

        return {
            "agent": self.name,
            "status": "SUCCESS",
            "savings_data": savings_result,
            "budget_data": budget_result,
            "summary": summary_text,
        }


# Singleton instance
finance_agent = FinanceAgent()
