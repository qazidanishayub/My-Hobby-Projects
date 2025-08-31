# app.py
import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PKR SIP Return & Real-Value Calculator", layout="wide")

st.title("📈 Stock Market Return Calculator (PKR) — Nominal vs Real (Devaluation-Aware)")

# =========================
# Documentation & Defaults
# =========================
with st.expander("ℹ️ How the calculator works (Default Calculation Mode)"):
    st.markdown(
        """
**Default Mode (if you don't change monthly customization):**
- You invest the **same amount every month** (set in the sidebar).
- Contributions are treated as **annuity due** by default (money goes in at the **start** of each month, then grows for the month).
- **Nominal annual return** is converted to an **effective monthly rate**.
- **Fees/Taxes (annual)** are converted to a monthly drag and reduce the nominal return to a **net nominal monthly rate**.
- **Devaluation/Inflation (annual)** is converted to a monthly rate and used to compute a **real (devaluation-adjusted)** series by discounting the nominal balance.
- **Step-up** (if any) increases your monthly contribution **once a year** on the chosen **Anchor Month** (e.g., January).
- If you enable **Monthly Customization**, you can specify a different contribution and optional **extra lump** per calendar month.  
  This **12-month pattern repeats** every year; step-ups (if set) still apply annually on the anchor month.
        """
    )

# ===============
# Sidebar Inputs
# ===============
with st.sidebar:
    st.header("Inputs")

    # Core cashflow defaults
    base_monthly_contribution = st.number_input("Base monthly contribution (PKR)", 0, 10_000_000, 100_000, step=10_000)
    years = st.slider("Duration (years)", 1, 40, 10)
    annuity_due = st.checkbox("Contribute at the start of each month (annuity due)", value=True)

    # Returns & drag
    nominal_annual_return_pct = st.number_input("Expected nominal annual return (%)", 0.0, 100.0, 19.85, step=0.05)
    annual_devaluation_pct = st.number_input("Annual devaluation / inflation (%)", 0.0, 100.0, 0.0, step=0.25)
    annual_fee_tax_drag_pct = st.number_input("Annual fees + tax drag (%)", 0.0, 20.0, 0.0, step=0.1)

    # Step-ups and extras
    step_up_pct = st.number_input("Annual step-up in contribution (%)", 0.0, 100.0, 0.0, step=1.0)
    lump_sum = st.number_input("One-time lump-sum at start (PKR)", 0, 1_000_000_000, 0, step=50_000)

    # Anchor month (applies to step-ups and acts as the yearly boundary)
    months_list = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]
    anchor_month = st.selectbox("Anchor month for annual effects", options=months_list, index=0)

    # Preset to match your example outputs
    st.markdown("---")
    if st.button("Use Example Preset (₨100k/month → ~₨3.4cr in 10y; ~₨24.3cr in 20y)"):
        st.session_state["base_monthly_contribution"] = 100_000
        st.session_state["years"] = 10
        st.session_state["nominal_annual_return_pct"] = 19.85
        st.session_state["annual_devaluation_pct"] = 0.0
        st.session_state["annual_fee_tax_drag_pct"] = 0.0
        st.session_state["step_up_pct"] = 0.0
        st.session_state["annuity_due"] = True
        st.session_state["lump_sum"] = 0
        st.session_state["anchor_month"] = "January"
        st.experimental_rerun()

# Reflect preset session state to live variables
base_monthly_contribution = st.session_state.get("base_monthly_contribution", base_monthly_contribution)
years = st.session_state.get("years", years)
nominal_annual_return_pct = st.session_state.get("nominal_annual_return_pct", nominal_annual_return_pct)
annual_devaluation_pct = st.session_state.get("annual_devaluation_pct", annual_devaluation_pct)
annual_fee_tax_drag_pct = st.session_state.get("annual_fee_tax_drag_pct", annual_fee_tax_drag_pct)
step_up_pct = st.session_state.get("step_up_pct", step_up_pct)
annuity_due = st.session_state.get("annuity_due", annuity_due)
lump_sum = st.session_state.get("lump_sum", lump_sum)
anchor_month = st.session_state.get("anchor_month", anchor_month)

months = years * 12
anchor_index = months_list.index(anchor_month)

# =========================
# Monthly Customization UI
# =========================
st.subheader("🗓️ Monthly Customization (Optional)")
st.caption("Specify a different monthly contribution and/or an extra lump for each calendar month. This 12-month pattern repeats every year.")

default_pattern = pd.DataFrame({
    "Month": months_list,
    "Contribution (PKR)": [base_monthly_contribution]*12,
    "Extra Lump (PKR)": [0]*12
})
pattern_df = st.data_editor(
    default_pattern,
    use_container_width=True,
    num_rows="fixed",
    key="pattern_editor",
    column_config={
        "Month": st.column_config.Column(disabled=True),
        "Contribution (PKR)": st.column_config.NumberColumn(min_value=0, step=10_000),
        "Extra Lump (PKR)": st.column_config.NumberColumn(min_value=0, step=10_000),
    }
)
use_monthly_customization = st.checkbox("Enable monthly customization pattern", value=False)

# ========================
# Rate Transform Utilities
# ========================
def eff_monthly_rate_from_annual(annual_pct: float) -> float:
    return (1 + annual_pct/100.0) ** (1/12) - 1

gross_monthly = eff_monthly_rate_from_annual(nominal_annual_return_pct)
drag_monthly = eff_monthly_rate_from_annual(annual_fee_tax_drag_pct)
net_nominal_monthly = (1 + gross_monthly) / (1 + drag_monthly) - 1
deval_monthly = eff_monthly_rate_from_annual(annual_devaluation_pct)

