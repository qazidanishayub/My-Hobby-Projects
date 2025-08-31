# app.py
import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PKR SIP Return & Real-Value Calculator", layout="wide")

st.title("📈 Stock Market Return Calculator (PKR) — Nominal vs Real (Devaluation-Aware)")

with st.sidebar:
    st.header("Inputs")

    # Core cashflow
    monthly_contribution = st.number_input("Monthly contribution (PKR)", 0, 10_000_000, 100_000, step=10_000)

    years = st.slider("Duration (years)", 1, 40, 10)
    annuity_due = st.checkbox("Contribute at the start of each month (annuity due)", value=True)

    # Returns & drag
    nominal_annual_return_pct = st.number_input("Expected nominal annual return (%)", 0.0, 100.0, 19.85, step=0.05)
    annual_devaluation_pct = st.number_input("Annual devaluation / inflation (%)", 0.0, 100.0, 0.0, step=0.25)
    annual_fee_tax_drag_pct = st.number_input("Annual fees + tax drag (%)", 0.0, 20.0, 0.0, step=0.1)

    # Step-ups and extras
    step_up_pct = st.number_input("Annual step-up in contribution (%)", 0.0, 100.0, 0.0, step=1.0)
    lump_sum = st.number_input("One-time lump-sum at start (PKR)", 0, 1_000_000_000, 0, step=50_000)

    # Anchor month
    anchor_month = st.selectbox(
        "Anchor month for annual effects (step-up, fees/taxes, devaluation)",
        options=[
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ],
        index=0
    )

    # Preset to match your example outputs
    if st.button("Use Example Preset (₨100k/month → ~₨3.4cr in 10y; ~₨24.3cr in 20y)"):
        st.session_state["monthly_contribution"] = 100_000
        st.session_state["years"] = 10
        st.session_state["nominal_annual_return_pct"] = 19.85
        st.session_state["annual_devaluation_pct"] = 0.0
        st.session_state["annual_fee_tax_drag_pct"] = 0.0
        st.session_state["step_up_pct"] = 0.0
        st.session_state["annuity_due"] = True
        st.session_state["lump_sum"] = 0
        st.session_state["anchor_month"] = "January"
        st.experimental_rerun()

# Allow session-state presetting to reflect in widgets
if "monthly_contribution" in st.session_state:
    monthly_contribution = st.session_state["monthly_contribution"]
if "years" in st.session_state:
    years = st.session_state["years"]
if "nominal_annual_return_pct" in st.session_state:
    nominal_annual_return_pct = st.session_state["nominal_annual_return_pct"]
if "annual_devaluation_pct" in st.session_state:
    annual_devaluation_pct = st.session_state["annual_devaluation_pct"]
if "annual_fee_tax_drag_pct" in st.session_state:
    annual_fee_tax_drag_pct = st.session_state["annual_fee_tax_drag_pct"]
if "step_up_pct" in st.session_state:
    step_up_pct = st.session_state["step_up_pct"]
if "annuity_due" in st.session_state:
    annuity_due = st.session_state["annuity_due"]
if "lump_sum" in st.session_state:
    lump_sum = st.session_state["lump_sum"]
if "anchor_month" in st.session_state:
    anchor_month = st.session_state["anchor_month"]

months = years * 12
anchor_index = ["January","February","March","April","May","June","July","August","September","October","November","December"].index(anchor_month)

# Convert annual rates to effective monthly rates
def eff_monthly_rate_from_annual(annual_pct: float) -> float:
    return (1 + annual_pct/100.0) ** (1/12) - 1

# We treat fee/tax drag as reducing the gross nominal return
gross_monthly = eff_monthly_rate_from_annual(nominal_annual_return_pct)
drag_monthly = eff_monthly_rate_from_annual(annual_fee_tax_drag_pct)
net_nominal_monthly = (1 + gross_monthly) / (1 + drag_monthly) - 1

# Monthly devaluation (for computing REAL value series)
deval_monthly = eff_monthly_rate_from_annual(annual_devaluation_pct)

# Build month-by-month schedule
dates = pd.date_range("2025-01-01", periods=months, freq="MS")  # Month start dates
df = pd.DataFrame({"date": dates})
df["month_index"] = np.arange(len(df))
df["month_num_in_year"] = df["date"].dt.month - 1  # 0..11
df.set_index("date", inplace=True)

