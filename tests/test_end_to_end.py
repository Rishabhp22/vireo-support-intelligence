import pandas as pd
from src.data_loader import load_data
from src.analytics import Analytics
from src.query_router import answer


def test_messy_sources_and_router(tmp_path):
    pd.DataFrame({
        "Ticket ID": [1,2,3,4], "Customer ID": ["c1","c1","c2","c3"], "Order ID": ["o1","o1","o2","o3"],
        "Created": ["2025-09-15 00:00Z","2025-09-20 00:00Z","2025-10-01 00:00Z","2024-12-01 00:00Z"],
        "First Response": ["2025-09-15 00:20Z", None, "2025-10-01 01:00Z", "2024-12-01 01:00Z"],
        "Resolved": ["2025-09-16 00:00Z","2025-09-20 02:00Z","2025-10-03 00:00Z", "2024-12-02 00:00Z"],
        "Assigned Team": ["Billing","Billing","Logistics","Billing"], "Channel": ["Chat","chat","Email","Email"],
        "Transfers": [1, None, 2, 9], "CSAT": [5, None, 3, 1], "Issue": ["payment","payment","delivery","payment"],
        "Product ID": ["p1","p1","p2","p1"], "Replacement": ["no","no","yes","no"], "Refund": [0,0,100,0]
    }).to_csv(tmp_path / "tickets.csv", index=False)
    pd.DataFrame({"order_id":["o1","o2","o3"]}).to_csv(tmp_path / "orders.csv", index=False)
    pd.DataFrame({"customer_id":["c1","c2","c3"]}).to_csv(tmp_path / "customers.csv", index=False)
    pd.DataFrame({"product_id":["p1","p2"],"product_name":["One","Two"],"unit_cost":[500,1000]}).to_csv(tmp_path / "products.csv", index=False)
    pd.DataFrame({"agent_id":["a1"]}).to_csv(tmp_path / "agents.csv", index=False)
    data = load_data(tmp_path)
    a = Analytics(data.tickets)
    assert len(a.t) == 3
    assert a.transfers()["excluded_legacy_tickets"] == 0
    assert a.sla_breaches()["rows"][0]["breaches"] >= 1
    assert a.csat()["eligible_responses"] == 2
    assert answer("show transfers", a)["result"]["metric"].startswith("internal")
    three_hires = answer("Should we hire 3 people for Billing?", a)["result"]
    assert three_hires["hire_count"] == 3
    assert three_hires["total_annual_hiring_cost_inr"] == 1_350_000
    assert three_hires["focus_team"] == "Billing"
