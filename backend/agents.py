"""
Multi-Agent Due Diligence Orchestrator
Uses Mistral AI for all reasoning
"""

import os
import json
import asyncio
from typing import Callable, Optional
from mistralai import Mistral
from document_processor import Document

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MODEL = "mistral-large-latest"


def get_client() -> Mistral:
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY environment variable not set")
    return Mistral(api_key=MISTRAL_API_KEY)


def truncate(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated, {len(text) - max_chars} more characters]"


async def call_mistral(client: Mistral, system: str, user: str) -> str:
    """Async wrapper around Mistral chat completion."""
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.chat.complete(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=3000,
        )
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# AGENT 1: Financial Risk Agent
# ─────────────────────────────────────────────

FINANCIAL_SYSTEM = """You are a senior financial analyst specializing in investment risk assessment.
Analyze the provided financial documents and extract key risk indicators.

Return ONLY valid JSON in this exact format:
{
  "risk_score": <integer 0-100>,
  "confidence": <float 0-1>,
  "key_metrics": {
    "revenue_trend": "<growing|stable|declining|unknown>",
    "debt_level": "<low|moderate|high|critical|unknown>",
    "cash_position": "<strong|adequate|weak|critical|unknown>",
    "profitability": "<profitable|breakeven|losing|unknown>"
  },
  "flags": [
    {"severity": "<high|medium|low>", "finding": "<description>", "evidence": "<quote or data point>"}
  ],
  "summary": "<2-3 sentence summary of financial risk>"
}"""

# ─────────────────────────────────────────────
# AGENT 2: Legal & Compliance Agent
# ─────────────────────────────────────────────

LEGAL_SYSTEM = """You are a senior legal counsel specializing in corporate due diligence.
Analyze documents for legal risks, regulatory exposure, litigation, and compliance issues.

Return ONLY valid JSON in this exact format:
{
  "risk_score": <integer 0-100>,
  "confidence": <float 0-1>,
  "categories": {
    "litigation_risk": "<high|medium|low|none|unknown>",
    "regulatory_risk": "<high|medium|low|none|unknown>",
    "contractual_risk": "<high|medium|low|none|unknown>",
    "ip_risk": "<high|medium|low|none|unknown>"
  },
  "flags": [
    {"severity": "<high|medium|low>", "finding": "<description>", "evidence": "<quote or reference>"}
  ],
  "summary": "<2-3 sentence summary of legal risk>"
}"""

# ─────────────────────────────────────────────
# AGENT 3: Reputation & Media Agent
# ─────────────────────────────────────────────

REPUTATION_SYSTEM = """You are a media intelligence analyst specializing in corporate reputation risk.
Analyze news articles, press releases, and media coverage for reputational risks and narrative patterns.

Return ONLY valid JSON in this exact format:
{
  "risk_score": <integer 0-100>,
  "confidence": <float 0-1>,
  "sentiment": {
    "overall": "<positive|neutral|mixed|negative|very_negative>",
    "trend": "<improving|stable|deteriorating|unknown>",
    "media_coverage": "<favorable|neutral|mixed|negative|unknown>"
  },
  "flags": [
    {"severity": "<high|medium|low>", "finding": "<description>", "evidence": "<quote or source>"}
  ],
  "summary": "<2-3 sentence summary of reputation risk>"
}"""

# ─────────────────────────────────────────────
# AGENT 4: ESG & Governance Agent
# ─────────────────────────────────────────────

ESG_SYSTEM = """You are an ESG (Environmental, Social, Governance) analyst specializing in sustainable investment risk.
Analyze documents for environmental, social, and governance risks and ethical concerns.

Return ONLY valid JSON in this exact format:
{
  "risk_score": <integer 0-100>,
  "confidence": <float 0-1>,
  "dimensions": {
    "environmental": "<high_risk|medium_risk|low_risk|unknown>",
    "social": "<high_risk|medium_risk|low_risk|unknown>",
    "governance": "<high_risk|medium_risk|low_risk|unknown>"
  },
  "flags": [
    {"severity": "<high|medium|low>", "finding": "<description>", "evidence": "<quote or reference>"}
  ],
  "summary": "<2-3 sentence summary of ESG risk>"
}"""

# ─────────────────────────────────────────────
# MASTER AGENT: Synthesis & Recommendation
# ─────────────────────────────────────────────

