# 🎧 Vireo Support Intelligence

> **Deterministic CX Decision-Support & Operational Analytics Platform**  
> *Resolving the Headcount vs. Process Routing Dilemma for Vireo Audio (Task 1 V2)*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.34%2B-FF4B4B.svg)](https://streamlit.io/)
[![Pytest](https://img.shields.io/badge/pytest-Passing-brightgreen.svg)](https://pytest.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20Deterministic%20%2B%20AI-purple.svg)](#architecture)
[![Policy](https://img.shields.io/badge/Policy%20Compliance-Vireo%20v3.2-orange.svg)](#business-rules--policy-ground-truth)

---

## 📌 Executive Summary

**Vireo Support Intelligence** is a purpose-built, auditable decision-support application built for Priya Raman (Head of Customer Experience, Vireo Audio). It directly evaluates and solves the core strategic question:  
**"Should we hire two people for Billing, allocate headcount to Chat, or fix Logistics intake routing?"**

### 🎯 The Stated Business Goal (As a Specific Number)
> **"Reduce Billing first-response SLA breaches from 19.7% to below 8% and cut misrouted transfers by 50%, saving ₹2.60 Lakhs annually in direct penalty credits (₹350/breach) and internal transfer fees (₹305/transfer), while avoiding an unnecessary ₹9.0 Lakh annual commitment for 2 frontline hires in Chat."**

---

## 🔍 Key Business Findings from Data (11,641 Primary Tickets)

The application proves that the client's initial rule of thumb (*"whichever team has the most volume gets the next two hires"*) would lead to a costly operational error:

```
┌─────────────────────────┬──────────────┬──────────────────┬─────────────────┬───────────────────┬─────────────────────┐
│ Team / Queue            │ 18-Mo Volume │ SLA Breach Rate  │ SLA Credit Cost │ Transfers (Count) │ Transfer Cost (INR) │ Total Friction (INR)│
├─────────────────────────┼──────────────┼──────────────────┼─────────────────┼───────────────────┼─────────────────────┤
│ Chat Frontline          │ 3,030        │ 7.5%             │ ₹79,100         │ 245               │ ₹74,725             │ ₹1,53,825           │
│ Billing                 │ 2,425        │ 19.7% (Highest!) │ ₹1,66,950       │ 632 (Highest!)    │ ₹1,92,760           │ ₹3,59,710           │
│ Logistics               │ 1,905        │ 9.7%             │ ₹64,400         │ 112               │ ₹34,160             │ ₹98,560             │
│ Email Frontline         │ 1,807        │ 11.0%            │ ₹69,300         │ 139               │ ₹42,395             │ ₹1,11,695           │
│ Returns Desk            │ 1,049        │ 10.8%            │ ₹39,550         │ 46                │ ₹14,030             │ ₹53,580             │
│ Voice Frontline         │ 900          │ 5.7%             │ ₹17,850         │ 82                │ ₹25,010             │ ₹42,860             │
│ Escalations & Warranty  │ 525          │ 8.2%             │ ₹15,050         │ 43                │ ₹13,115             │ ₹28,165             │
└─────────────────────────┴──────────────┴──────────────────┴─────────────────┴───────────────────┴─────────────────────┘
```

1. **The Volume Illusion**: Chat Frontline receives the highest raw ticket volume (3,030) but operates efficiently with a low **7.5% breach rate**.
2. **The Bottleneck**: Billing experiences **477 SLA breaches** and **632 transfers**, generating the lowest CSAT (**3.02**) and **₹3.6 Lakhs** in measured operational friction.
3. **The Staffing Trap**: 2 new hires cost **₹9,00,000/year**. Even eliminating 100% of Billing SLA credits and transfers would only recover **~₹3.6L/year** (<40% of headcount cost). **Root cause fix**: Resolve upstream frontline intake misrouting first.

---

## 🏛️ Architecture: Zero-Hallucination Hybrid Model

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Streamlit User Interface                        │
│   [Decision Intelligence]  [Monthly Breakdowns]  [Simulator]  [Memo]   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
     ┌────────────────────────┐             ┌─────────────────────────┐
     │  Natural Language      │             │ Deterministic Analytics │
     │  Query Router          │             │ Engine (Pandas)         │
     │  (src/query_router.py) │             │ (src/analytics.py)      │
     └───────────┬────────────┘             └────────────┬────────────┘
                 │                                       │
                 ▼                                       ▼
     ┌────────────────────────┐             ┌─────────────────────────┐
     │ Executive AI Summaries │             │ Policy & Constants (v3.2│
     │ (Groq Llama-3.3-70B    │             │ (src/business_rules.py) │
     │  or Clean Local Engine)│             │ SLA: 15m/2h/4h/8h       │
     └────────────────────────┘             └─────────────────────────┘
```

* **100% Grounded Mathematical Integrity**: Mathematical computations, SLA breaches, FCR lookups, and transfer penalties are executed exclusively via Pandas. LLMs are never used as calculators.
* **Optional AI Executive Layer**: Groq Cloud API (`llama-3.3-70b-versatile` / `openai/gpt-oss-120b`) synthesizes computed metrics into crisp 2-sentence executive recommendations. If no API key is provided, it falls back seamlessly to deterministic output.

---

## ✨ Features & Interactive Tabs

### 1. 💬 Decision Intelligence & Chat Router
Ask natural language questions with dynamic headcount and team extraction:
* *"Should we hire two people for Billing or fix Logistics routing?"*
* *"Show me the 3 hiring team metrics"* (scales cost to ₹13,50,000)
* *"Show SLA breaches"*
* *"What is the repeat-contact rate?"*

### 2. 📊 Monthly Trends & Visual Breakdowns *(Priya's Direct Ask)*
* **Monthly Volume by Assigned Team** (interactive bar charts).
* **Monthly Volume by Issue Category** (trendline breakdown).
* **First-Response SLA Breach Rates** across all channels.
* **Internal Transfer Friction Cost** (₹305/transfer).

### 3. 👥 Staffing & ROI Simulator
* Interactive slider (1 to 10 hires).
* Real-time comparison: **Annual Headcount Budget** vs **Measured Friction Cost**.
* Decision guardrails preventing premature hiring commitments.

### 4. 📄 Executive Memo to Priya Raman
* Ready-to-read 1-page non-technical executive memo detailing the 3-point action plan.

---

## ⚡ Quick Start & Run Instructions

### Prerequisites
* Python 3.10, 3.11, or 3.12

### 1. Clone the Repository
```bash
git clone https://github.com/Rishabhp22/vireo-support-intelligence.git
cd vireo-support-intelligence
```

### 2. Create and Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Configure Free Groq API Key for AI Summaries
Copy `.env.example` to `.env` and add your free Groq API key (from [console.groq.com](https://console.groq.com/keys)):
```bash
cp .env.example .env
```
*(Note: The app works 100% offline without any API key).*

### 5. Launch the Streamlit App
```bash
streamlit run app.py
```
Open your browser at **`http://localhost:8502`**.

---

## 🧪 Running the Automated Test Suite

To verify data normalization, legacy cutoffs, 30-day FCR windows, and router accuracy:

```bash
pytest -q
```

---

## 📜 Business Rules & Policy Ground Truth (Vireo v3.2)

All operational thresholds are defined in [`src/business_rules.py`](src/business_rules.py):

| Parameter | Policy Value | Description |
|---|---|---|
| **Analysis Window** | `2025-01-01` to `2026-06-30` | 18-Month primary operational audit scope |
| **Helpdesk Cutover** | `2025-09-14` | Date when transfers started being recorded |
| **Chat SLA** | `0.25 hours` (15 min) | First-response threshold |
| **Voice SLA** | `2.0 hours` | Callback response threshold |
| **Social SLA** | `4.0 hours` | Social response threshold |
| **Email SLA** | `8.0 hours` | Email ticket response threshold |
| **SLA Breach Penalty** | `₹350.00` | Credit issued to customer per breached ticket |
| **Transfer Cost** | `₹305.00` | Internal cost per cross-queue transfer |
| **Annual Cost per Hire** | `₹4,50,000` | Standard planning assumption (₹9.0L for 2 hires) |

---

## 📂 Repository Structure

```text
vireo-support-intelligence/
│
├── data/                       # Primary CSV datasets (11,641 primary tickets)
│   ├── tickets.csv
│   ├── orders.csv
│   ├── customers.csv
│   ├── products.csv
│   └── agents.csv
│
├── knowledge/                  # Ground truth policy source materials
│   ├── README.md
│   └── support-policy.pdf      # Official Vireo Support Policy v3.2
│
├── src/                        # Core analytics & decision engine
│   ├── __init__.py
│   ├── analytics.py            # Deterministic Pandas metrics engine
│   ├── business_rules.py       # Auditable policy constants (v3.2)
│   ├── data_loader.py          # Resilient data pipeline, deduplication & aliases
│   └── query_router.py         # Dynamic headcount parsing & hybrid AI router
│
├── tests/                      # Automated test suite
│   └── test_end_to_end.py      # End-to-end integration tests
│
├── .env.example                # Safe environment configuration template
├── .gitignore                  # Excludes .env, virtual environments & caches
├── app.py                      # Interactive Streamlit application
├── requirements.txt            # Minimal, pinned Python dependencies
├── submission-form.md          # Completed official submission form
└── README.md                   # Project documentation
```

---

## 🛡️ License & Acknowledgments
Built for the **Vireo Audio 48-Hour Support Operations Challenge**. Designed with defensibility, transparency, and grounded business intelligence at its core.
