# Submission Form — Task 1 V2: Vireo Audio Support Intelligence

## 1. Candidate & Submission Details
* **Project Name**: Vireo Support Intelligence (Decision Support for Support Operations)
* **Dataset Used**: Vireo Audio Support Tickets (Set E, Jan 2025 – Jun 2026 primary period, 11,641 primary tickets).

---

## 2. The Stated Business Goal (As a Specific Number)
> **"Reduce Billing first-response SLA breaches from 19.7% to below 8% and cut misrouted transfers by 50%, saving ₹2.6 Lakhs annually in direct penalties (₹350/breach) and internal transfer waste (₹305/transfer), while avoiding an unnecessary ₹9.0 Lakh annual headcount commitment in Chat Frontline."**

---

## 3. How the Tool Works & Validation Evidence
* **Architecture**: Deterministic Python/Pandas calculation engine combined with a flexible Natural Language Query Router and interactive Streamlit UI.
* **Accuracy / Zero Hallucination**:
  * Adheres 100% to Vireo Support Policy v3.2.
  * SLA breaches are evaluated by channel response thresholds (Chat: 0.25h, Voice: 2h, Social: 4h, Email: 8h).
  * Excludes legacy pre-2025 records; tags pre-14 Sep 2025 helpdesk tickets where transfers were not recorded as `pd.NA` rather than zero.
  * Evaluates 30-day First Contact Resolution (FCR) with customer + issue lookback window.
* **Validation Suite**:
  * Automated end-to-end testing in `tests/test_end_to_end.py` covering messy data handling, alias normalization, deduplication, legacy cutoffs, and router accuracy.

---

## 4. Key Decisions & Trade-Offs Made (What We Chose and What We Left Out)
1. **Decision: Rejected Naive Volume-Based Hiring**:
   * Chat Frontline has the most tickets (3,030), but a healthy 7.5% SLA breach rate.
   * Billing has 2,425 tickets, but suffers the highest breach rate (19.7%, 477 breaches), lowest CSAT (3.02), and highest transfer friction (632 transfers, costing ₹1.92 Lakhs).
2. **Decision: Deterministic Math vs LLM Calculator**:
   * We strictly decoupled mathematical computations from LLMs. The app uses Pandas for 100% auditable figures and uses LLMs only for executive summarization and natural language intent understanding.
3. **What We Left Out / Discarded**:
   * We discarded naive text sentiment analysis on ticket bodies in favor of concrete, auditable CSAT and SLA metrics.
   * We did not treat legacy unrecorded transfers as zero (which would distort real transfer rates).

---

## 5. AI Tools Used & Cost Breakdown
* **AI Coding Assistants & Models**:
  * Google Gemini / Antigravity Agent for iterative architectural development, data pipeline construction, and test automation.
* **Total AI Cost**: ₹0 / $0 (used native developer APIs and local test harnesses).
