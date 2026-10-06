# Vireo Support Intelligence

A focused, deterministic decision-support app for the Vireo Audio 48-hour support-operations challenge. It helps examine the Billing vs Logistics question without treating an LLM as a calculator.

## What it does

- Loads and normalizes `tickets.csv`, `orders.csv`, `customers.csv`, `products.csv`, and `agents.csv`.
- Excludes the stated legacy period (before 1 Jan 2025) from the primary analysis, while retaining a data-quality note.
- Treats legacy `transfers` as unavailable, never as zero; transfer metrics use only post-14 Sep 2025 helpdesk data.
- Implements policy SLA targets, Rs 350 breach credits, channel contact costs, Rs 305 transfer cost, and replacement cost (unit cost + Rs 340 shipping).
- Excludes blank CSAT, requires valid timestamps for SLA/handle-time metrics, and censors FCR cases that do not yet have a full 30-day observation window.
- Calculates FCR/repeat contacts as the same customer and issue returning within 30 days of resolution.
- Offers a small Streamlit chat interface. Its router selects deterministic analytics functions; it never asks a language model to calculate or fabricate values.

## Data placement

Place the supplied CSVs directly in [`data/`](data/):

```text
data/tickets.csv
data/orders.csv
data/customers.csv
data/products.csv
data/agents.csv
```

The supplied CSV exports are included in `data/`. The current export contains 11,780 tickets: 11,641 in the stated primary period and 139 pre-2025 legacy rows. The email thread was not available as a local file and is not used as a source of numerical truth.

Expected ticket fields are `ticket_id`, `customer_id`, `created_at`, `assigned_team`, and `channel`. Common export aliases (for example `Ticket ID`, `Created`, and `First Response`) are normalized automatically. It also recognizes the fields needed for the detailed metrics: `resolved_at`, `first_response_at`, `transfers`, `csat`, `issue`, `product_id`, `refund_amount`, and `replacement`.

## Run

```powershell
.\.vireo-venv\Scripts\python.exe -m streamlit run app.py
```

The project-local `.vireo-venv` environment is already configured for VS Code. Use **Terminal > Run Task > Run Vireo Support Intelligence** to start the app, or **Test Vireo Support Intelligence** to run validation.

Ask questions such as:

- `Should we hire two people for Billing or fix Logistics routing?`
- `Show SLA breaches`
- `What is the repeat-contact rate?`
- `Which product costs the most?`
- `Show monthly volume by team`

## Validation and decision guardrails

The staffing view compares observed SLA-credit and transfer costs with the Rs 9,00,000 planning cost of two hires. It explicitly labels those observed costs as a signal, **not** an assertion that staffing would recover them. Tier 2 should be examined on resolution duration and case complexity rather than Tier 1 ticket-volume comparisons.

For a staffing question, the app reads a stated hire count (for example, `3 hires` or `three people`) and scales the Rs 4,50,000-per-hire annual planning assumption. It also focuses the result when an assigned-team name appears in the question. Other question types remain intentionally constrained to defined analytics metrics; they are not a general-purpose LLM.

Run the included end-to-end validation:

```powershell
pytest -q
```

The test creates a temporary messy export with a legacy record, missing transfer/CSAT/response fields, an alias-based schema, and a product join. It checks cleaning, key policy metrics, and the chat router.
