"""
Demo script — tests the backend with sample Tesla documents
Run: python demo_test.py
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("MISTRAL_API_KEY", os.getenv("MISTRAL_API_KEY", ""))

TESLA_FINANCIAL = """
Tesla, Inc. — Annual Financial Summary 2023

Revenue: $96.8 billion (up 19% YoY)
Net Income: $14.1 billion (down 23% YoY due to margin compression)
Operating Margin: 9.2% (down from 16.8% prior year)
Free Cash Flow: $4.4 billion
Total Debt: $5.2 billion
Cash & Equivalents: $29.1 billion

Key Concerns:
- Gross margin fell to 17.6% due to aggressive price cuts across all vehicle lines
- Energy generation segment growing rapidly (+54% YoY) but still small
- Capex increasing significantly for Gigafactory expansions
- R&D spend $3.9B focused on next-gen platform and FSD development
- Inventory levels elevated: 15.5 days vs 12.1 prior year
- Vehicle delivery growth slowing: 1.81M units (up 38% but below 2M guidance)
"""

TESLA_LEGAL = """
Tesla Legal & Regulatory Exposure — Q4 2023

1. FTC Investigation: Federal Trade Commission reviewing Tesla's advertising claims
   around Autopilot and Full Self-Driving capabilities. Potential fine exposure.

2. NHTSA Investigations: 12 active investigations into Autopilot-related incidents.
   Recall of 2 million vehicles issued in December 2023 for Autopilot safety update.

3. SEC Scrutiny: Ongoing review of CEO Elon Musk's compensation package 
   (valued at $56 billion, rejected by shareholders in 2022).

4. Labor Disputes: Multiple NLRB complaints filed regarding alleged union suppression
   at Fremont, California and Buffalo, New York facilities.

5. Environmental Permits: EPA reviewing permits for Nevada Gigafactory expansion
   citing water usage concerns in drought-prone region.
"""

TESLA_NEWS = """
Tesla Media Coverage Compilation — 2023-2024

Bloomberg, Jan 2024: "Tesla's price war strategy backfires as margins collapse"
Tesla has cut vehicle prices 13 times since early 2023, eroding profitability 
while failing to stimulate the volume growth originally projected.

Reuters, Dec 2023: "Tesla Autopilot recall raises safety questions"
The largest software recall in automotive history affects over 2 million vehicles. 
NHTSA found the system inadequate at preventing driver misuse.

WSJ, Nov 2023: "Musk distraction factor weighing on Tesla stock"
Analysts cite CEO Elon Musk's involvement with X (Twitter), xAI, and SpaceX as 
a governance concern. Survey of institutional investors shows 67% view Musk's 
divided attention as a significant risk factor.

Financial Times, Oct 2023: "Tesla faces EV market share pressure from BYD"
Chinese competitor BYD surpassed Tesla in quarterly EV sales for first time.
European market share declining as local competitors gain ground.

Positive: Tesla Powerwall and energy storage orders hit record backlog, 
indicating strong diversification potential beyond automotive.
"""

TESLA_ESG = """
Tesla ESG Assessment 2023

ENVIRONMENTAL:
- Zero direct emissions from vehicles (positive)
- Gigafactory Nevada water consumption: 4.2M gallons/day in drought zone (risk)
- Battery supply chain: cobalt sourcing concerns from DRC operations
- Manufacturing waste: improving but still above industry benchmarks
- Carbon footprint of Gigafactory construction significant

SOCIAL:
- Workforce diversity: 21% women in leadership roles (below 30% target)
- Safety incidents: OSHA recordable rate 6.3 (above industry average of 4.2)
- CEO pay ratio: 1,351:1 (among highest in S&P 500)
- Community investment: $12M in 2023 (down from $18M in 2022)
- Social media controversy: Musk's political statements alienating customers

GOVERNANCE:
- Board independence: 4 of 8 directors have prior Musk relationships
- Compensation controversy: $56B CEO package under shareholder challenge
- Related party transactions: Multiple contracts with Musk-owned SpaceX
- Audit committee: Two members lack accounting expertise per proxy statement
- Whistleblower retaliation claims: 14 active complaints filed
"""


async def run_demo():
    print("=" * 60)
    print("DILIGENCE AI — DEMO TEST")
    print("=" * 60)

    if not os.environ.get("MISTRAL_API_KEY"):
        print("ERROR: MISTRAL_API_KEY not set")
        print("Set it with: export MISTRAL_API_KEY=your_key_here")
        return

    from document_processor import DocumentProcessor, Document
    from agents import DueDiligenceOrchestrator

    # Create mock documents
    docs = [
        Document("tesla_financial_2023.txt", TESLA_FINANCIAL, "financial"),
        Document("tesla_legal_2023.txt", TESLA_LEGAL, "legal"),
        Document("tesla_news_2023.txt", TESLA_NEWS, "news"),
        Document("tesla_esg_2023.txt", TESLA_ESG, "esg"),
    ]

    print(f"\n📁 Loaded {len(docs)} documents")
    print("🚀 Starting multi-agent analysis...\n")

    def progress(pct, agent):
        print(f"  [{pct:3d}%] {agent}")

    orchestrator = DueDiligenceOrchestrator(progress_callback=progress)
    result = await orchestrator.run(company_name="Tesla, Inc.", documents=docs)

    m = result.get("master", {})
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Company: {result['company_name']}")
    print(f"Overall Risk Score: {m.get('overall_risk_score')}/100")
    print(f"Risk Rating: {m.get('risk_rating')}")
    print(f"Recommendation: {m.get('investment_recommendation')}")
    print(f"Confidence: {m.get('confidence_score', 0)*100:.0f}%")
    print(f"\nExecutive Summary:\n{m.get('executive_summary', 'N/A')}")
    print("\nAgent Scores:")
    for k, v in (m.get("agent_scores") or {}).items():
        print(f"  {k.capitalize():15s}: {v}/100")

    import json
    with open("demo_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Full report saved to demo_result.json")


if __name__ == "__main__":
    asyncio.run(run_demo())
