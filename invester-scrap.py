import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Finance Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 28px 20px 20px;
        border-radius: 14px;
        text-align: center;
        color: white;
        margin-bottom: 24px;
    }
    .hero h1 { margin: 0; font-size: 2rem; letter-spacing: .5px; }
    .hero p  { margin: 6px 0 0; opacity: .8; font-size: .95rem; }

    /* Section divider label */
    .section-label {
        font-size: .75rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: #888;
        margin: 18px 0 4px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 22px;
        font-weight: 600;
        background: #f0f2f6;
        color: #1a1a2e !important;
    }
    .stTabs [aria-selected="true"] {
        background: #0f3460 !important;
        color: #ffffff !important;
    }

    /* Big metric value */
    div[data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 700; }

    /* Footer */
    .footer {
        text-align: center;
        color: #aaa;
        font-size: .8rem;
        padding: 12px 0 4px;
    }

    /* Highlight box */
    .highlight-box {
        background: linear-gradient(135deg,#667eea,#764ba2);
        border-radius: 10px;
        padding: 14px 18px;
        color: white;
        font-size: .9rem;
        line-height: 1.6;
    }
    .highlight-box-green {
        background: linear-gradient(135deg,#11998e,#38ef7d);
        border-radius: 10px;
        padding: 14px 18px;
        color: #1a3a1a;
        font-size: .9rem;
        line-height: 1.6;
    }
    .highlight-box-orange {
        background: linear-gradient(135deg,#f7971e,#ffd200);
        border-radius: 10px;
        padding: 14px 18px;
        color: #3a2500;
        font-size: .9rem;
        line-height: 1.6;
    }
    .highlight-box-red {
        background: linear-gradient(135deg,#cb2d3e,#ef473a);
        border-radius: 10px;
        padding: 14px 18px;
        color: white;
        font-size: .9rem;
        line-height: 1.6;
    }
    /* WhatsApp share button — override Streamlit's link colour at every state */
    .wa-btn,
    .wa-btn:link,
    .wa-btn:visited,
    .wa-btn:hover,
    .wa-btn:active,
    .wa-btn:focus {
        display: inline-block !important;
        background: #25D366 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        padding: 8px 20px !important;
        border-radius: 8px !important;
        text-decoration: none !important;
        font-weight: 600 !important;
        font-size: .875rem !important;
        margin-top: 10px !important;
        transition: background .2s;
    }
    .wa-btn:hover,
    .wa-btn:focus { background: #1db954 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_pkr(amount: float) -> str:
    """Return a human-readable PKR string (Cr / Lac / plain)."""
    if amount >= 10_000_000:
        return f"PKR {amount/10_000_000:.2f} Cr"
    elif amount >= 100_000:
        return f"PKR {amount/100_000:.2f} Lac"
    else:
        return f"PKR {amount:,.0f}"


def parse_investment(inv_type_en: str, inv_type_ur: str, language: str) -> float:
    """Render the right number-input and return the PKR amount."""
    if language == "English":
        lbl_map = {"Millions": (1_000_000, "Amount (millions):", 1.0, 0.5),
                   "Lacs":     (100_000,   "Amount (lacs):",    5.0, 1.0),
                   "Custom Amount": (1,    "Amount (PKR):",  100_000.0, 10_000.0)}
        mult, lbl, default, step = lbl_map[inv_type_en]
    else:
        lbl_map = {"ملین":      (1_000_000, "رقم (ملین میں):",   1.0, 0.5),
                   "لاکھ":      (100_000,   "رقم (لاکھ میں):",   5.0, 1.0),
                   "کسٹم رقم":  (1,         "رقم (روپے):",  100_000.0, 10_000.0)}
        mult, lbl, default, step = lbl_map[inv_type_ur]
    return st.number_input(lbl, min_value=0.0, value=default, step=step) * mult


def calculate_investment_scenario(
    investment: float, profit_rate: float, deduction_amt: float,
    months: int, apply_zakat: bool, apply_tax: bool, income_tax_rate: float,
) -> dict:
    """Run the compound investment loop with optional Zakat & income-tax deductions."""
    rows = []
    current = investment
    total_profit = 0.0
    total_zakat = 0.0
    total_tax_ded = 0.0
    annual_profit = 0.0

    for m in range(1, int(months) + 1):
        mp = current * profit_rate
        mp = max(0.0, mp - deduction_amt) if mp >= deduction_amt else 0.0

        tax_m = 0.0
        if apply_tax and mp > 0:
            tax_m = mp * (income_tax_rate / 100)
            mp -= tax_m

        current += mp
        annual_profit += mp
        total_profit += mp
        total_tax_ded += tax_m

        zakat_m = 0.0
        if apply_zakat and m % 12 == 0 and annual_profit > 0:
            zakat_m = annual_profit * 0.025
            current = max(0.0, current - zakat_m)
            total_zakat += zakat_m
            annual_profit = 0.0

        rows.append({
            "Month": m,
            "Monthly Profit": round(mp, 2),
            "Tax Deducted": round(tax_m, 2),
            "Zakat Deducted": round(zakat_m, 2),
            "Total Amount": round(current, 2),
        })

    roi = (total_profit / investment * 100) if investment > 0 else 0.0
    avg_monthly = total_profit / months if months > 0 else 0.0
    return {
        "rows": rows, "current": current, "total_profit": total_profit,
        "total_zakat": total_zakat, "total_tax": total_tax_ded,
        "roi": roi, "avg_monthly": avg_monthly,
    }


_SEP = "━" * 24

def wa_share(text: str, label: str) -> None:
    """Render a styled WhatsApp share anchor-button."""
    url = f"https://wa.me/?text={urllib.parse.quote(text, safe='')}"
    st.markdown(
        f'<a href="{url}" target="_blank" class="wa-btn">{label}</a>',
        unsafe_allow_html=True,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## ⚙️ Settings")
language = st.sidebar.selectbox("🌐 Language / زبان", ["English", "اردو"])
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Display Options")
show_chart     = st.sidebar.checkbox("Show Growth Charts",      value=True)
show_breakdown = st.sidebar.checkbox("Show Detailed Breakdown", value=False)
show_summary   = st.sidebar.checkbox("Show Summary Statistics", value=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**Smart Finance Calculator v3.0**")
st.sidebar.caption("Investment · Rent · Committee · Loan")

EN = language == "English"

# ── Hero Banner ───────────────────────────────────────────────────────────────
if EN:
    st.markdown("""
    <div class="hero">
        <h1>💰 Smart Finance Calculator</h1>
        <p>Investment Profit &amp; Rent Projection — built for Pakistani investors</p>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="hero">
        <h1>💰 سمارٹ فنانس کیلکولیٹر</h1>
        <p>سرمایہ کاری منافع اور کرایہ پروجیکشن — پاکستانی سرمایہ کاروں کے لیے</p>
    </div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_labels = (
    ["📈  Investment Calculator", "🏠  Rent Calculator", "🤝  Committee / BC", "🏦  Loan / EMI"]
    if EN else
    ["📈  سرمایہ کاری کیلکولیٹر", "🏠  کرایہ کیلکولیٹر", "🤝  کمیٹی / بی سی", "🏦  قرض / قسط"]
)
tab1, tab2, tab3, tab4 = st.tabs(tab_labels)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — INVESTMENT CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Enhancement 2: Compare toggle ────────────────────────────────────────
    compare_mode = st.checkbox(
        "🔀  Compare Two Scenarios" if EN else "🔀  دو منظرنامے موازنہ کریں",
        key="compare_mode",
    )

    # ── Enhancement 1: Zakat & Tax expander ──────────────────────────────────
    with st.expander(
        "⚙️  Deductions — Zakat & Tax" if EN else "⚙️  کٹوتیاں — زکوٰۃ اور ٹیکس",
        expanded=False,
    ):
        apply_zakat = st.checkbox(
            "Deduct Zakat (2.5% annually on accumulated profit)" if EN
            else "زکوٰۃ کاٹیں (سالانہ منافع پر 2.5%)",
            key="apply_zakat",
        )
        apply_tax = st.checkbox(
            "Deduct Income Tax on monthly profit" if EN
            else "ماہانہ منافع پر آمدنی ٹیکس کاٹیں",
            key="apply_tax",
        )
        income_tax_rate = 0.0
        if apply_tax:
            income_tax_rate = st.number_input(
                "Income tax rate (%):" if EN else "آمدنی ٹیکس کی شرح (%):",
                min_value=0.0, max_value=100.0, value=15.0, step=0.5,
                key="income_tax_rate",
            )

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    #  COMPARISON MODE
    # ══════════════════════════════════════════════════════════════════════════
    if compare_mode:
        st.markdown(
            f'<p class="section-label">{"Scenario Inputs" if EN else "منظرنامے کے ان پٹ"}</p>',
            unsafe_allow_html=True,
        )
        sc_a_col, sc_b_col = st.columns(2)

        # ── Scenario A inputs ─────────────────────────────────────────────────
        with sc_a_col:
            st.markdown("#### 📊 " + ("Scenario A" if EN else "منظرنامہ الف"))
            if EN:
                a_itype = st.selectbox("Investment type:", ["Millions", "Lacs", "Custom Amount"], key="a_itype")
                if a_itype == "Millions":
                    inv_a = st.number_input("Amount (millions):", min_value=0.0, value=1.0, step=0.5, key="a_iamt") * 1_000_000
                elif a_itype == "Lacs":
                    inv_a = st.number_input("Amount (lacs):", min_value=0.0, value=5.0, step=1.0, key="a_iamt") * 100_000
                else:
                    inv_a = st.number_input("Amount (PKR):", min_value=0.0, value=100_000.0, step=10_000.0, key="a_iamt")
                rate_a = st.number_input("Monthly profit rate (%):", min_value=0.0, value=3.0, step=0.1, key="a_rate") / 100
                ded_a  = st.number_input("Monthly deduction (PKR):", min_value=0.0, step=500.0, key="a_ded")
                meth_a = st.radio("Method:", ["Months", "Quarters"], horizontal=True, key="a_meth")
                mo_a   = int(st.number_input("Months:" if meth_a == "Months" else "Quarters:", min_value=1, value=12, step=1, key="a_mo"))
                if meth_a == "Quarters":
                    mo_a *= 3
            else:
                a_itype = st.selectbox("سرمایہ کاری کی قسم:", ["ملین", "لاکھ", "کسٹم رقم"], key="a_itype")
                if a_itype == "ملین":
                    inv_a = st.number_input("رقم (ملین):", min_value=0.0, value=1.0, step=0.5, key="a_iamt") * 1_000_000
                elif a_itype == "لاکھ":
                    inv_a = st.number_input("رقم (لاکھ):", min_value=0.0, value=5.0, step=1.0, key="a_iamt") * 100_000
                else:
                    inv_a = st.number_input("رقم (روپے):", min_value=0.0, value=100_000.0, step=10_000.0, key="a_iamt")
                rate_a = st.number_input("ماہانہ شرح (%):", min_value=0.0, value=3.0, step=0.1, key="a_rate") / 100
                ded_a  = st.number_input("ماہانہ کٹوتی (روپے):", min_value=0.0, step=500.0, key="a_ded")
                meth_a = st.radio("طریقہ:", ["مہینے", "سہ ماہی"], horizontal=True, key="a_meth")
                mo_a   = int(st.number_input("مہینے:" if meth_a == "مہینے" else "سہ ماہی:", min_value=1, value=12, step=1, key="a_mo"))
                if meth_a == "سہ ماہی":
                    mo_a *= 3

        # ── Scenario B inputs ─────────────────────────────────────────────────
        with sc_b_col:
            st.markdown("#### 📈 " + ("Scenario B" if EN else "منظرنامہ ب"))
            if EN:
                b_itype = st.selectbox("Investment type:", ["Millions", "Lacs", "Custom Amount"], key="b_itype")
                if b_itype == "Millions":
                    inv_b = st.number_input("Amount (millions):", min_value=0.0, value=1.0, step=0.5, key="b_iamt") * 1_000_000
                elif b_itype == "Lacs":
                    inv_b = st.number_input("Amount (lacs):", min_value=0.0, value=5.0, step=1.0, key="b_iamt") * 100_000
                else:
                    inv_b = st.number_input("Amount (PKR):", min_value=0.0, value=100_000.0, step=10_000.0, key="b_iamt")
                rate_b = st.number_input("Monthly profit rate (%):", min_value=0.0, value=4.0, step=0.1, key="b_rate") / 100
                ded_b  = st.number_input("Monthly deduction (PKR):", min_value=0.0, step=500.0, key="b_ded")
                meth_b = st.radio("Method:", ["Months", "Quarters"], horizontal=True, key="b_meth")
                mo_b   = int(st.number_input("Months:" if meth_b == "Months" else "Quarters:", min_value=1, value=12, step=1, key="b_mo"))
                if meth_b == "Quarters":
                    mo_b *= 3
            else:
                b_itype = st.selectbox("سرمایہ کاری کی قسم:", ["ملین", "لاکھ", "کسٹم رقم"], key="b_itype")
                if b_itype == "ملین":
                    inv_b = st.number_input("رقم (ملین):", min_value=0.0, value=1.0, step=0.5, key="b_iamt") * 1_000_000
                elif b_itype == "لاکھ":
                    inv_b = st.number_input("رقم (لاکھ):", min_value=0.0, value=5.0, step=1.0, key="b_iamt") * 100_000
                else:
                    inv_b = st.number_input("رقم (روپے):", min_value=0.0, value=100_000.0, step=10_000.0, key="b_iamt")
                rate_b = st.number_input("ماہانہ شرح (%):", min_value=0.0, value=4.0, step=0.1, key="b_rate") / 100
                ded_b  = st.number_input("ماہانہ کٹوتی (روپے):", min_value=0.0, step=500.0, key="b_ded")
                meth_b = st.radio("طریقہ:", ["مہینے", "سہ ماہی"], horizontal=True, key="b_meth")
                mo_b   = int(st.number_input("مہینے:" if meth_b == "مہینے" else "سہ ماہی:", min_value=1, value=12, step=1, key="b_mo"))
                if meth_b == "سہ ماہی":
                    mo_b *= 3

        # ── Calculate both ────────────────────────────────────────────────────
        res_a = calculate_investment_scenario(inv_a, rate_a, ded_a, mo_a, apply_zakat, apply_tax, income_tax_rate)
        res_b = calculate_investment_scenario(inv_b, rate_b, ded_b, mo_b, apply_zakat, apply_tax, income_tax_rate)

        # ── Side-by-side metrics ──────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            f'<p class="section-label">{"Side-by-Side Results" if EN else "موازنہ نتائج"}</p>',
            unsafe_allow_html=True,
        )
        h_a, h_b = st.columns(2)
        h_a.markdown(f"#### 📊 {'Scenario A' if EN else 'منظرنامہ الف'}")
        h_b.markdown(f"#### 📈 {'Scenario B' if EN else 'منظرنامہ ب'}")

        for label_en, label_ur, val_a, val_b, delta_a, delta_b in [
            ("Initial Investment", "ابتدائی سرمایہ", fmt_pkr(inv_a), fmt_pkr(inv_b), None, None),
            ("Total Profit",       "کل منافع",        fmt_pkr(res_a["total_profit"]), fmt_pkr(res_b["total_profit"]),
             f"+{res_a['roi']:.1f}% ROI", f"+{res_b['roi']:.1f}% ROI"),
            ("Final Amount",       "حتمی رقم",         fmt_pkr(res_a["current"]), fmt_pkr(res_b["current"]), None, None),
            ("Avg Monthly Profit", "اوسط ماہانہ منافع", fmt_pkr(res_a["avg_monthly"]), fmt_pkr(res_b["avg_monthly"]), None, None),
        ]:
            c_left, c_right = st.columns(2)
            c_left.metric(label_en if EN else label_ur, val_a, delta=delta_a)
            c_right.metric(label_en if EN else label_ur, val_b, delta=delta_b)

        # ── Verdict box ───────────────────────────────────────────────────────
        final_diff = res_b["current"] - res_a["current"]
        pct_diff   = (abs(final_diff) / res_a["current"] * 100) if res_a["current"] > 0 else 0
        if final_diff > 0:
            verd_en = (f"📈 <b>Scenario B</b> yields <b>{fmt_pkr(final_diff)}</b> more "
                       f"— a <b>{pct_diff:.1f}%</b> advantage over the projection period.")
            verd_ur = f"📈 <b>منظرنامہ ب</b> نے <b>{fmt_pkr(final_diff)}</b> زیادہ دیے — <b>{pct_diff:.1f}%</b> کا فرق۔"
            box_cls = "highlight-box-green"
        elif final_diff < 0:
            verd_en = (f"📊 <b>Scenario A</b> yields <b>{fmt_pkr(abs(final_diff))}</b> more "
                       f"— a <b>{pct_diff:.1f}%</b> advantage over the projection period.")
            verd_ur = f"📊 <b>منظرنامہ الف</b> نے <b>{fmt_pkr(abs(final_diff))}</b> زیادہ دیے — <b>{pct_diff:.1f}%</b> کا فرق۔"
            box_cls = "highlight-box"
        else:
            verd_en, verd_ur, box_cls = "Both scenarios yield identical results.", "دونوں یکساں نتائج۔", "highlight-box-orange"
        st.markdown(f'<div class="{box_cls}">' + (verd_en if EN else verd_ur) + "</div>", unsafe_allow_html=True)

        # ── Combined chart ────────────────────────────────────────────────────
        if show_chart:
            st.markdown("---")
            df_a_cmp = pd.DataFrame(res_a["rows"])
            df_b_cmp = pd.DataFrame(res_b["rows"])
            fig_cmp  = go.Figure()
            fig_cmp.add_trace(go.Scatter(
                x=df_a_cmp["Month"], y=df_a_cmp["Total Amount"],
                name="Scenario A" if EN else "منظرنامہ الف",
                fill="tozeroy", line=dict(color="#667eea", width=2.5),
                fillcolor="rgba(102,126,234,0.10)",
                hovertemplate="Month %{x}<br>A: PKR %{y:,.0f}<extra></extra>",
            ))
            fig_cmp.add_trace(go.Scatter(
                x=df_b_cmp["Month"], y=df_b_cmp["Total Amount"],
                name="Scenario B" if EN else "منظرنامہ ب",
                fill="tozeroy", line=dict(color="#11998e", width=2.5),
                fillcolor="rgba(17,153,142,0.10)",
                hovertemplate="Month %{x}<br>B: PKR %{y:,.0f}<extra></extra>",
            ))
            fig_cmp.update_layout(
                title=dict(text="📈 Scenario Comparison — Total Amount Growth" if EN
                           else "📈 منظرنامے موازنہ — کل رقم کی نمو", x=0.02),
                xaxis_title="Month" if EN else "مہینہ",
                yaxis_title="Total Amount (PKR)" if EN else "کل رقم (روپے)",
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=420, margin=dict(t=60, b=40),
            )
            st.plotly_chart(fig_cmp, use_container_width=True)

        # ── WhatsApp share (compare mode) ─────────────────────────────────────
        wa_txt = (
            f"📊 Investment Comparison (Smart Finance Calculator)\n{_SEP}\n"
            f"Scenario A\n"
            f"💰 Investment: {fmt_pkr(inv_a)}  |  Rate: {rate_a*100:.1f}%/mo  |  {mo_a} months\n"
            f"📈 Profit: {fmt_pkr(res_a['total_profit'])}  |  Final: {fmt_pkr(res_a['current'])}\n\n"
            f"Scenario B\n"
            f"💰 Investment: {fmt_pkr(inv_b)}  |  Rate: {rate_b*100:.1f}%/mo  |  {mo_b} months\n"
            f"📈 Profit: {fmt_pkr(res_b['total_profit'])}  |  Final: {fmt_pkr(res_b['current'])}\n"
            f"{_SEP}\n"
            f"{'Scenario B wins' if final_diff > 0 else 'Scenario A wins'} by {fmt_pkr(abs(final_diff))}\n"
            f"Calculated with Smart Finance Calculator"
        ) if EN else (
            f"📊 سرمایہ کاری موازنہ (سمارٹ فنانس کیلکولیٹر)\n{_SEP}\n"
            f"منظرنامہ الف: {fmt_pkr(inv_a)} | حتمی رقم: {fmt_pkr(res_a['current'])}\n"
            f"منظرنامہ ب: {fmt_pkr(inv_b)} | حتمی رقم: {fmt_pkr(res_b['current'])}\n"
            f"{_SEP}\n"
            f"فرق: {fmt_pkr(abs(final_diff))}"
        )
        wa_share(wa_txt, "Share Comparison on WhatsApp 📲" if EN else "واٹس ایپ پر موازنہ شیئر کریں 📲")

    # ══════════════════════════════════════════════════════════════════════════
    #  SINGLE SCENARIO MODE (existing layout, enhanced with Zakat/Tax)
    # ══════════════════════════════════════════════════════════════════════════
    else:
        st.markdown(
            f'<p class="section-label">{"Investment Details" if EN else "سرمایہ کاری کی تفصیلات"}</p>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)

        with col_a:
            if EN:
                inv_type_en = st.selectbox("Investment amount type:", ["Millions", "Lacs", "Custom Amount"])
                inv_type_ur = ""
            else:
                inv_type_ur = st.selectbox("سرمایہ کاری کی رقم کی قسم:", ["ملین", "لاکھ", "کسٹم رقم"])
                inv_type_en = ""
            investment = parse_investment(inv_type_en, inv_type_ur, language)
            if EN:
                profit_rate   = st.number_input("Monthly profit rate (%):", min_value=0.0, value=3.0, step=0.1) / 100
                deduction_amt = st.number_input("Monthly deduction from profit (PKR):", min_value=0.0, step=500.0)
            else:
                profit_rate   = st.number_input("ماہانہ منافع کی شرح (%):", min_value=0.0, value=3.0, step=0.1) / 100
                deduction_amt = st.number_input("ماہانہ کٹوتی (روپے):", min_value=0.0, step=500.0)

        with col_b:
            if EN:
                method = st.radio("Calculation method:",
                                  ["Number of Months", "Number of Quarters", "Custom Dates"],
                                  horizontal=True)
            else:
                method = st.radio("حساب کا طریقہ:",
                                  ["مہینوں کی تعداد", "سہ ماہی کی تعداد", "مخصوص تاریخیں"],
                                  horizontal=True)
            months: int = 12
            if method in ("Number of Months", "مہینوں کی تعداد"):
                months = int(st.number_input("Number of months:" if EN else "مہینوں کی تعداد:", min_value=1, value=12, step=1))
            elif method in ("Number of Quarters", "سہ ماہی کی تعداد"):
                q = int(st.number_input("Number of quarters:" if EN else "سہ ماہی کی تعداد:", min_value=1, value=4, step=1))
                months = q * 3
            else:
                c1, c2 = st.columns(2)
                with c1:
                    d_start = st.date_input("Start date:" if EN else "شروع کی تاریخ:")
                with c2:
                    d_end   = st.date_input("End date:"   if EN else "آخری تاریخ:")
                delta  = (d_end - d_start).days if d_start and d_end else 365
                months = max(1, round(delta / 30))
                st.caption(f"≈ {months} months detected" if EN else f"≈ {months} مہینے")

        # ── Calculation (now uses helper with Zakat/Tax support) ───────────────
        res         = calculate_investment_scenario(investment, profit_rate, deduction_amt, months,
                                                    apply_zakat, apply_tax, income_tax_rate)
        rows        = res["rows"]
        current     = res["current"]
        total_profit = res["total_profit"]
        roi          = res["roi"]
        avg_monthly  = res["avg_monthly"]
        total_zakat  = res["total_zakat"]
        total_tax_d  = res["total_tax"]

        # ── Key Metrics ───────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            f'<p class="section-label">{"Results Summary" if EN else "نتائج کا خلاصہ"}</p>',
            unsafe_allow_html=True,
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Initial Investment"   if EN else "ابتدائی سرمایہ",   fmt_pkr(investment))
        m2.metric("Total Profit"         if EN else "کل منافع",          fmt_pkr(total_profit), delta=f"+{roi:.1f}% ROI")
        m3.metric("Final Amount"         if EN else "حتمی رقم",          fmt_pkr(current))
        m4.metric("Avg Monthly Profit"   if EN else "اوسط ماہانہ منافع", fmt_pkr(avg_monthly))

        # Deduction summary caption
        if apply_zakat or apply_tax:
            parts = []
            if apply_zakat: parts.append(f"Zakat {fmt_pkr(total_zakat)}" if EN else f"زکوٰۃ {fmt_pkr(total_zakat)}")
            if apply_tax:   parts.append(f"Tax {fmt_pkr(total_tax_d)}" if EN else f"ٹیکس {fmt_pkr(total_tax_d)}")
            eff_roi = ((current - investment) / investment * 100) if investment > 0 else 0
            st.caption(("Deductions applied — " if EN else "لاگو کٹوتیاں — ")
                       + "  |  ".join(parts)
                       + (f"  →  Net ROI: {eff_roi:.1f}%" if EN else f"  →  خالص ROI: {eff_roi:.1f}%"))

        # ── Summary Stats ─────────────────────────────────────────────────────
        if show_summary:
            st.markdown("")
            si1, si2, si3 = st.columns(3)
            si1.info(f"**Duration:** {months} months  ({months/12:.1f} yrs)" if EN
                     else f"**مدت:** {months} مہینے ({months/12:.1f} سال)")
            si2.info(f"**Rate:** {profit_rate*100:.2f}%/mo  →  {profit_rate*1200:.1f}%/yr" if EN
                     else f"**شرح:** {profit_rate*100:.2f}% ماہانہ → {profit_rate*1200:.1f}% سالانہ")
            si3.info(f"**Monthly Deduction:** {fmt_pkr(deduction_amt)}" if EN
                     else f"**ماہانہ کٹوتی:** {fmt_pkr(deduction_amt)}")

            growth_factor = (current / investment) if investment > 0 else 1
            eff_roi       = ((current - investment) / investment * 100) if investment > 0 else 0
            extra_note    = ""
            if apply_zakat or apply_tax:
                extra_note = (f" After Zakat &amp; tax, effective net return: <b>{eff_roi:.1f}%</b>."
                              if EN else f" زکوٰۃ اور ٹیکس کے بعد مؤثر واپسی: <b>{eff_roi:.1f}%</b>۔")
            st.markdown(
                f'<div class="highlight-box">💡 '
                + (f"Your <b>PKR {investment/100000:.1f} Lac</b> investment grows to "
                   f"<b>{fmt_pkr(current)}</b> in <b>{months} months</b> — "
                   f"a <b>{growth_factor:.2f}×</b> return at {profit_rate*100:.1f}%/mo compounded."
                   + extra_note
                   if EN else
                   f"آپ کی <b>{fmt_pkr(investment)}</b> سرمایہ کاری <b>{months} مہینوں</b> میں "
                   f"<b>{fmt_pkr(current)}</b> ہو جاتی ہے — <b>{growth_factor:.2f}×</b> واپسی۔"
                   + extra_note)
                + "</div>",
                unsafe_allow_html=True,
            )

        # ── Chart ─────────────────────────────────────────────────────────────
        if show_chart and rows:
            st.markdown("---")
            df = pd.DataFrame(rows)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["Month"], y=df["Total Amount"],
                name="Total Amount" if EN else "کل رقم",
                fill="tozeroy", line=dict(color="#667eea", width=2.5),
                fillcolor="rgba(102,126,234,0.12)",
                hovertemplate="Month %{x}<br>Total: PKR %{y:,.0f}<extra></extra>",
            ))
            fig.add_trace(go.Bar(
                x=df["Month"], y=df["Monthly Profit"],
                name="Monthly Profit" if EN else "ماہانہ منافع",
                marker_color="rgba(118,75,162,0.65)", yaxis="y2",
                hovertemplate="Month %{x}<br>Profit: PKR %{y:,.0f}<extra></extra>",
            ))
            fig.update_layout(
                title=dict(text="📈 Investment Growth Over Time" if EN else "📈 وقت کے ساتھ سرمایہ کاری کی نمو", x=0.02),
                xaxis_title="Month" if EN else "مہینہ",
                yaxis_title="Total Amount (PKR)" if EN else "کل رقم (روپے)",
                yaxis2=dict(title="Monthly Profit (PKR)", overlaying="y", side="right", showgrid=False),
                hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=420, margin=dict(t=60, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── Breakdown Table + Export ───────────────────────────────────────────
        if show_breakdown and rows:
            st.markdown("---")
            st.markdown(
                f'<p class="section-label">{"Monthly Breakdown" if EN else "ماہانہ تفصیل"}</p>',
                unsafe_allow_html=True,
            )
            df_disp = pd.DataFrame(rows)
            # Format numeric columns
            for c_name in ["Monthly Profit", "Total Amount", "Tax Deducted", "Zakat Deducted"]:
                if c_name in df_disp.columns:
                    df_disp[c_name] = df_disp[c_name].map(lambda x: f"PKR {x:,.0f}")
            # Drop unused deduction columns
            if not apply_tax   and "Tax Deducted"   in df_disp.columns: df_disp.drop(columns=["Tax Deducted"],   inplace=True)
            if not apply_zakat and "Zakat Deducted" in df_disp.columns: df_disp.drop(columns=["Zakat Deducted"], inplace=True)
            # Translate column headers for Urdu
            if not EN:
                df_disp.rename(columns={"Month": "مہینہ", "Monthly Profit": "ماہانہ منافع",
                                        "Tax Deducted": "ٹیکس کٹوتی", "Zakat Deducted": "زکوٰۃ کٹوتی",
                                        "Total Amount": "کل رقم"}, inplace=True)
            st.dataframe(df_disp, use_container_width=True, hide_index=True)

            st.download_button(
                "📥 Download CSV" if EN else "📥 CSV ڈاؤن لوڈ کریں",
                data=pd.DataFrame(rows).to_csv(index=False),
                file_name="investment_breakdown.csv",
                mime="text/csv",
            )

        # ── Enhancement 3: WhatsApp share (single mode) ───────────────────────
        eff_roi_wa = ((current - investment) / investment * 100) if investment > 0 else 0
        ded_note   = ""
        if apply_zakat: ded_note += f"\n🕌 Zakat Deducted: {fmt_pkr(total_zakat)}"
        if apply_tax:   ded_note += f"\n🏛 Tax Deducted: {fmt_pkr(total_tax_d)}"
        wa_inv = (
            f"📊 Investment Summary (Smart Finance Calculator)\n{_SEP}\n"
            f"💰 Initial Investment: {fmt_pkr(investment)}\n"
            f"📈 Total Profit: {fmt_pkr(total_profit)} ({roi:.1f}% ROI)\n"
            f"🏦 Final Amount: {fmt_pkr(current)}\n"
            f"⏱ Duration: {months} months  |  Rate: {profit_rate*100:.1f}%/mo"
            + ded_note + f"\n{_SEP}\nCalculated with Smart Finance Calculator"
        ) if EN else (
            f"📊 سرمایہ کاری خلاصہ (سمارٹ فنانس کیلکولیٹر)\n{_SEP}\n"
            f"💰 ابتدائی سرمایہ: {fmt_pkr(investment)}\n"
            f"📈 کل منافع: {fmt_pkr(total_profit)} ({roi:.1f}% ROI)\n"
            f"🏦 حتمی رقم: {fmt_pkr(current)}\n"
            f"⏱ مدت: {months} مہینے  |  شرح: {profit_rate*100:.1f}%/ماہ"
            + ded_note + f"\n{_SEP}\nسمارٹ فنانس کیلکولیٹر"
        )
        wa_share(wa_inv, "Share on WhatsApp 📲" if EN else "واٹس ایپ پر شیئر کریں 📲")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — RENT CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(
        f'<p class="section-label">{"Rent Projection with Annual Increase" if EN else "سالانہ اضافے کے ساتھ کرایہ پروجیکشن"}</p>',
        unsafe_allow_html=True,
    )
    if EN:
        st.caption("Model your rental income across multiple years, accounting for annual hikes, vacancies, and expenses.")
    else:
        st.caption("سالانہ اضافے، خالی مدت اور اخراجات کو مدنظر رکھتے ہوئے کئی سالوں میں اپنی کرایہ آمدنی کا اندازہ لگائیں۔")

    r1, r2 = st.columns(2)

    # ── Rent Inputs ───────────────────────────────────────────────────────────
    with r1:
        if EN:
            rent_unit = st.selectbox("Rent amount type:", ["Custom Amount", "Thousands", "Lacs"])
            if rent_unit == "Thousands":
                initial_rent = st.number_input("Monthly rent (thousands):", min_value=0.0, value=50.0, step=5.0) * 1_000
            elif rent_unit == "Lacs":
                initial_rent = st.number_input("Monthly rent (lacs):", min_value=0.0, value=1.0, step=0.5) * 100_000
            else:
                initial_rent = st.number_input("Monthly rent (PKR):", min_value=0.0, value=50_000.0, step=5_000.0)

            years = int(st.number_input("Projection period (years):", min_value=1, max_value=30, value=5, step=1))
        else:
            rent_unit = st.selectbox("کرایہ کی رقم کی قسم:", ["کسٹم رقم", "ہزار", "لاکھ"])
            if rent_unit == "ہزار":
                initial_rent = st.number_input("ماہانہ کرایہ (ہزار):", min_value=0.0, value=50.0, step=5.0) * 1_000
            elif rent_unit == "لاکھ":
                initial_rent = st.number_input("ماہانہ کرایہ (لاکھ):", min_value=0.0, value=1.0, step=0.5) * 100_000
            else:
                initial_rent = st.number_input("ماہانہ کرایہ (روپے):", min_value=0.0, value=50_000.0, step=5_000.0)

            years = int(st.number_input("پروجیکشن مدت (سال):", min_value=1, max_value=30, value=5, step=1))

    with r2:
        if EN:
            annual_increase = st.number_input("Annual rent increase (%):", min_value=0.0, value=10.0, step=1.0)
            monthly_expense = st.number_input("Monthly expenses / maintenance (PKR):", min_value=0.0, value=0.0, step=1_000.0)
            vacancy_rate    = st.number_input("Annual vacancy rate (%):", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
            tax_rate        = st.number_input("Annual property / income tax rate (%):", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        else:
            annual_increase = st.number_input("سالانہ کرایہ اضافہ (%):", min_value=0.0, value=10.0, step=1.0)
            monthly_expense = st.number_input("ماہانہ اخراجات / دیکھ بھال (روپے):", min_value=0.0, value=0.0, step=1_000.0)
            vacancy_rate    = st.number_input("سالانہ خالی شرح (%):", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
            tax_rate        = st.number_input("سالانہ ٹیکس کی شرح (%):", min_value=0.0, max_value=100.0, value=0.0, step=0.5)

    # ── Rent Calculation ──────────────────────────────────────────────────────
    rent_rows = []
    current_rent      = initial_rent
    total_gross       = 0.0
    total_net         = 0.0
    total_vacancy_loss = 0.0
    total_expenses    = 0.0
    total_tax         = 0.0

    for yr in range(1, years + 1):
        gross           = current_rent * 12
        vac_loss        = gross * (vacancy_rate / 100)
        expenses        = monthly_expense * 12
        effective_gross = gross - vac_loss
        tax             = effective_gross * (tax_rate / 100)
        net             = effective_gross - expenses - tax

        total_gross        += gross
        total_net          += net
        total_vacancy_loss += vac_loss
        total_expenses     += expenses
        total_tax          += tax

        rent_rows.append({
            "Year"          if EN else "سال":          yr,
            "Monthly Rent"  if EN else "ماہانہ کرایہ": round(current_rent, 0),
            "Gross Annual"  if EN else "مجموعی سالانہ": round(gross, 0),
            "Vacancy Loss"  if EN else "خالی نقصان":   round(vac_loss, 0),
            "Expenses"      if EN else "اخراجات":       round(expenses, 0),
            "Tax"           if EN else "ٹیکس":          round(tax, 0),
            "Net Income"    if EN else "خالص آمدنی":    round(net, 0),
        })
        current_rent *= 1 + annual_increase / 100

    final_monthly_rent = initial_rent * ((1 + annual_increase / 100) ** years)

    # ── Rent Metrics ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'<p class="section-label">{"Projection Summary" if EN else "پروجیکشن کا خلاصہ"}</p>',
        unsafe_allow_html=True,
    )
    rm1, rm2, rm3, rm4 = st.columns(4)
    rm1.metric("Starting Rent"      if EN else "ابتدائی کرایہ",     fmt_pkr(initial_rent) + "/mo")
    rm2.metric("Final Year Rent"    if EN else "آخری سال کا کرایہ",  fmt_pkr(final_monthly_rent) + "/mo",
               delta=f"+{((final_monthly_rent / initial_rent) - 1)*100:.0f}% total" if initial_rent > 0 else None)
    rm3.metric("Total Gross Income" if EN else "کل مجموعی آمدنی",   fmt_pkr(total_gross))
    rm4.metric("Total Net Income"   if EN else "کل خالص آمدنی",      fmt_pkr(total_net))

    # ── Insight box ───────────────────────────────────────────────────────────
    if show_summary and initial_rent > 0:
        st.markdown("")
        doubles_in = round(70 / annual_increase, 1) if annual_increase > 0 else "∞"
        st.markdown(
            f'<div class="highlight-box-green">🏠 '
            + (f"At <b>{annual_increase:.0f}%/yr</b> increase, your rent doubles in ≈ <b>{doubles_in} years</b> (Rule of 70). "
               f"Over <b>{years} years</b>, cumulative losses from vacancy &amp; expenses total <b>{fmt_pkr(total_vacancy_loss + total_expenses + total_tax)}</b>."
               if EN else
               f"<b>{annual_increase:.0f}% سالانہ</b> اضافے سے آپ کا کرایہ ≈ <b>{doubles_in} سالوں</b> میں دوگنا ہوگا۔ "
               f"<b>{years} سالوں</b> میں خالی مدت اور اخراجات کا کل نقصان <b>{fmt_pkr(total_vacancy_loss + total_expenses + total_tax)}</b>۔")
            + "</div>",
            unsafe_allow_html=True,
        )

    # ── Rent Chart ────────────────────────────────────────────────────────────
    if show_chart and rent_rows:
        st.markdown("---")
        df_r = pd.DataFrame(rent_rows)
        yr_col    = "Year"         if EN else "سال"
        gross_col = "Gross Annual" if EN else "مجموعی سالانہ"
        net_col   = "Net Income"   if EN else "خالص آمدنی"
        rent_col  = "Monthly Rent" if EN else "ماہانہ کرایہ"

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df_r[yr_col], y=df_r[gross_col],
            name="Gross Annual Income" if EN else "مجموعی سالانہ آمدنی",
            marker_color="rgba(17,153,142,0.72)",
            hovertemplate="Year %{x}<br>Gross: PKR %{y:,.0f}<extra></extra>",
        ))
        fig2.add_trace(go.Bar(
            x=df_r[yr_col], y=df_r[net_col],
            name="Net Annual Income" if EN else "خالص سالانہ آمدنی",
            marker_color="rgba(56,239,125,0.75)",
            hovertemplate="Year %{x}<br>Net: PKR %{y:,.0f}<extra></extra>",
        ))
        fig2.add_trace(go.Scatter(
            x=df_r[yr_col], y=df_r[rent_col],
            name="Monthly Rent" if EN else "ماہانہ کرایہ",
            line=dict(color="#ff6b6b", width=2.5, dash="dot"),
            yaxis="y2",
            hovertemplate="Year %{x}<br>Rent/mo: PKR %{y:,.0f}<extra></extra>",
        ))
        fig2.update_layout(
            title=dict(text="🏠 Rent Growth Projection" if EN else "🏠 کرایہ ترقی پروجیکشن", x=0.02),
            xaxis=dict(title="Year" if EN else "سال", dtick=1),
            yaxis_title="Annual Income (PKR)"   if EN else "سالانہ آمدنی (روپے)",
            yaxis2=dict(title="Monthly Rent (PKR)" if EN else "ماہانہ کرایہ (روپے)", overlaying="y", side="right", showgrid=False),
            barmode="group",
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=420,
            margin=dict(t=60, b=40),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Year-by-Year Table + Export ───────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'<p class="section-label">{"Year-by-Year Breakdown" if EN else "سال بہ سال تفصیل"}</p>',
        unsafe_allow_html=True,
    )
    df_r_disp = pd.DataFrame(rent_rows).copy()
    for col in list(df_r_disp.columns)[1:]:
        df_r_disp[col] = df_r_disp[col].map(lambda x: f"PKR {x:,.0f}")
    st.dataframe(df_r_disp, use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Download Rent Projection CSV" if EN else "📥 کرایہ پروجیکشن CSV ڈاؤن لوڈ کریں",
        data=pd.DataFrame(rent_rows).to_csv(index=False),
        file_name="rent_projection.csv",
        mime="text/csv",
    )
    wa_rent = (
        f"🏠 Rent Projection (Smart Finance Calculator)\n{_SEP}\n"
        f"💰 Starting Rent: {fmt_pkr(initial_rent)}/mo\n"
        f"📈 Annual Increase: {annual_increase:.0f}%  |  Period: {years} years\n"
        f"🏦 Final Year Rent: {fmt_pkr(final_monthly_rent)}/mo\n"
        f"📊 Total Gross: {fmt_pkr(total_gross)}  |  Total Net: {fmt_pkr(total_net)}\n"
        f"{_SEP}\nCalculated with Smart Finance Calculator"
    ) if EN else (
        f"🏠 کرایہ پروجیکشن (سمارٹ فنانس کیلکولیٹر)\n{_SEP}\n"
        f"💰 ابتدائی کرایہ: {fmt_pkr(initial_rent)}/ماہ\n"
        f"📈 سالانہ اضافہ: {annual_increase:.0f}%  |  مدت: {years} سال\n"
        f"🏦 آخری سال کرایہ: {fmt_pkr(final_monthly_rent)}/ماہ\n"
        f"📊 کل مجموعی: {fmt_pkr(total_gross)}  |  کل خالص: {fmt_pkr(total_net)}\n"
        f"{_SEP}\nسمارٹ فنانس کیلکولیٹر"
    )
    wa_share(wa_rent, "Share on WhatsApp 📲" if EN else "واٹس ایپ پر شیئر کریں 📲")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — COMMITTEE / BC CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(
        f'<p class="section-label">{"Committee / BC Details" if EN else "کمیٹی / بی سی کی تفصیلات"}</p>',
        unsafe_allow_html=True,
    )
    if EN:
        st.caption("A committee (BC) is a rotating savings group. See your true return based on your draw position vs. investing the same monthly amount at a chosen rate.")
    else:
        st.caption("کمیٹی ایک گھومتی بچت گروپ ہے۔ اپنی قرعہ اندازی کی پوزیشن کی بنیاد پر اصل واپسی دیکھیں — اور یہ ماہانہ سرمایہ کاری سے موازنہ کریں۔")

    bc_col1, bc_col2 = st.columns(2)

    with bc_col1:
        if EN:
            bc_members = int(st.number_input("Number of members (N):", min_value=2, max_value=100, value=10, step=1, key="bc_members"))
            bc_unit = st.selectbox("Contribution amount type:", ["Custom Amount", "Thousands", "Lacs"], key="bc_unit")
            if bc_unit == "Thousands":
                bc_contribution = st.number_input("Monthly contribution per member (thousands):", min_value=0.0, value=10.0, step=1.0, key="bc_c") * 1_000
            elif bc_unit == "Lacs":
                bc_contribution = st.number_input("Monthly contribution per member (lacs):", min_value=0.0, value=0.5, step=0.1, key="bc_c") * 100_000
            else:
                bc_contribution = st.number_input("Monthly contribution per member (PKR):", min_value=0.0, value=10_000.0, step=1_000.0, key="bc_c")
        else:
            bc_members = int(st.number_input("اراکین کی تعداد (N):", min_value=2, max_value=100, value=10, step=1, key="bc_members"))
            bc_unit = st.selectbox("حصہ داری کی رقم کی قسم:", ["کسٹم رقم", "ہزار", "لاکھ"], key="bc_unit")
            if bc_unit == "ہزار":
                bc_contribution = st.number_input("ماہانہ حصہ داری فی رکن (ہزار):", min_value=0.0, value=10.0, step=1.0, key="bc_c") * 1_000
            elif bc_unit == "لاکھ":
                bc_contribution = st.number_input("ماہانہ حصہ داری فی رکن (لاکھ):", min_value=0.0, value=0.5, step=0.1, key="bc_c") * 100_000
            else:
                bc_contribution = st.number_input("ماہانہ حصہ داری فی رکن (روپے):", min_value=0.0, value=10_000.0, step=1_000.0, key="bc_c")

    with bc_col2:
        if EN:
            bc_draw_pos = int(st.number_input(
                f"Your draw position (1 = first, {bc_members} = last):",
                min_value=1, max_value=bc_members, value=min(5, bc_members), step=1, key="bc_draw",
            ))
            bc_comp_rate = st.number_input("Comparison investment rate (% monthly):", min_value=0.0, value=3.0, step=0.1, key="bc_rate") / 100
        else:
            bc_draw_pos = int(st.number_input(
                f"آپ کی قرعہ اندازی پوزیشن (1 = پہلی، {bc_members} = آخری):",
                min_value=1, max_value=bc_members, value=min(5, bc_members), step=1, key="bc_draw",
            ))
            bc_comp_rate = st.number_input("موازنہ سرمایہ کاری کی شرح (% ماہانہ):", min_value=0.0, value=3.0, step=0.1, key="bc_rate") / 100

    # ── BC Calculation ────────────────────────────────────────────────────────
    bc_N          = bc_members
    bc_c          = bc_contribution
    bc_D          = bc_draw_pos
    bc_total_pot  = bc_N * bc_c        # pot size = full monthly round
    bc_total_paid = bc_N * bc_c        # you pay c for all N months

    # Apparent annualised return: what you appear to get vs what you've paid *at draw month*
    paid_at_draw = bc_D * bc_c
    if paid_at_draw > 0 and bc_D > 0:
        bc_apparent_return = ((bc_total_pot / paid_at_draw) - 1) / (bc_D / 12) * 100
    else:
        bc_apparent_return = 0.0

    # Fair comparison: both scenarios pay bc_c per month for bc_N months.
    # Invest scenario: invest bc_c/month at bc_comp_rate → FV at month N
    if bc_comp_rate > 0:
        invest_fv = bc_c * ((1 + bc_comp_rate) ** bc_N - 1) / bc_comp_rate
    else:
        invest_fv = bc_c * bc_N

    # BC scenario: receive bc_total_pot at month D, invest it for (N-D) months
    bc_remaining = bc_N - bc_D
    bc_fv_final  = bc_total_pot * (1 + bc_comp_rate) ** bc_remaining
    bc_advantage = bc_fv_final - invest_fv   # positive → BC wins; negative → investing wins

    # Cash-flow table: net position each month
    bc_rows = []
    for m in range(1, bc_N + 1):
        cum_paid    = m * bc_c
        pot_this_m  = bc_total_pot if m == bc_D else 0.0
        # After draw month, pot received offsets cumulative paid
        net_pos     = (bc_total_pot if m >= bc_D else 0.0) - cum_paid
        bc_rows.append({
            "Month"           if EN else "مہینہ":         m,
            "Your Payment"    if EN else "آپ کی ادائیگی": round(bc_c, 0),
            "Cumulative Paid" if EN else "کل ادا کردہ":   round(cum_paid, 0),
            "Pot Received"    if EN else "پاٹ موصول":      round(pot_this_m, 0),
            "Net Position"    if EN else "خالص پوزیشن":   round(net_pos, 0),
        })

    # ── BC Metrics ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'<p class="section-label">{"Committee Summary" if EN else "کمیٹی کا خلاصہ"}</p>',
        unsafe_allow_html=True,
    )
    bcm1, bcm2, bcm3, bcm4 = st.columns(4)
    bcm1.metric("Total Pot (per round)" if EN else "کل پاٹ (فی دور)",     fmt_pkr(bc_total_pot))
    bcm2.metric("Total You Pay In"      if EN else "آپ کی کل ادائیگی",    fmt_pkr(bc_total_paid))

    adv_label = fmt_pkr(abs(bc_advantage))
    bcm3.metric(
        "BC vs Investing" if EN else "کمیٹی بمقابلہ سرمایہ کاری",
        (f"+{adv_label}" if bc_advantage >= 0 else f"-{adv_label}"),
        delta=("BC wins ✓" if bc_advantage >= 0 else "Invest wins ✓") if EN else
              ("کمیٹی بہتر ✓" if bc_advantage >= 0 else "سرمایہ کاری بہتر ✓"),
        delta_color="normal" if bc_advantage >= 0 else "inverse",
    )
    bcm4.metric(
        "Apparent Annual Return" if EN else "ظاہری سالانہ واپسی",
        f"{bc_apparent_return:.0f}%",
    )

    # ── Insight Box ───────────────────────────────────────────────────────────
    if show_summary:
        st.markdown("")
        if bc_advantage >= 0:
            box_class = "highlight-box-green"
            msg_en = (
                f"Drawing at position <b>{bc_D}</b> means you receive <b>{fmt_pkr(bc_total_pot)}</b> "
                f"in month {bc_D} and can invest it for {bc_remaining} more months. "
                f"At {bc_comp_rate*100:.1f}%/mo your pot grows to <b>{fmt_pkr(bc_fv_final)}</b> "
                f"vs investing {fmt_pkr(bc_c)}/mo which yields <b>{fmt_pkr(invest_fv)}</b>. "
                f"<b>Committee beats investing by {fmt_pkr(bc_advantage)}.</b>"
            )
            msg_ur = (
                f"پوزیشن <b>{bc_D}</b> پر قرعہ اندازی سے آپ کو مہینہ {bc_D} میں <b>{fmt_pkr(bc_total_pot)}</b> ملتے ہیں "
                f"جو {bc_remaining} مہینے مزید بڑھتے ہیں۔ "
                f"<b>کمیٹی، سرمایہ کاری سے {fmt_pkr(bc_advantage)} بہتر ہے۔</b>"
            )
        else:
            box_class = "highlight-box-orange"
            deficit = abs(bc_advantage)
            msg_en = (
                f"Drawing at position <b>{bc_D}</b> (month {bc_D} of {bc_N}) leaves only "
                f"{bc_remaining} months for your pot to compound. "
                f"At {bc_comp_rate*100:.1f}%/mo, pot reaches <b>{fmt_pkr(bc_fv_final)}</b> "
                f"vs investing {fmt_pkr(bc_c)}/mo giving <b>{fmt_pkr(invest_fv)}</b>. "
                f"<b>Investing beats this BC position by {fmt_pkr(deficit)}.</b>"
            )
            msg_ur = (
                f"پوزیشن <b>{bc_D}</b> پر صرف {bc_remaining} مہینے بچتے ہیں۔ "
                f"پاٹ بڑھ کر <b>{fmt_pkr(bc_fv_final)}</b> ہوگا — لیکن ماہانہ سرمایہ کاری <b>{fmt_pkr(invest_fv)}</b> دیتی ہے۔ "
                f"<b>سرمایہ کاری {fmt_pkr(deficit)} بہتر ہے۔</b>"
            )

        st.markdown(
            f'<div class="{box_class}">🤝 ' + (msg_en if EN else msg_ur) + "</div>",
            unsafe_allow_html=True,
        )

    # ── BC Chart ──────────────────────────────────────────────────────────────
    if show_chart and bc_rows:
        st.markdown("---")
        df_bc       = pd.DataFrame(bc_rows)
        net_col_bc  = "Net Position"    if EN else "خالص پوزیشن"
        cum_col_bc  = "Cumulative Paid" if EN else "کل ادا کردہ"
        mo_col_bc   = "Month"           if EN else "مہینہ"

        bar_colors = [
            "rgba(239,68,68,0.75)" if v < 0 else "rgba(34,197,94,0.75)"
            for v in df_bc[net_col_bc]
        ]

        fig_bc = go.Figure()
        fig_bc.add_trace(go.Bar(
            x=df_bc[mo_col_bc], y=df_bc[net_col_bc],
            name="Net Position"    if EN else "خالص پوزیشن",
            marker_color=bar_colors,
            hovertemplate="Month %{x}<br>Net: PKR %{y:,.0f}<extra></extra>",
        ))
        fig_bc.add_trace(go.Scatter(
            x=df_bc[mo_col_bc], y=df_bc[cum_col_bc],
            name="Cumulative Paid" if EN else "کل ادا کردہ",
            line=dict(color="#f7971e", width=2.5, dash="dot"),
            yaxis="y2",
            hovertemplate="Month %{x}<br>Paid: PKR %{y:,.0f}<extra></extra>",
        ))
        # Mark draw month with a vertical line
        fig_bc.add_shape(
            type="line", x0=bc_D, x1=bc_D, y0=0, y1=1,
            yref="paper", line=dict(color="#764ba2", width=2, dash="dash"),
        )
        fig_bc.add_annotation(
            x=bc_D, y=1, yref="paper", yanchor="bottom",
            text=f"🎯 Draw month {bc_D}" if EN else f"🎯 قرعہ اندازی مہینہ {bc_D}",
            showarrow=False, font=dict(color="#764ba2", size=11),
        )
        fig_bc.update_layout(
            title=dict(text="🤝 Committee Cash Flow — Net Position Per Month" if EN else "🤝 کمیٹی کیش فلو — ماہانہ خالص پوزیشن", x=0.02),
            xaxis=dict(title="Month" if EN else "مہینہ", dtick=max(1, bc_N // 10)),
            yaxis=dict(title="Net Position (PKR)" if EN else "خالص پوزیشن (روپے)", zeroline=True, zerolinecolor="#ccc", zerolinewidth=1.5),
            yaxis2=dict(title="Cumulative Paid (PKR)" if EN else "کل ادا کردہ (روپے)", overlaying="y", side="right", showgrid=False),
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=420,
            margin=dict(t=70, b=40),
        )
        st.plotly_chart(fig_bc, use_container_width=True)

    # ── BC Table + Export ─────────────────────────────────────────────────────
    if show_breakdown and bc_rows:
        st.markdown("---")
        st.markdown(
            f'<p class="section-label">{"Month-by-Month Cash Flow" if EN else "مہینہ بہ مہینہ کیش فلو"}</p>',
            unsafe_allow_html=True,
        )
        df_bc_disp = pd.DataFrame(bc_rows).copy()
        for col in list(df_bc_disp.columns)[1:]:
            df_bc_disp[col] = df_bc_disp[col].map(lambda x: f"PKR {x:,.0f}")
        st.dataframe(df_bc_disp, use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Download Committee CSV" if EN else "📥 کمیٹی CSV ڈاؤن لوڈ کریں",
        data=pd.DataFrame(bc_rows).to_csv(index=False),
        file_name="committee_cashflow.csv",
        mime="text/csv",
        key="bc_dl",
    )
    bc_verdict = ("BC wins" if bc_advantage >= 0 else "Investing wins") if EN else ("کمیٹی بہتر" if bc_advantage >= 0 else "سرمایہ کاری بہتر")
    wa_bc = (
        f"🤝 Committee (BC) Result (Smart Finance Calculator)\n{_SEP}\n"
        f"👥 Members: {bc_N}  |  Monthly Contribution: {fmt_pkr(bc_c)}\n"
        f"🎯 Your Draw Position: {bc_D} of {bc_N}\n"
        f"💰 Total Pot: {fmt_pkr(bc_total_pot)}\n"
        f"📊 BC vs Investing at {bc_comp_rate*100:.1f}%/mo: "
        f"{'+'  if bc_advantage >= 0 else ''}{fmt_pkr(bc_advantage)} ({bc_verdict})\n"
        f"{_SEP}\nCalculated with Smart Finance Calculator"
    ) if EN else (
        f"🤝 کمیٹی نتیجہ (سمارٹ فنانس کیلکولیٹر)\n{_SEP}\n"
        f"👥 اراکین: {bc_N}  |  ماہانہ حصہ: {fmt_pkr(bc_c)}\n"
        f"🎯 آپ کی پوزیشن: {bc_D} از {bc_N}\n"
        f"💰 کل پاٹ: {fmt_pkr(bc_total_pot)}\n"
        f"📊 کمیٹی بمقابلہ سرمایہ کاری: {fmt_pkr(bc_advantage)} ({bc_verdict})\n"
        f"{_SEP}\nسمارٹ فنانس کیلکولیٹر"
    )
    wa_share(wa_bc, "Share on WhatsApp 📲" if EN else "واٹس ایپ پر شیئر کریں 📲")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — LOAN / EMI CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(
        f'<p class="section-label">{"Loan / EMI Details" if EN else "قرض / قسط کی تفصیلات"}</p>',
        unsafe_allow_html=True,
    )
    if EN:
        st.caption("Calculate your monthly instalment, total interest, and full amortisation schedule. Add an extra monthly payment to see early payoff savings.")
    else:
        st.caption("اپنی ماہانہ قسط، کل سود اور مکمل ادائیگی کا شیڈول دیکھیں۔ جلد ادائیگی کے اثرات جاننے کے لیے اضافی ماہانہ رقم شامل کریں۔")

    loan_c1, loan_c2 = st.columns(2)

    with loan_c1:
        if EN:
            loan_type = st.selectbox("Loan amount type:", ["Lacs", "Millions", "Custom Amount"], key="loan_type")
            if loan_type == "Millions":
                loan_principal = st.number_input("Loan amount (millions):", min_value=0.0, value=1.0, step=0.5, key="loan_p") * 1_000_000
            elif loan_type == "Lacs":
                loan_principal = st.number_input("Loan amount (lacs):", min_value=0.0, value=50.0, step=5.0, key="loan_p") * 100_000
            else:
                loan_principal = st.number_input("Loan amount (PKR):", min_value=0.0, value=500_000.0, step=50_000.0, key="loan_p")

            loan_rate_annual = st.number_input("Annual interest rate (%):", min_value=0.0, value=18.0, step=0.5, key="loan_rate")
            loan_years       = int(st.number_input("Loan tenure (years):", min_value=1, max_value=30, value=5, step=1, key="loan_years"))
        else:
            loan_type = st.selectbox("قرض کی رقم کی قسم:", ["لاکھ", "ملین", "کسٹم رقم"], key="loan_type")
            if loan_type == "ملین":
                loan_principal = st.number_input("قرض کی رقم (ملین):", min_value=0.0, value=1.0, step=0.5, key="loan_p") * 1_000_000
            elif loan_type == "لاکھ":
                loan_principal = st.number_input("قرض کی رقم (لاکھ):", min_value=0.0, value=50.0, step=5.0, key="loan_p") * 100_000
            else:
                loan_principal = st.number_input("قرض کی رقم (روپے):", min_value=0.0, value=500_000.0, step=50_000.0, key="loan_p")

            loan_rate_annual = st.number_input("سالانہ سود کی شرح (%):", min_value=0.0, value=18.0, step=0.5, key="loan_rate")
            loan_years       = int(st.number_input("قرض کی مدت (سال):", min_value=1, max_value=30, value=5, step=1, key="loan_years"))

    with loan_c2:
        if EN:
            extra_payment = st.number_input("Extra monthly payment (PKR, optional):", min_value=0.0, value=0.0, step=1_000.0, key="loan_extra")
            st.caption("Adding extra principal payments each month reduces your tenure and total interest paid.")
        else:
            extra_payment = st.number_input("اضافی ماہانہ ادائیگی (روپے، اختیاری):", min_value=0.0, value=0.0, step=1_000.0, key="loan_extra")
            st.caption("ماہانہ اضافی اصل رقم ادا کرنے سے مدت اور کل سود کم ہوتا ہے۔")

    # ── EMI Calculation ───────────────────────────────────────────────────────
    loan_n         = loan_years * 12
    loan_r         = loan_rate_annual / 12 / 100   # monthly rate

    if loan_r > 0 and loan_principal > 0:
        emi = loan_principal * loan_r * (1 + loan_r) ** loan_n / ((1 + loan_r) ** loan_n - 1)
    elif loan_principal > 0:
        emi = loan_principal / loan_n
    else:
        emi = 0.0

    total_paid_std    = emi * loan_n
    total_interest_std = total_paid_std - loan_principal
    interest_pct      = (total_interest_std / loan_principal * 100) if loan_principal > 0 else 0.0

    # Amortisation with optional extra payment
    balance              = loan_principal
    emi_rows             = []
    total_interest_actual = 0.0
    actual_months        = loan_n

    for m in range(1, loan_n + 1):
        interest_pmt   = balance * loan_r
        principal_pmt  = emi - interest_pmt
        extra_this_mo  = min(extra_payment, max(0.0, balance - principal_pmt))
        total_monthly  = emi + extra_this_mo
        principal_pmt += extra_this_mo
        balance       -= principal_pmt

        if balance <= 0:
            # Final payment adjustment
            balance       = 0.0
            total_monthly = interest_pmt + (principal_pmt + balance)  # balance already 0
            actual_months = m

        total_interest_actual += interest_pmt
        emi_rows.append({
            "Month"     if EN else "مہینہ":     m,
            "EMI"       if EN else "قسط":        round(total_monthly, 0),
            "Principal" if EN else "اصل رقم":   round(principal_pmt, 0),
            "Interest"  if EN else "سود":        round(interest_pmt, 0),
            "Balance"   if EN else "باقی رقم":   round(max(balance, 0.0), 0),
        })

        if balance <= 0:
            break

    months_saved   = loan_n - actual_months
    interest_saved = max(0.0, total_interest_std - total_interest_actual)
    total_paid_actual = sum(r["EMI" if EN else "قسط"] for r in emi_rows)

    # ── EMI Metrics ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'<p class="section-label">{"Loan Summary" if EN else "قرض کا خلاصہ"}</p>',
        unsafe_allow_html=True,
    )
    em1, em2, em3, em4 = st.columns(4)
    em1.metric("Monthly EMI"          if EN else "ماہانہ قسط",         fmt_pkr(emi))
    em2.metric("Total Amount Paid"    if EN else "کل ادا کردہ رقم",    fmt_pkr(total_paid_actual))
    em3.metric("Total Interest"       if EN else "کل سود",              fmt_pkr(total_interest_actual))
    em4.metric("Interest % of Principal" if EN else "اصل کا سود %",    f"{interest_pct:.1f}%")

    # Extra-payment savings cards
    if extra_payment > 0 and months_saved > 0:
        st.markdown("")
        es1, es2 = st.columns(2)
        es1.metric(
            "Months Saved"   if EN else "بچائے گئے مہینے",
            f"{months_saved} mo  ({months_saved/12:.1f} yrs)" if EN else f"{months_saved} مہینے ({months_saved/12:.1f} سال)",
            delta=f"Paid off in {actual_months} months" if EN else f"{actual_months} مہینوں میں ادائیگی",
        )
        es2.metric(
            "Interest Saved" if EN else "بچایا گیا سود",
            fmt_pkr(interest_saved),
            delta=f"vs standard {loan_n}-mo schedule" if EN else f"معیاری {loan_n} مہینوں سے موازنہ",
        )

    # ── Insight Box ───────────────────────────────────────────────────────────
    if show_summary and loan_principal > 0:
        st.markdown("")
        per_100 = (total_interest_actual / loan_principal * 100) if loan_principal > 0 else 0
        if extra_payment > 0 and months_saved > 0:
            box_en = (
                f"For every <b>PKR 100</b> borrowed you pay <b>PKR {per_100:.0f}</b> in interest over {actual_months} months. "
                f"Your extra <b>{fmt_pkr(extra_payment)}/mo</b> saves <b>{fmt_pkr(interest_saved)}</b> in interest "
                f"and pays off the loan <b>{months_saved} months early</b>."
            )
            box_ur = (
                f"قرض لی گئی ہر <b>PKR 100</b> پر آپ <b>PKR {per_100:.0f}</b> سود ادا کرتے ہیں۔ "
                f"اضافی <b>{fmt_pkr(extra_payment)}/ماہ</b> سے <b>{fmt_pkr(interest_saved)}</b> سود بچتا ہے "
                f"اور قرض <b>{months_saved} مہینے جلدی</b> ختم ہوتا ہے۔"
            )
        else:
            box_en = (
                f"For every <b>PKR 100</b> borrowed you pay <b>PKR {per_100:.0f}</b> in interest "
                f"over <b>{loan_n} months</b>. "
                f"Total cost of this loan: <b>{fmt_pkr(total_paid_actual)}</b>. "
                f"Add an extra monthly payment above to see how fast you can pay it off."
            )
            box_ur = (
                f"قرض لی گئی ہر <b>PKR 100</b> پر آپ <b>PKR {per_100:.0f}</b> سود ادا کرتے ہیں — "
                f"<b>{loan_n} مہینوں</b> میں کل <b>{fmt_pkr(total_paid_actual)}</b>۔ "
                f"جلد ادائیگی کے اثرات دیکھنے کے لیے اضافی ماہانہ رقم درج کریں۔"
            )
        st.markdown(
            '<div class="highlight-box-red">🏦 ' + (box_en if EN else box_ur) + "</div>",
            unsafe_allow_html=True,
        )

    # ── EMI Chart ─────────────────────────────────────────────────────────────
    if show_chart and emi_rows:
        st.markdown("---")
        df_emi     = pd.DataFrame(emi_rows)
        mo_col_e   = "Month"     if EN else "مہینہ"
        prin_col_e = "Principal" if EN else "اصل رقم"
        int_col_e  = "Interest"  if EN else "سود"
        bal_col_e  = "Balance"   if EN else "باقی رقم"

        fig_emi = go.Figure()
        fig_emi.add_trace(go.Bar(
            x=df_emi[mo_col_e], y=df_emi[prin_col_e],
            name="Principal" if EN else "اصل رقم",
            marker_color="rgba(102,126,234,0.75)",
            hovertemplate="Month %{x}<br>Principal: PKR %{y:,.0f}<extra></extra>",
        ))
        fig_emi.add_trace(go.Bar(
            x=df_emi[mo_col_e], y=df_emi[int_col_e],
            name="Interest" if EN else "سود",
            marker_color="rgba(203,45,62,0.65)",
            hovertemplate="Month %{x}<br>Interest: PKR %{y:,.0f}<extra></extra>",
        ))
        fig_emi.add_trace(go.Scatter(
            x=df_emi[mo_col_e], y=df_emi[bal_col_e],
            name="Remaining Balance" if EN else "باقی رقم",
            line=dict(color="#ffd200", width=2.5),
            yaxis="y2",
            hovertemplate="Month %{x}<br>Balance: PKR %{y:,.0f}<extra></extra>",
        ))
        fig_emi.update_layout(
            title=dict(text="🏦 Loan Amortisation — Principal vs Interest" if EN else "🏦 قرض کی ادائیگی — اصل بمقابلہ سود", x=0.02),
            xaxis_title="Month" if EN else "مہینہ",
            yaxis_title="Monthly Breakdown (PKR)" if EN else "ماہانہ تفصیل (روپے)",
            yaxis2=dict(title="Remaining Balance (PKR)" if EN else "باقی رقم (روپے)", overlaying="y", side="right", showgrid=False),
            barmode="stack",
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=420,
            margin=dict(t=60, b=40),
        )
        st.plotly_chart(fig_emi, use_container_width=True)

    # ── Amortisation Table + Export ───────────────────────────────────────────
    if show_breakdown and emi_rows:
        st.markdown("---")
        st.markdown(
            f'<p class="section-label">{"Full Amortisation Schedule" if EN else "مکمل ادائیگی کا شیڈول"}</p>',
            unsafe_allow_html=True,
        )
        df_emi_disp = pd.DataFrame(emi_rows).copy()
        for col in list(df_emi_disp.columns)[1:]:
            df_emi_disp[col] = df_emi_disp[col].map(lambda x: f"PKR {x:,.0f}")
        st.dataframe(df_emi_disp, use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Download Amortisation CSV" if EN else "📥 ادائیگی شیڈول CSV ڈاؤن لوڈ کریں",
        data=pd.DataFrame(emi_rows).to_csv(index=False),
        file_name="loan_amortisation.csv",
        mime="text/csv",
        key="emi_dl",
    )
    extra_line = (f"\n💡 Extra payment {fmt_pkr(extra_payment)}/mo saves {fmt_pkr(interest_saved)} — paid off {months_saved} months early"
                  if extra_payment > 0 and months_saved > 0 else "")
    wa_emi = (
        f"🏦 Loan / EMI Summary (Smart Finance Calculator)\n{_SEP}\n"
        f"💰 Loan Amount: {fmt_pkr(loan_principal)}\n"
        f"📅 Monthly EMI: {fmt_pkr(emi)}\n"
        f"⏱ Tenure: {actual_months} months  |  Rate: {loan_rate_annual:.1f}%/yr\n"
        f"📈 Total Interest: {fmt_pkr(total_interest_actual)}"
        + extra_line
        + f"\n{_SEP}\nCalculated with Smart Finance Calculator"
    ) if EN else (
        f"🏦 قرض / قسط خلاصہ (سمارٹ فنانس کیلکولیٹر)\n{_SEP}\n"
        f"💰 قرض: {fmt_pkr(loan_principal)}\n"
        f"📅 ماہانہ قسط: {fmt_pkr(emi)}\n"
        f"⏱ مدت: {actual_months} مہینے  |  شرح: {loan_rate_annual:.1f}%/سال\n"
        f"📈 کل سود: {fmt_pkr(total_interest_actual)}"
        + extra_line
        + f"\n{_SEP}\nسمارٹ فنانس کیلکولیٹر"
    )
    wa_share(wa_emi, "Share on WhatsApp 📲" if EN else "واٹس ایپ پر شیئر کریں 📲")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div class="footer">Smart Finance Calculator v3.0 — '
    + ("Built for investors &amp; property owners in Pakistan"
       if EN else "پاکستان میں سرمایہ کاروں اور جائیداد کے مالکان کے لیے")
    + "</div>",
    unsafe_allow_html=True,
)
