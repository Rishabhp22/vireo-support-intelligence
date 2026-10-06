# Source-material map

The analytics constants in `src/business_rules.py` implement the supplied Vireo support policy (version 3.2): SLA response targets, Rs 350 breach credits, contact and transfer costs, replacement planning cost, CSAT treatment, the 30-day FCR definition, and the current-helpdesk cutover date.

`support-policy.pdf` is retained here as the supplied policy source. The app calculates results from the CSVs in `data/`; it does not fabricate missing evidence from the email thread.