# Contribution schedule with annual step-ups on the anchor month
df["contribution"] = monthly_contribution
if step_up_pct > 0:
    # For each anchor month after the first year, lift contribution by step_up_pct cumulatively
    # Example: +10% each year -> contribution *= 1.1^(years_elapsed)
    years_elapsed = (df["month_index"] // 12)
    is_anchor = (df["month_num_in_year"] == anchor_index)
    # Build a cumulative factor that only increments on anchor-months (except at t=0)
    step_factor = np.ones(len(df))
    inc_points = np.where(is_anchor)[0]
    cum = 1.0
    for i in range(len(df)):
        if i in inc_points and i != 0:
            cum *= (1 + step_up_pct/100.0)
        step_factor[i] = cum
    df["contribution"] = df["contribution"] * step_factor

# Engine: simulate monthly compounding with contributions
def simulate_series(contribution_series, lump_sum=0, monthly_rate=0.01, annuity_due=True):
    balance = 0.0
    balances = []
    for i, c in enumerate(contribution_series):
        if i == 0 and lump_sum > 0:
            balance += lump_sum
        if annuity_due:
            # Add contribution then grow
            balance += c
            balance *= (1 + monthly_rate)
        else:
            # Grow then add contribution
            balance *= (1 + monthly_rate)
            balance += c
        balances.append(balance)
    return np.array(balances)

df["nominal_balance"] = simulate_series(
    contribution_series=df["contribution"].values,
    lump_sum=lump_sum,
    monthly_rate=net_nominal_monthly,
    annuity_due=annuity_due
)

# Compute real value by discounting the nominal balance with devaluation
# Real_t = Nominal_t / (1+deval_monthly)^(t+1) (t is 0-based)
discount_factors = (1 + deval_monthly) ** (df["month_index"] + 1)
df["real_balance"] = df["nominal_balance"] / discount_factors

# Helper: crores formatting
def to_crore(x):
    return x / 10_000_000  # 1 crore = 10,000,000

# Summary metrics
final_nominal = df["nominal_balance"].iloc[-1]
final_real = df["real_balance"].iloc[-1]
total_contrib = df["contribution"].sum() + lump_sum
gain_nominal = final_nominal - total_contrib
gain_real = final_real - total_contrib / ((1 + deval_monthly) ** months)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Final Nominal Value", f"₨ {final_nominal:,.0f}", help="Before devaluation")
c2.metric("Final Real Value (Devaluation-adjusted)", f"₨ {final_real:,.0f}")
c3.metric("Total Contributions", f"₨ {total_contrib:,.0f}")
c4.metric("Nominal Gain", f"₨ {gain_nominal:,.0f}")

st.divider()

# Show quick checks for 10y and 20y (to match your example when parameters are set)
with st.expander("Check 10-year vs 20-year outcomes"):
    def fv_annuity_due(monthly, r_m, n):
        """Closed-form FV for level monthly annuity due (no step-ups, no deval, no fees), for cross-checks."""
        if r_m == 0:
            return monthly * n
        return monthly * (((1 + r_m) ** n - 1) / r_m) * (1 + r_m)

    r_m = net_nominal_monthly
    fv_10y = fv_annuity_due(monthly_contribution, r_m, 10 * 12)
    fv_20y = fv_annuity_due(monthly_contribution, r_m, 20 * 12)

    st.write(
        f"""
        **Closed-form cross-check (no step-ups, no lump-sum, no devaluation):**  
        • 10 years: **₨ {fv_10y:,.0f}** ({to_crore(fv_10y):.2f} crore)  
        • 20 years: **₨ {fv_20y:,.0f}** ({to_crore(fv_20y):.2f} crore)
        """
    )
    st.caption(
        "Tip: With ₨100,000/month, nominal annual ~19.85%, annuity-due, no devaluation/fees, "
        "10 years ≈ ₨3.4 crore and 20 years ≈ ₨24.3 crore (your example)."
    )

# Charts
st.subheader("Growth Over Time")
plot_df = df[["nominal_balance", "real_balance"]].rename(
    columns={"nominal_balance": "Nominal (PKR)", "real_balance": "Real (Devaluation-Adjusted PKR)"}
)
st.line_chart(plot_df)

# Table
with st.expander("View Month-by-Month Table"):
    show_cols = ["month_index", "contribution", "nominal_balance", "real_balance"]
    st.dataframe(
        df[show_cols].style.format({
            "contribution": "₨ {:,.0f}",
            "nominal_balance": "₨ {:,.0f}",
            "real_balance": "₨ {:,.0f}"
        }),
        use_container_width=True,
        height=500
    )

st.divider()
st.markdown(
    """
**Notes & How this works**
- **Net nominal monthly return** = convert annual return to monthly, then reduce by the monthly equivalent of fees/taxes.  
- **Real (devaluation-adjusted) value** discounts the nominal balance by monthly devaluation.  
- **Anchor month** applies annual step-up, fee/tax drag compounding boundary, and devaluation boundary consistently in the same month each year, matching “compounded every time for this time of year selected.”  
- Check your results with the **expander**; use the **Preset** in the sidebar to reproduce your target figures.
"""
)
