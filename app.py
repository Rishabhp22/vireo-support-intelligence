from pathlib import Path
import streamlit as st
import pandas as pd
from src.data_loader import load_data
from src.analytics import Analytics
from src.query_router import answer

st.set_page_config(
    page_title="Vireo Support Intelligence | Decision Support",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header
st.title("🎧 Vireo Support Intelligence")
st.caption("AI & Policy-Grounded Decision Support for CX Operations — Headcount, Routing & Process Optimization")

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration & Data")
data_dir = Path(st.sidebar.text_input("CSV Folder Path", "data"))

try:
    data = load_data(data_dir)
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.info("Ensure tickets.csv, orders.csv, customers.csv, products.csv, and agents.csv are present in the folder.")
    st.stop()

analytics = Analytics(data.tickets)

# Quick Metric Tiles in Sidebar
with st.sidebar:
    st.divider()
    st.subheader("📌 Dataset Snapshot")
    st.metric("Total Primary Tickets", f"{len(analytics.t):,}")
    st.metric("Post-Cutover Tickets (with transfers)", f"{int(analytics.t['transfers_available'].sum()):,}")
    
    with st.expander("⚠️ Data Quality & Audit Notes", expanded=False):
        for note in data.quality_notes:
            st.info(note)

# Main Navigation Tabs
tab_chat, tab_dashboard, tab_simulator, tab_memo = st.tabs([
    "💬 Decision Intelligence",
    "📊 Monthly Trends & Breakdown",
    "👥 Staffing & ROI Simulator",
    "📄 Executive Memo to Priya Raman"
])

# ----------------------------------------------------
# TAB 1: DECISION INTELLIGENCE / CHAT ROUTER
# ----------------------------------------------------
with tab_chat:
    st.subheader("💡 Ask Operational Decision Questions")
    st.write("Type a natural language question or pick a prompt below to see policy-grounded analytics with dynamic headcount parameters.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🤔 Should we hire 2 people for Billing or fix Logistics?"):
            st.session_state["query_input"] = "Should we hire two people for Billing or fix Logistics routing?"
        if st.button("⏱️ Show SLA breaches and credit costs"):
            st.session_state["query_input"] = "Show SLA breaches"
    with col2:
        if st.button("👥 Show me the 3 hiring team metrics"):
            st.session_state["query_input"] = "Show me the 3 hiring team metrics"
        if st.button("🔄 Show transfer volume & routing costs"):
            st.session_state["query_input"] = "Show transfers"
    with col3:
        if st.button("🏷️ Show category volume breakdown"):
            st.session_state["query_input"] = "Show category volume breakdown"
        if st.button("🔁 What is the repeat-contact rate?"):
            st.session_state["query_input"] = "What is the repeat-contact rate?"

    default_q = st.session_state.get("query_input", "Should we hire two people for Billing or fix Logistics routing?")
    question = st.text_input("Your Question:", value=default_q)

    if st.button("Analyze Query", type="primary"):
        with st.spinner("Computing deterministic metrics..."):
            response = answer(question, analytics)
            
        st.success(f"**Insight:** {response['answer']}")
        
        res = response["result"]
        
        # Display formatted tables/charts based on result type
        if "rows" in res and isinstance(res["rows"], list) and len(res["rows"]) > 0:
            df_res = pd.DataFrame(res["rows"])
            st.markdown(f"### 📋 Metric: **{res.get('metric', 'Results').title()}**")
            
            # Show summary cards if available
            if "hire_count" in res:
                c1, c2, c3 = st.columns(3)
                c1.metric("Headcount Evaluated", f"{res['hire_count']} Hires")
                c2.metric("Annual Headcount Cost", f"₹{res['total_annual_hiring_cost_inr']:,.0f}")
                focus = res.get("focus_team") or "All Teams"
                c3.metric("Target Focus Team", focus)
                
            # Render chart and table
            col_left, col_right = st.columns([3, 2])
            with col_left:
                st.dataframe(df_res, use_container_width=True)
            with col_right:
                # Automatic sensible chart visualization
                num_cols = df_res.select_dtypes(include=["number"]).columns.tolist()
                cat_cols = df_res.select_dtypes(include=["object"]).columns.tolist()
                if cat_cols and num_cols:
                    chart_df = df_res.set_index(cat_cols[0])[num_cols[0]]
                    st.bar_chart(chart_df)
                    
            with st.expander("🔍 Inspect Full Deterministic JSON Output"):
                st.json(res)
        else:
            # Single object metric (e.g. repeat contacts / FCR)
            st.markdown(f"### 📋 Metric: **{res.get('metric', 'Results').title()}**")
            c1, c2, c3 = st.columns(3)
            if "fcr" in res and res["fcr"] is not None:
                c1.metric("First Contact Resolution (FCR)", f"{res['fcr']*100:.1f}%")
            if "repeat_contacts" in res:
                c2.metric("Repeat Contacts (within 30d)", f"{res['repeat_contacts']:,}")
            if "repeat_contact_cost_inr" in res:
                c3.metric("Repeat Contact Cost", f"₹{res['repeat_contact_cost_inr']:,.0f}")
                
            with st.expander("🔍 Inspect Full Deterministic JSON Output"):
                st.json(res)

# ----------------------------------------------------
# TAB 2: VISUAL DASHBOARD (PRIYA'S SPECIFIC REQUIREMENTS)
# ----------------------------------------------------
with tab_dashboard:
    st.subheader("📊 Monthly Breakdowns (By Team & By Category)")
    st.write("Direct fulfillment of Priya Raman's request: monthly volume breakdown charts by category and by assigned team.")
    
    dash_col1, dash_col2 = st.columns(2)
    
    with dash_col1:
        st.markdown("#### 🏢 Monthly Volume by Assigned Team")
        monthly_team = analytics.monthly_team_volume()["rows"]
        df_monthly_team = pd.DataFrame(monthly_team)
        pivot_team = df_monthly_team.pivot(index="month", columns="assigned_team", values="tickets").fillna(0)
        st.bar_chart(pivot_team)
        
    with dash_col2:
        st.markdown("#### 🏷️ Monthly Volume by Issue Category")
        monthly_cat = analytics.monthly_category_volume()["rows"]
        df_monthly_cat = pd.DataFrame(monthly_cat)
        pivot_cat = df_monthly_cat.pivot(index="month", columns="issue", values="tickets").fillna(0)
        st.line_chart(pivot_cat)

    st.divider()
    st.subheader("⚡ Operational Friction: SLA Breaches & Transfers")
    
    col_sla, col_trans = st.columns(2)
    with col_sla:
        st.markdown("#### ⏱️ First-Response SLA Breach Rate by Team")
        sla_data = pd.DataFrame(analytics.sla_breaches()["rows"])
        sla_data["breach_rate_pct"] = sla_data["breach_rate"] * 100
        st.bar_chart(sla_data.set_index("assigned_team")["breach_rate_pct"])
        st.caption("Billing exhibits the highest breach rate (19.7%), followed by Email Frontline (11.0%) and Returns Desk (10.8%).")
        
    with col_trans:
        st.markdown("#### 🔄 Internal Transfer Friction Cost (₹305/transfer)")
        trans_data = pd.DataFrame(analytics.transfers()["rows"])
        st.bar_chart(trans_data.set_index("assigned_team")["transfer_cost_inr"])
        st.caption("Billing accounts for 632 transfers (₹1.92 Lakhs), reflecting severe misrouting at frontline intake.")

# ----------------------------------------------------
# TAB 3: STAFFING & ROI SIMULATOR
# ----------------------------------------------------
with tab_simulator:
    st.subheader("👥 Headcount Scaling vs Process Friction Simulator")
    st.write("Compare the cost of adding new hires against the observed financial friction (SLA Breach Penalties + Internal Transfer Overhead).")
    
    sim_c1, sim_c2 = st.columns([1, 2])
    with sim_c1:
        sim_hires = st.slider("Select Headcount to Evaluate (Hires)", min_value=1, max_value=10, value=2, step=1)
        sim_team_options = ["All Teams"] + list(analytics.t["assigned_team"].dropna().unique())
        sim_selected_team = st.selectbox("Filter Focus Team", sim_team_options)
        
        target_team = None if sim_selected_team == "All Teams" else sim_selected_team
        sim_result = analytics.staffing_business_case(hire_count=sim_hires, focus_team=target_team)
        
        st.metric("Total Annual Hiring Budget", f"₹{sim_result['total_annual_hiring_cost_inr']:,.0f}")
        st.metric("Annual Cost per Hire", f"₹{sim_result['annual_cost_per_hire_inr']:,.0f}")
        
    with sim_c2:
        df_sim = pd.DataFrame(sim_result["rows"])
        df_sim["share_of_hiring_cost_pct"] = (df_sim["share_of_hiring_cost"] * 100).round(1)
        df_sim.columns = ["Team", "Observed Friction (SLA + Transfers) [INR]", "Friction as % of Hiring Cost", "Friction Share (%)"]
        
        st.markdown(f"#### 📊 Friction vs Headcount Cost ({sim_hires} Hires)")
        st.dataframe(df_sim[["Team", "Observed Friction (SLA + Transfers) [INR]", "Friction Share (%)"]], use_container_width=True)
        
        st.warning(
            f"**Key Decision Guardrail**: For {sim_hires} hires (Cost: ₹{sim_result['total_annual_hiring_cost_inr']:,.0f}), "
            "Billing has the highest observed pain (₹3,59,710), which represents only "
            f"**{(359710 / sim_result['total_annual_hiring_cost_inr']) * 100:.1f}%** of the headcount cost. "
            "Hiring will NOT eliminate transfer costs caused by upstream routing errors."
        )

# ----------------------------------------------------
# TAB 4: EXECUTIVE MEMO TO PRIYA RAMAN
# ----------------------------------------------------
with tab_memo:
    st.subheader("📄 One-Page Executive Decision Memo")
    st.markdown("""
### **MEMORANDUM**

**TO:** Priya Raman, Head of Customer Experience  
**FROM:** CX Operations Decision-Support Team  
**DATE:** October 2026  
**SUBJECT:** Headcount Allocation & Routing Optimization Strategy (Billing vs. Logistics vs. Frontline)  

---

#### **1. Executive Summary & Recommended Business Goal**
> **Target Business Goal:**  
> **"Reduce Billing first-response SLA breaches from 19.7% to <8% and cut misrouted transfers by 50%, saving ₹2.6 Lakhs annually in direct penalties and transfer waste, without adding fixed headcount."**

We strongly recommend **revising the initial rule of thumb** (*"whichever team has the most volume gets the next two hires"*). Adding 2 hires to the highest-volume queue (Chat Frontline, 3,030 tickets) will not resolve Vireo’s largest operational bottlenecks and commits **₹9,00,000 annually** to a team that already maintains a healthy **7.5% SLA breach rate**.

---

#### **2. Where the Real Pain Lives (Data Evidence)**

| Team / Queue | 18-Mo Volume | SLA Breach Rate | SLA Credit Cost | Transfers | Transfer Cost | Total Friction |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Chat Frontline** | **3,030** | 7.5% | ₹79,100 | 245 | ₹74,725 | ₹1,53,825 |
| **Billing** | 2,425 | **19.7%** | **₹1,66,950** | **632** | **₹1,92,760** | **₹3,59,710** |
| **Logistics** | 1,905 | 9.7% | ₹64,400 | 112 | ₹34,160 | ₹98,560 |
| **Email Frontline** | 1,807 | 11.0% | ₹69,300 | 139 | ₹42,395 | ₹1,11,695 |
| **Returns Desk** | 1,049 | 10.8% | ₹39,550 | 46 | ₹14,030 | ₹53,580 |

1. **Billing is the True Bottleneck, Not Chat**: Despite lower raw volume than Chat Frontline, Billing accounts for **₹3.6 Lakhs** in measurable friction (477 SLA breaches and 632 transfers). Its CSAT is the lowest in the organization (3.02 / 5.0).
2. **The Transfer Routing Problem**: Over 632 tickets get bounced into Billing from frontline channels, costing ₹1.92 Lakhs in wasted internal transfer fees (₹305/transfer).
3. **The Staffing Trap**: Adding two hires at ₹4.5L each costs **₹9,00,000/year**. Even if new hires completely eliminated all Billing SLA penalties, you would only recover ₹1.67L of value.

---

#### **3. Actionable 3-Point Strategic Plan**

1. **Fix Upstream Intake & Auto-Routing (Immediate - Week 1 to 4)**:
   * Implement automated intent classification at chat/email entry points to route payment and refund inquiries directly to Billing rather than frontline bounce-backs.
2. **Deflect Repetitive Billing & Delivery Queries via Self-Service**:
   * Deploy automated order tracking and payment status lookups in the IVR and Chat widget.
3. **Conditional Staffing Trigger**:
   * Re-evaluate Billing staffing only after intake routing is streamlined. If volume remains sustained above 180 tickets/agent/month post-routing fix, consider allocating 1 specialized billing specialist rather than 2 general frontline agents.
""")
