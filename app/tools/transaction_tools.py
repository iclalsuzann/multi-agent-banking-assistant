"""Transaction analysis tools for the Transaction Agent."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.models import User, Account, Transaction, utcnow


@tool
def get_customer_transactions(
    customer_number: str = "CUST-1001",
    days: int = 30,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Belirtilen müşterinin son X gün içerisindeki hesap hareketlerini ve harcamalarını getirir.
    
    Args:
        customer_number: Müşteri numarası (Örn: 'CUST-1001').
        days: Geriye dönük kaç günlük harcamanın sorgulanacağı (varsayılan: 30).
        category: İsteğe bağlı harcama kategorisi filtresi (Örn: 'Restoran & Yeme İçme', 'Market & Gıda').
    """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.customer_number == customer_number).first()
        if not user:
            return {"error": f"Müşteri bulunamadı: {customer_number}"}

        cutoff_date = utcnow() - timedelta(days=days)
        account_ids = [acc.id for acc in user.accounts]

        query = db.query(Transaction).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.transaction_date >= cutoff_date,
        )

        if category:
            query = query.filter(Transaction.category.ilike(f"%{category}%"))

        txs = query.order_by(Transaction.transaction_date.desc()).all()

        results = []
        total_expense = 0.0
        total_income = 0.0

        for t in txs:
            if t.amount < 0:
                total_expense += abs(t.amount)
            else:
                total_income += t.amount

            results.append({
                "id": t.id,
                "amount": t.amount,
                "currency": t.currency,
                "category": t.category,
                "merchant": t.merchant,
                "description": t.description,
                "date": t.transaction_date.strftime("%Y-%m-%d %H:%M"),
                "is_disputed": t.is_disputed,
            })

        return {
            "customer_number": customer_number,
            "period_days": days,
            "category_filter": category,
            "transaction_count": len(results),
            "total_expense": round(total_expense, 2),
            "total_income": round(total_income, 2),
            "transactions": results,
        }
    finally:
        db.close()


@tool
def analyze_spending_trends(
    customer_number: str = "CUST-1001",
) -> Dict[str, Any]:
    """
    Müşterinin son 30 gündeki harcamalarını bir önceki 30 günlük dönemle kıyaslayarak
    harcama artışlarını, kategorik değişimleri ve olağandışı harcama artışlarını (spikes) analiz eder.
    
    Args:
        customer_number: Müşteri numarası (Örn: 'CUST-1001').
    """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.customer_number == customer_number).first()
        if not user:
            return {"error": f"Müşteri bulunamadı: {customer_number}"}

        now = utcnow()
        last_month_start = now - timedelta(days=30)
        baseline_start = now - timedelta(days=60)
        account_ids = [acc.id for acc in user.accounts]

        all_txs = (
            db.query(Transaction)
            .filter(
                Transaction.account_id.in_(account_ids),
                Transaction.transaction_date >= baseline_start,
                Transaction.amount < 0,  # Sadece harcamalar
            )
            .all()
        )

        last_month_categories: Dict[str, float] = {}
        baseline_categories: Dict[str, float] = {}
        last_month_merchants: Dict[str, List[Dict[str, Any]]] = {}

        for t in all_txs:
            amt = abs(t.amount)
            if t.transaction_date >= last_month_start:
                last_month_categories[t.category] = last_month_categories.get(t.category, 0.0) + amt
                if t.category not in last_month_merchants:
                    last_month_merchants[t.category] = []
                last_month_merchants[t.category].append({
                    "merchant": t.merchant,
                    "amount": amt,
                    "date": t.transaction_date.strftime("%Y-%m-%d"),
                })
            else:
                baseline_categories[t.category] = baseline_categories.get(t.category, 0.0) + amt

        total_last_month = sum(last_month_categories.values())
        total_baseline = sum(baseline_categories.values())
        net_difference = total_last_month - total_baseline
        total_percent_change = (
            ((total_last_month - total_baseline) / total_baseline * 100) if total_baseline > 0 else 0.0
        )

        # Kategori karşılaştırması
        all_cats = set(last_month_categories.keys()).union(baseline_categories.keys())
        category_comparison = []

        for cat in all_cats:
            lm_val = round(last_month_categories.get(cat, 0.0), 2)
            bl_val = round(baseline_categories.get(cat, 0.0), 2)
            diff = round(lm_val - bl_val, 2)
            pct = round(((diff) / bl_val * 100), 1) if bl_val > 0 else (100.0 if lm_val > 0 else 0.0)

            # Bu kategorideki en yüksek harcama yapılan işyerleri
            top_merchants = sorted(
                last_month_merchants.get(cat, []),
                key=lambda x: x["amount"],
                reverse=True,
            )[:3]

            category_comparison.append({
                "category": cat,
                "last_month_spending": lm_val,
                "previous_month_spending": bl_val,
                "difference": diff,
                "percentage_change": pct,
                "top_merchants": top_merchants,
            })

        # Farkı en yüksek olandan en düşüğe sırala
        category_comparison.sort(key=lambda x: x["difference"], reverse=True)

        # En belirgin artış gösteren kategoriler (artış miktarı > 1000 TL)
        significant_spikes = [c for c in category_comparison if c["difference"] > 1000.0]

        return {
            "customer_number": customer_number,
            "customer_name": user.full_name,
            "monthly_income": user.monthly_income,
            "last_month_total_spending": round(total_last_month, 2),
            "previous_month_total_spending": round(total_baseline, 2),
            "net_spending_increase": round(net_difference, 2),
            "percentage_increase": round(total_percent_change, 1),
            "category_breakdown": category_comparison,
            "significant_spikes": significant_spikes,
            "primary_drivers": [
                f"{c['category']}: +{c['difference']} TL artış (%{c['percentage_change']})"
                for c in significant_spikes
            ],
        }
    finally:
        db.close()