MASTER_SYSTEM = """You are the Chief Investment Risk Officer synthesizing a complete due diligence report.
You receive findings from 4 specialized agents and must produce a final investment risk assessment.

Return ONLY valid JSON in this exact format:
{
  "overall_risk_score": <integer 0-100>,
  "risk_rating": "<CRITICAL|HIGH|ELEVATED|MODERATE|LOW>",
  "investment_recommendation": "<AVOID|CAUTION|NEUTRAL|CONSIDER|RECOMMEND>",
  "confidence_score": <float 0-1>,
  "executive_summary": "<3-4 sentence executive summary for C-suite audience>",
  "key_risks": [
    {"rank": 1, "category": "<Financial|Legal|Reputation|ESG>", "risk": "<description>", "severity": "<high|medium|low>"}
  ],
  "strengths": ["<strength 1>", "<strength 2>"],
  "critical_flags": ["<most urgent item 1>", "<most urgent item 2>"],
  "recommended_actions": ["<action 1>", "<action 2>", "<action 3>"],
  "agent_scores": {
    "financial": <score>,
    "legal": <score>,
    "reputation": <score>,
    "esg": <score>
  }
}"""


def safe_parse_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    # Remove markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}\nText: {text[:500]}")
        return {}


class DueDiligenceOrchestrator:
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback or (lambda p, a: None)
        self.client = get_client()

    def _docs_for_type(self, documents: list[Document], doc_type: str) -> str:
        relevant = [d for d in documents if d.doc_type == doc_type]
        if not relevant:
            # Fall back to all docs if no type-specific ones
            relevant = documents
        combined = "\n\n---\n\n".join(
            f"[{d.filename}]\n{d.content}" for d in relevant
        )
        return truncate(combined, 15000)

    async def run(self, company_name: str, documents: list[Document]) -> dict:
        self.progress_callback(5, "Preparing documents")
        await asyncio.sleep(0.1)

        # Build context strings for each agent
        financial_ctx = self._docs_for_type(documents, "financial")
        legal_ctx = self._docs_for_type(documents, "legal")
        news_ctx = self._docs_for_type(documents, "news")
        esg_ctx = self._docs_for_type(documents, "esg")
        all_ctx = truncate("\n\n---\n\n".join(d.content for d in documents), 20000)

        # Run 4 agents in parallel
        self.progress_callback(10, "Financial Risk Agent")

        async def run_financial():
            self.progress_callback(15, "Financial Risk Agent analyzing...")
            prompt = f"Company: {company_name}\n\nDocuments:\n{financial_ctx}"
            result = await call_mistral(self.client, FINANCIAL_SYSTEM, prompt)
            self.progress_callback(35, "Financial Risk Agent complete")
            return safe_parse_json(result)

        async def run_legal():
            self.progress_callback(40, "Legal & Compliance Agent analyzing...")
            prompt = f"Company: {company_name}\n\nDocuments:\n{legal_ctx}"
            result = await call_mistral(self.client, LEGAL_SYSTEM, prompt)
            self.progress_callback(55, "Legal & Compliance Agent complete")
            return safe_parse_json(result)

        async def run_reputation():
            self.progress_callback(60, "Reputation & Media Agent analyzing...")
            prompt = f"Company: {company_name}\n\nDocuments:\n{news_ctx}"
            result = await call_mistral(self.client, REPUTATION_SYSTEM, prompt)
            self.progress_callback(72, "Reputation Agent complete")
            return safe_parse_json(result)

        async def run_esg():
            self.progress_callback(75, "ESG & Governance Agent analyzing...")
            prompt = f"Company: {company_name}\n\nDocuments:\n{esg_ctx}"
            result = await call_mistral(self.client, ESG_SYSTEM, prompt)
            self.progress_callback(85, "ESG Agent complete")
            return safe_parse_json(result)

        # Run all 4 agents concurrently
        financial_result, legal_result, reputation_result, esg_result = await asyncio.gather(
            run_financial(), run_legal(), run_reputation(), run_esg()
        )

        # Master synthesis
        self.progress_callback(88, "Master Reasoning Agent synthesizing...")

        master_prompt = f"""Company: {company_name}

FINANCIAL AGENT FINDINGS:
{json.dumps(financial_result, indent=2)}

LEGAL AGENT FINDINGS:
{json.dumps(legal_result, indent=2)}

REPUTATION AGENT FINDINGS:
{json.dumps(reputation_result, indent=2)}

ESG AGENT FINDINGS:
{json.dumps(esg_result, indent=2)}

Synthesize these findings into a comprehensive investment risk report."""

        master_response = await call_mistral(self.client, MASTER_SYSTEM, master_prompt)
        master_result = safe_parse_json(master_response)

        self.progress_callback(95, "Generating final report...")

        # Assemble full report
        report = {
            "company_name": company_name,
            "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "documents_analyzed": len(documents),
            "document_types": list(set(d.doc_type for d in documents)),
            "master": master_result,
            "agents": {
                "financial": financial_result,
                "legal": legal_result,
                "reputation": reputation_result,
                "esg": esg_result,
            },
        }

        return report
