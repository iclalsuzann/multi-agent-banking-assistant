"""Document Agent: Specializes in searching and synthesizing banking regulations, policies, and terms."""
from typing import Dict, Any, Optional
from app.agents.base import get_llm
from app.tools.document_tools import search_banking_documents, get_banking_document_details

DOCUMENT_AGENT_PROMPT = """Sen Multi-Agent Banking Assistant sisteminde görevli kıdemli bir **Banka Mevzuat ve Doküman Ajanısın (Document Agent)**.

GÖREVLERİN:
1. Banka sözleşmeleri, mevduat faiz oranları, kredi kartı aidat politikaları ve prosedür dokümanlarından bilgi bulmak.
2. Müşterinin hukuki ve operasyonel sorularına net maddeler ve banka politikaları ile yanıt vermek.
3. İlgili doküman başlıklarını ve şartlarını açıkça belirtmek.

İletişim Tarzı:
- Güvenilir, kurumsal, anlaşılır ve şeffaf.
"""

DOCUMENT_TOOLS = [search_banking_documents, get_banking_document_details]


class DocumentAgent:
    """Specialized agent for searching bank documentation, policies, and contracts."""

    def __init__(self):
        self.name = "Document Agent"
        self.llm = get_llm()
        self.tools = DOCUMENT_TOOLS

    def run(self, query: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes document search and returns synthesized policy information.
        """
        search_res = search_banking_documents.invoke({
            "query": query,
            "category": category,
            "limit": 2,
        })

        docs = search_res.get("documents", [])
        if not docs:
            return {
                "agent": self.name,
                "status": "NOT_FOUND",
                "summary": "Aradığınız konuyla ilgili bankacılık dokümanı veya mevzuat kaydı bulunamadı.",
                "raw_data": search_res,
            }

        doc_summaries = []
        for d in docs:
            doc_summaries.append(
                f"📄 **{d['title']}** ({d['category']}):\n{d['content']}"
            )

        summary_text = (
            f"📚 **Bankacılık Mevzuat ve Politika Bilgisi:**\n\n"
            + "\n\n".join(doc_summaries)
        )

        return {
            "agent": self.name,
            "status": "SUCCESS",
            "summary": summary_text,
            "raw_data": search_res,
        }


# Singleton instance
document_agent = DocumentAgent()
