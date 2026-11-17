"""Orchestrator Agent (Supervisor) for Multi-Agent Banking Assistant."""
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.agents.base import get_llm

ORCHESTRATOR_SYSTEM_PROMPT = """Sen Multi-Agent Banking Assistant sisteminin lideri olan **Orchestrator Agent (Supervisor)** rolündesin.

GÖREVLERİN:
1. Müşterinin talebini detaylıca analiz etmek.
2. Talebin gerektirdiği uzman alt ajanı veya ajanları sırasıyla görevlendirmek:
   - **Transaction Agent**: Hesap hareketleri, harcama artışları (spikes), ekstre inceleme, bütçe trendleri.
   - **Finance Agent**: Tasarruf tavsiyeleri, bütçe optimizasyonu, 50/30/20 kuralı, mevduat faiz getirisi.
   - **Document Agent**: Banka mevzuatı, kart aidat iade şartları, faiz oranları, resmi bankacılık politikaları.
   - **Support Agent**: Kart bloke etme/dondurma, harcama itirazı (chargeback), bilet sorgulama.
3. Karmaşık talepleri parçalara ayırmak. Örneğin:
   "Geçen ay harcamalarım neden arttı ve nasıl tasarruf edebilirim?" sorusunda:
   Önce Transaction Agent'tan harcama analizini almalı, ardından bu veriyi Finance Agent'a ileterek tasarruf planı oluşturmalı ve nihai yanıtı müşteriye anlaşılır bir şekilde sunmalısın.
4. Müşteriye sunulacak nihai yanıtı sentezlemek.
"""


class OrchestratorAgent:
    """Supervisor agent coordinating specialized banking agents."""

    def __init__(self):
        self.name = "Orchestrator Agent"
        self.llm = get_llm()

    def route_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Determines the execution plan / agent sequence for the given query.
        Returns a list of agent identifiers in execution order.
        """
        lower_q = query.lower()
        plan: List[str] = []

        # Karmaşık senaryo: Hem harcama analizi hem tasarruf tavsiyesi
        has_spending = any(w in lower_q for w in ["harcama", "arttı", "neden arttı", "ekstre", "trend", "hareket"])
        has_saving = any(w in lower_q for w in ["tasarruf", "bütçe", "birikim", "nasıl tasarruf", "paramı nasıl"])

        if has_spending and has_saving:
            plan = ["transaction_agent", "finance_agent"]
        elif has_saving:
            plan = ["finance_agent"]
        elif has_spending:
            plan = ["transaction_agent"]
        elif any(w in lower_q for w in ["bloke", "dondur", "kayıp", "çalıntı", "itiraz", "bilet"]):
            plan = ["support_agent"]
        elif any(w in lower_q for w in ["aidat", "faiz", "mevzuat", "oran", "sözleşme", "politika", "doküman", "şart"]):
            plan = ["document_agent"]
        else:
            # Genel danışma - önce doküman veya genel yanıt
            plan = ["document_agent"]

        return plan

    def synthesize_response(
        self,
        query: str,
        agent_outputs: Dict[str, Any],
        customer_name: str = "Ali Yılmaz",
    ) -> str:
        """
        Synthesizes agent outputs into a unified, polite, structured banking response.
        """
        sections = []

        # Transaction Agent Çıktısı
        if "transaction_agent" in agent_outputs:
            sections.append(agent_outputs["transaction_agent"].get("summary", ""))

        # Finance Agent Çıktısı
        if "finance_agent" in agent_outputs:
            sections.append(agent_outputs["finance_agent"].get("summary", ""))

        # Document Agent Çıktısı
        if "document_agent" in agent_outputs:
            sections.append(agent_outputs["document_agent"].get("summary", ""))

        # Support Agent Çıktısı
        if "support_agent" in agent_outputs:
            sections.append(agent_outputs["support_agent"].get("summary", ""))

        combined_content = "\n\n---\n\n".join([s for s in sections if s])

        final_response = (
            f"Sayın **{customer_name}**, talebiniz uzman bankacılık asistanlarımız tarafından incelenmiştir:\n\n"
            f"{combined_content}\n\n"
            f"---\n"
            f"🏦 *Bankacılık Asistanınız olarak ek bir işlem veya detaylı hesap ekstresi için her zaman buradayım.*"
        )
        return final_response


# Singleton instance
orchestrator_agent = OrchestratorAgent()