# =======================
# Build Cashflow Schedule
# =======================
dates = pd.date_range("2025-01-01", periods=months, freq="MS")
df = pd.DataFrame({"date": dates})
df["month_index"] = np.arange(len(df))
df["month_num_in_year"] = df["date"].dt.month - 1  # 0..11
df.set_index("date", inplace=True)

# Base contribution series (either flat or from pattern)
if use_monthly_customization:
    # Map month -> contribution and extra
    contrib_map = dict(zip(pattern_df["Month"], pattern_df["Contribution (PKR)"]))
    extra_map = dict(zip(pattern_df["Month"], pattern_df["Extra Lump (PKR)"]))
    df["contribution"] = df["month_num_in_year"].map(lambda i: contrib_map[months_list[i]])
    df["extra_lump"] = df["month_num_in_year"].map(lambda i: extra_map[months_list[i]])
else:
    df["contribution"] = base_monthly_contribution
    df["extra_lump"] = 0.0

# Apply annual step-ups on anchor months (cumulative)
if step_up_pct > 0:
    is_anchor = (df["month_num_in_year"] == anchor_index)
    step_factor = np.ones(len(df))
    cum = 1.0
    for i in range(len(df)):
        if is_anchor.iloc[i] and i != 0:
            cum *= (1 + step_up_pct/100.0)
        step_factor[i] = cum
    df["contribution"] = df["contribution"] * step_factor
    # Note: extra lumps are **not** step-upped (treated as fixed per calendar month pattern)

# =====================
# Compounding Engine
# =====================
def simulate_series(contribution_series, extra_series, lump_sum=0, monthly_rate=0.01, annuity_due=True):
    balance = 0.0
    balances = []
    for i, (c, x) in enumerate(zip(contribution_series, extra_series)):
        if i == 0 and lump_sum > 0:
            balance += lump_sum
        # Apply monthly injection
        if annuity_due:
            balance += c + x
            balance *= (1 + monthly_rate)
        else:
            balance *= (1 + monthly_rate)
            balance += c + x
        balances.append(balance)
    return np.array(balances)

df["nominal_balance"] = simulate_series(
    contribution_series=df["contribution"].values,
    extra_series=df["extra_lump"].values,
    lump_sum=lump_sum,
    monthly_rate=net_nominal_monthly,
    annuity_due=annuity_due
)

# Compute real (devaluation-adjusted) balance
discount_factors = (1 + deval_monthly) ** (df["month_index"] + 1)
df["real_balance"] = df["nominal_balance"] / discount_factors

# ================
# Summary & Charts
# ================
def to_crore(x): return x / 10_000_000

final_nominal = df["nominal_balance"].iloc[-1]
final_real = df["real_balance"].iloc[-1]
total_contrib = df["contribution"].sum() + df["extra_lump"].sum() + lump_sum
gain_nominal = final_nominal - total_contrib
gain_real = final_real - (total_contrib / ((1 + deval_monthly) ** months))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Final Nominal Value", f"₨ {final_nominal:,.0f}", help="Before devaluation")
c2.metric("Final Real Value (Devaluation-adjusted)", f"₨ {final_real:,.0f}")
c3.metric("Total Contributions", f"₨ {total_contrib:,.0f}")
c4.metric("Nominal Gain", f"₨ {gain_nominal:,.0f}")

st.divider()

st.subheader("Growth Over Time")
plot_df = df[["nominal_balance", "real_balance"]].rename(
    columns={"nominal_balance": "Nominal (PKR)", "real_balance": "Real (Devaluation-Adjusted PKR)"}
)
st.line_chart(plot_df, use_container_width=True)

with st.expander("View Month-by-Month Table"):
    show_cols = ["month_index", "contribution", "extra_lump", "nominal_balance", "real_balance"]
    st.dataframe(
        df[show_cols].style.format({
            "contribution": "₨ {:,.0f}",
            "extra_lump": "₨ {:,.0f}",
            "nominal_balance": "₨ {:,.0f}",
            "real_balance": "₨ {:,.0f}"
        }),
        use_container_width=True,
        height=520
    )

# Cross-check expander
st.divider()
with st.expander("Check 10-year vs 20-year outcomes (closed-form, level contributions only)"):
    def fv_annuity_due(monthly, r_m, n):
        if r_m == 0:
            return monthly * n
        return monthly * (((1 + r_m) ** n - 1) / r_m) * (1 + r_m)

    r_m = net_nominal_monthly
    # Closed-form assumes: no monthly customization, no extra lumps, no step-ups, no devaluation/fees beyond r_m
    fv_10y = fv_annuity_due(base_monthly_contribution, r_m, 10 * 12)
    fv_20y = fv_annuity_due(base_monthly_contribution, r_m, 20 * 12)

    st.write(
        f"""
        **Closed-form cross-check (level contributions only):**  
        • 10 years: **₨ {fv_10y:,.0f}** ({to_crore(fv_10y):.2f} crore)  
        • 20 years: **₨ {fv_20y:,.0f}** ({to_crore(fv_20y):.2f} crore)
        """
    )
    st.caption(
        "Tip: With ₨100,000/month, nominal annual ~19.85%, annuity-due, no devaluation/fees, "
        "10 years ≈ ₨3.4 crore and 20 years ≈ ₨24.3 crore (matches your example)."
    )

# Footer notes
st.markdown(
    """
---
**Notes**
- Monthly customization pattern repeats each year. Annual step-ups (if set) still occur on the **Anchor Month**.
- Extra lumps in the monthly pattern are applied every time that month occurs (e.g., every December).
- Real values discount the nominal balance by monthly devaluation.
"""
)
