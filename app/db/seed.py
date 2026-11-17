"""Database seed script populating realistic banking data for the multi-agent system."""
from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal, init_db
from app.models.models import User, Account, Transaction, DocumentChunk, SupportTicket, utcnow


def seed_database():
    """Populate database with sample customer, accounts, transactions, and banking documents."""
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_user = db.query(User).filter(User.customer_number == "CUST-1001").first()
        if existing_user:
            print("Database already seeded with sample customer CUST-1001.")
            return

        print("Seeding database with banking data...")

        # 1. Create Sample Customer
        customer = User(
            customer_number="CUST-1001",
            full_name="Ali Yılmaz",
            email="ali.yilmaz@example.com",
            phone="+90 532 555 0123",
            monthly_income=65000.0,
            created_at=utcnow() - timedelta(days=180),
        )
        db.add(customer)
        db.flush()

        # 2. Create Accounts
        checking_account = Account(
            user_id=customer.id,
            account_number="TR320006100511123456789001",
            account_type="CHECKING",
            balance=28450.0,
            currency="TRY",
            card_last_four="4589",
            is_blocked=False,
            created_at=utcnow() - timedelta(days=180),
        )
        savings_account = Account(
            user_id=customer.id,
            account_number="TR320006100511123456789002",
            account_type="SAVINGS",
            balance=150000.0,
            currency="TRY",
            card_last_four=None,
            is_blocked=False,
            created_at=utcnow() - timedelta(days=120),
        )
        db.add_all([checking_account, savings_account])
        db.flush()

        # 3. Create Transactions (Two months ago vs Last month vs Current month)
        # Using relative dates so the "Geçen ay harcamalarım neden arttı?" question always works realistically!
        now = utcnow()
        # Define baseline month (60-31 days ago) and last month (30-1 days ago)
        transactions = []

        # --- Baseline Month (2 months ago: approx 31 to 60 days ago) ---
        # Normal spending: ~23,000 TRY
        baseline_items = [
            (-750.0, "Market & Gıda", "Migros", "Haftalık mutfak alışverişi", 58),
            (-1200.0, "Market & Gıda", "CarrefourSA", "Aylık temel gıda", 52),
            (-850.0, "Market & Gıda", "A101", "Temizlik ve kahvaltılık", 45),
            (-1100.0, "Market & Gıda", "Macrocenter", "Şarküteri alışverişi", 38),
            (-450.0, "Restoran & Yeme İçme", "Burger King", "Hızlı yemek", 55),
            (-800.0, "Restoran & Yeme İçme", "Köfteci Yusuf", "Aile yemeği", 47),
            (-650.0, "Restoran & Yeme İçme", "Starbucks", "Kahve ve tatlı", 40),
            (-500.0, "Restoran & Yeme İçme", "EspressoLab", "Kahve molaları", 35),
            (-950.0, "Faturalar & Abonelikler", "Enerjisa", "Elektrik faturası", 50),
            (-450.0, "Faturalar & Abonelikler", "İSKİ", "Su faturası", 48),
            (-350.0, "Faturalar & Abonelikler", "Turkcell", "Mobil hat faturası", 44),
            (-280.0, "Faturalar & Abonelikler", "Netflix", "Standart paket abonelik", 42),
            (-1800.0, "Ulaşım & Akaryakıt", "Shell", "Yakıt dolumu", 53),
            (-1750.0, "Ulaşım & Akaryakıt", "Opet", "Yakıt dolumu", 37),
            (-12000.0, "Kira & Konut", "Ev Sahibi Havale", "Aylık ev kirası", 32),
            (65000.0, "Maaş & Gelir", "ABC Teknoloji A.Ş.", "Aylık net maaş ödemesi", 31),
        ]

        for amt, cat, merch, desc, days_ago in baseline_items:
            transactions.append(
                Transaction(
                    account_id=checking_account.id,
                    amount=amt,
                    category=cat,
                    merchant=merch,
                    description=desc,
                    transaction_date=now - timedelta(days=days_ago),
                )
            )

        # --- Last Month (Spike Month: approx 1 to 30 days ago) ---
        # Spending jumped significantly!
        # Restoran surged from 2,400 -> 16,850 TRY (luxury dinners, frequent deliveries)
        # Subscriptions & Bills surged from 2,030 -> 6,900 TRY (new gym subscription, cloud services, food delivery club)
        last_month_items = [
            (-1400.0, "Market & Gıda", "Macrocenter", "Gurme market alışverişi", 28),
            (-1850.0, "Market & Gıda", "Migros Sanal Market", "Haftalık süpermarket", 21),
            (-1200.0, "Market & Gıda", "CarrefourSA", "Gıda ve içecek", 14),
            (-1600.0, "Market & Gıda", "Metro Grossmarket", "Toplu gıda alımı", 7),
            # Restoran Spike (16,850 TRY total)
            (-4200.0, "Restoran & Yeme İçme", "Nusr-Et Steakhouse", "Özel kutlama yemeği", 26),
            (-3100.0, "Restoran & Yeme İçme", "Sunset Grill & Bar", "İş akşam yemeği", 22),
            (-2450.0, "Restoran & Yeme İçme", "Lucca Bebek", "Hafta sonu akşam yemeği", 18),
            (-1800.0, "Restoran & Yeme İçme", "Zuma Restaurant", "Öğle yemeği", 15),
            (-1650.0, "Restoran & Yeme İçme", "Yemeksepeti", "Toplu sipariş", 12),
            (-1950.0, "Restoran & Yeme İçme", "GetirYemek", "Akşam yemekleri", 9),
            (-900.0, "Restoran & Yeme İçme", "Starbucks", "Kahve ve atıştırmalıklar", 5),
            (-800.0, "Restoran & Yeme İçme", "Midpoint", "Arkadaş buluşması", 3),
            # Subscriptions & Bills Spike (6,900 TRY total)
            (-3200.0, "Faturalar & Abonelikler", "MacFit Spor Salonu", "Yıllık üyelik yenileme ilk taksiti", 27),
            (-1100.0, "Faturalar & Abonelikler", "Enerjisa", "Elektrik faturası (klima kullanımı)", 25),
            (-650.0, "Faturalar & Abonelikler", "Apple Services", "iCloud + Apple One aboneliği", 20),
            (-550.0, "Faturalar & Abonelikler", "Spotify & Youtube", "Premium aile paketleri", 17),
            (-850.0, "Faturalar & Abonelikler", "OpenAI ChatGPT Plus", "Yapay zeka aboneliği", 10),
            (-550.0, "Faturalar & Abonelikler", "Turkcell", "Mobil hat ve aşım paketi", 6),
            # Transportation & Living
            (-2400.0, "Ulaşım & Akaryakıt", "Shell", "Akaryakıt alımı", 24),
            (-2200.0, "Ulaşım & Akaryakıt", "Uber", "Havalimanı ve şehir içi taksi", 11),
            (-12000.0, "Kira & Konut", "Ev Sahibi Havale", "Aylık ev kirası", 2),
            (65000.0, "Maaş & Gelir", "ABC Teknoloji A.Ş.", "Aylık net maaş ödemesi", 1),
        ]

        for amt, cat, merch, desc, days_ago in last_month_items:
            transactions.append(
                Transaction(
                    account_id=checking_account.id,
                    amount=amt,
                    category=cat,
                    merchant=merch,
                    description=desc,
                    transaction_date=now - timedelta(days=days_ago),
                )
            )

        db.add_all(transactions)

        # 4. Create Document Chunks for Document Agent (RAG / Policy Search)
        documents = [
            DocumentChunk(
                title="Kredi Kartı Yıllık Üyelik Ücreti ve İade Esasları",
                category="Kredi Kartı",
                content=(
                    "Banka Politikası Madde 14.2: Platinum ve Gold kart kullanıcıları için yıllık kart aidatı tahakkuk ettirilir. "
                    "Müşterinin son 12 ayda en az 50.000 TL kart harcaması bulunması veya aktif en az 2 adet otomatik fatura "
                    "ödeme talimatı vermesi halinde, kesilen aidat tutarının %100'ü karta bonus/nakit iade olarak 48 saat içinde yansıtılır. "
                    "Aidat itirazı için Support Agent aracılığıyla doğrudan bilet açılabilir."
                ),
            ),
            DocumentChunk(
                title="Vadeli Mevduat ve Birikim Hesabı Getiri Oranları 2026",
                category="Mevduat",
                content=(
                    "2026 Yılı Mevduat Faiz Tarifesi: 32-92 gün vadeli TL mevduat faiz oranı yıllık %45.00'tir. "
                    "Esnek Günlük Birikim Hesabı (O/N) için geçerli faiz oranı yıllık %41.50 olup vade bozulmadan para yatırma ve çekme imkanı sunar. "
                    "Düzenli Tasarruf Planı: Her ay maaş gününde vadesiz hesaptan birikim hesabına otomatik virman talimatı veren müşterilere "
                    "ek +%1.5 hoş geldin faiz primi uygulanmaktadır."
                ),
            ),
            DocumentChunk(
                title="Bireysel İhtiyaç Kredisi ve Harcama Yapılandırma Koşulları",
                category="Krediler",
                content=(
                    "Yüksek ekstre borçları veya harcama artışları için 'Ekstre Taksitlendir' özelliği ile 10.000 TL ve üzeri "
                    "kredi kartı borçları aylık %2.89 faiz oranı ile 3 ila 12 ay arasında taksitlendirilebilir. "
                    "Acil nakit ihtiyaçları için hazır ihtiyaç kredisi anında mobil şubeden veya asistan üzerinden onaylanabilir."
                ),
            ),
            DocumentChunk(
                title="Şüpheli İşlem Bildirimi, Kart Bloke ve Harcama İtiraz Süreci",
                category="Güvenlik",
                content=(
                    "Müşterilerimiz kartlarını kaybettiklerinde, çaldırdıklarında veya ekstresinde tanımadığı bir harcama gördüklerinde "
                    "asistan üzerinden anında geçici veya kalıcı kart blokesi koyabilirler. "
                    "Harcama itirazı (Chargeback) için işlem tarihinden itibaren 60 gün içinde başvuru yapılmalıdır. "
                    "İtiraz edilen tutar inceleme süresince geçici olarak alacak kaydedilir."
                ),
            ),
        ]
        db.add_all(documents)

        # 5. Create Sample Support Ticket
        sample_ticket = SupportTicket(
            user_id=customer.id,
            ticket_number="TCK-2026-1082",
            ticket_type="GENERAL_INQUIRY",
            status="RESOLVED",
            subject="Otomatik fatura talimatı bilgilendirmesi",
            description="Müşteri elektrik faturası için otomatik ödeme talimatı oluşturdu.",
            created_at=now - timedelta(days=45),
        )
        db.add(sample_ticket)

        db.commit()
        print("Database seeded successfully with realistic customer, accounts, transactions, and documents!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
