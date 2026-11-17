"""Document search and RAG retrieval tools for Document Agent."""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.session import SessionLocal
from app.models.models import DocumentChunk


@tool
def search_banking_documents(
    query: str,
    category: Optional[str] = None,
    limit: int = 3,
) -> Dict[str, Any]:
    """
    Banka mevzuatları, kredi ve kart sözleşmeleri, faiz tarifeleri ve politika dokümanlarında arama yapar.
    
    Args:
        query: Aranacak konu veya anahtar kelime (Örn: 'kart aidatı iade', 'vadeli mevduat faiz', 'harcama itirazı').
        category: İsteğe bağlı kategori filtresi ('Kredi Kartı', 'Mevduat', 'Krediler', 'Güvenlik').
        limit: Döndürülecek maksimum doküman sayısı (varsayılan: 3).
    """
    db: Session = SessionLocal()
    try:
        keywords = [k.strip().lower() for k in query.split() if len(k.strip()) > 2]
        base_query = db.query(DocumentChunk)

        if category:
            base_query = base_query.filter(DocumentChunk.category.ilike(f"%{category}%"))

        # Kelime bazlı arama filtresi oluştur
        matched_chunks = []
        all_docs = base_query.all()

        for doc in all_docs:
            score = 0
            doc_text = f"{doc.title} {doc.content} {doc.category}".lower()

            # Tam arama ifadesi eşleşmesi
            if query.lower() in doc_text:
                score += 10

            # Kelime bazlı eşleşmeler
            for kw in keywords:
                if kw in doc.title.lower():
                    score += 5
                elif kw in doc_text:
                    score += 2

            if score > 0:
                matched_chunks.append({
                    "score": score,
                    "id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "content": doc.content,
                })

        # Skora göre sırala
        matched_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_results = matched_chunks[:limit]

        # Sonuç bulunamazsa kategori bazlı en alakalı dokümanları dön
        if not top_results and all_docs:
            top_results = [
                {
                    "score": 1,
                    "id": d.id,
                    "title": d.title,
                    "category": d.category,
                    "content": d.content,
                }
                for d in all_docs[:limit]
            ]

        return {
            "query": query,
            "category_filter": category,
            "match_count": len(top_results),
            "documents": top_results,
        }
    finally:
        db.close()


@tool
def get_banking_document_details(document_id: int) -> Dict[str, Any]:
    """
    ID numarası verilen bankacılık dokümanının tam metnini ve detaylarını getirir.
    
    Args:
        document_id: Dokümanın ID numarası.
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(DocumentChunk).filter(DocumentChunk.id == document_id).first()
        if not doc:
            return {"error": f"Doküman bulunamadı: ID {document_id}"}

        return {
            "id": doc.id,
            "title": doc.title,
            "category": doc.category,
            "content": doc.content,
            "created_at": doc.created_at.strftime("%Y-%m-%d"),
        }
    finally:
        db.close()
