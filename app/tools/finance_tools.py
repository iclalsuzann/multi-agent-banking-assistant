"""Financial advisory and savings optimization tools for the Finance Agent."""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool


@tool
def calculate_savings_potential(
    dining_spending: float = 0.0,
    subscriptions_spending: float = 0.0,
    discretionary_spending: float = 0.0,
    savings_account_rate: float = 45.0,
) -> Dict[str, Any]:
    """
    Yüksek harcama kategorilerine göre potansiyel tasarruf tutarlarını ve 
    bu tasarrufun vadeli/birikim hesabında değerlendirilmesi durumundaki faiz getirisini hesaplar.
    
    Args:
        dining_spending: Restoran ve dışarıda yeme-içme harcama tutarı.
        subscriptions_spending: Abonelik ve fatura harcama tutarı.
        discretionary_spending: Diğer keyfi/lüks harcamalar toplamı.
        savings_account_rate: Vadeli birikim mevduat faiz oranı (varsayılan: %45.0).
    """
    # Önerilen tasarruf oranları:
    # Dışarıda yemeği %40 azaltmak
    # Kullanılmayan abonelikleri %35 sadeleştirmek
    # Keyfi harcamaları %25 kısmak
    dining_savings = dining_spending * 0.40
    subscription_savings = subscriptions_spending * 0.35
    discretionary_savings = discretionary_spending * 0.25

    total_monthly_savings = dining_savings + subscription_savings + discretionary_savings
    annual_principal = total_monthly_savings * 12

    # Bileşik/yıllık getiri yaklaşık hesabı (aylık düzenli birikim + mevduat faizi)
    # Basit ortalama bakiye üzerinden faiz hesabı
    annual_interest_earned = (annual_principal / 2) * (savings_account_rate / 100.0)
    total_annual_future_value = annual_principal + annual_interest_earned

    recommendations = []
    if dining_spending > 5000:
        recommendations.append({
            "area": "Dışarıda Yemek & Sipariş",
            "current_monthly": round(dining_spending, 2),
            "suggested_monthly_savings": round(dining_savings, 2),
            "action": "Haftalık yemek siparişlerini sınırlandırarak ve evde yemek hazırlayarak ayda yaklaşık %40 tasarruf edebilirsiniz.",
        })

    if subscriptions_spending > 2000:
        recommendations.append({
            "area": "Abonelikler & Üyelikler",
            "current_monthly": round(subscriptions_spending, 2),
            "suggested_monthly_savings": round(subscription_savings, 2),
            "action": "Yıllık spor salonu veya çoklu dijital platform (iCloud, Netflix, müzik vb.) üyeliklerini ortak/aile paketine çevirip kullanmadıklarınızı iptal edebilirsiniz.",
        })

    if discretionary_spending > 3000:
        recommendations.append({
            "area": "Genel Keyfi Harcamalar",
            "current_monthly": round(discretionary_spending, 2),
            "suggested_monthly_savings": round(discretionary_savings, 2),
            "action": "Acil durum fonu ve yatırım hedefleriniz için lüks tüketim kalemlerinde %25 kısıntı yapabilirsiniz.",
        })

    return {
        "monthly_savings_potential": round(total_monthly_savings, 2),
        "annual_savings_potential": round(annual_principal, 2),
        "estimated_annual_interest_earned": round(annual_interest_earned, 2),
        "projected_total_wealth_in_1_year": round(total_annual_future_value, 2),
        "savings_rate_applied": f"%{savings_account_rate}",
        "actionable_recommendations": recommendations,
    }


@tool
def get_budget_recommendations(
    monthly_income: float,
    current_total_expenses: float,
    essential_expenses: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Aylık gelir ve harcamaları 50/30/20 bütçe kuralı (İhtiyaçlar %50, İstekler %30, Birikim %20) 
    standartlarına göre değerlendirip bütçe optimizasyon planı sunar.
    
    Args:
        monthly_income: Müşterinin aylık net geliri.
        current_total_expenses: Müşterinin mevcut toplam aylık harcaması.
        essential_expenses: Temel zorunlu harcamalar (Kira, market, temel faturalar).
    """
    # 50/30/20 Hedefleri
    target_needs = monthly_income * 0.50
    target_wants = monthly_income * 0.30
    target_savings = monthly_income * 0.20

    current_savings = max(0.0, monthly_income - current_total_expenses)
    savings_rate = (current_savings / monthly_income * 100) if monthly_income > 0 else 0.0

    status = "SAĞLIKLI"
    if current_total_expenses > monthly_income:
        status = "BÜTÇE AÇIĞI (GELİRİ AŞAN HARCAMA)"
    elif savings_rate < 15.0:
        status = "YETERSİZ BİRİKİM ORANI"

    advice = []
    if current_total_expenses > monthly_income:
        deficit = current_total_expenses - monthly_income
        advice.append(
            f"Aylık harcamanız gelirinizi {round(deficit, 2)} TL aşıyor! Harcamalarınızı acilen ihtiyaç kategorilerine odaklamalısınız."
        )
    elif savings_rate < 20.0:
        gap = target_savings - current_savings
        advice.append(
            f"Hedeflenen %20'lik birikim oranına ulaşmak için aylık birikiminizi {round(gap, 2)} TL artırmalısınız."
        )
    else:
        advice.append(
            "Tebrikler! Birikim oranınız finansal sağlık kriterlerine (%20 ve üzeri) oldukça uygun."
        )

    return {
        "monthly_income": round(monthly_income, 2),
        "current_total_expenses": round(current_total_expenses, 2),
        "current_monthly_savings": round(current_savings, 2),
        "current_savings_rate": f"%{round(savings_rate, 1)}",
        "financial_health_status": status,
        "ideal_50_30_20_targets": {
            "needs_limit_50pct": round(target_needs, 2),
            "wants_limit_30pct": round(target_wants, 2),
            "savings_target_20pct": round(target_savings, 2),
        },
        "recommendations": advice,
    }
