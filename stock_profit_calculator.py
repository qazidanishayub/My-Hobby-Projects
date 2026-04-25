import os
from dotenv import load_dotenv
load_dotenv()
import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import google.generativeai as genai
from datetime import datetime

st.set_page_config(page_title="AI Wealth Simulator", layout="wide", page_icon="📈")

# --- Custom CSS for Premium Look ---
st.markdown("""
<style>
/* Glassmorphism and premium styles */
.reportview-container .main .block-container{
    padding-top: 2rem;
}
.metric-card {
    background: #1E1E2E;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    text-align: center;
    border: 1px solid #2d2d3f;
    margin-bottom: 20px;
}
.metric-title {
    font-size: 0.9rem;
    color: #A0A0B0;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 5px;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #4CAF50;
}
.metric-value.neutral {
    color: #E0E0E0;
}
/* Ensure text in light mode is legible if background isn't purely dark */
@media (prefers-color-scheme: light) {
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .metric-title {
        color: #6c757d;
    }
    .metric-value {
        color: #2e7d32;
    }
    .metric-value.neutral {
        color: #212529;
    }
}
</style>
""", unsafe_allow_html=True)

st.title("📈 AI-Driven Wealth Simulator & Pitch Generator")
st.markdown("A professional financial projection tool powered by real market data and Generative AI.")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. RAG / Market Data Integration
    st.subheader("Market Context (Optional)")
    st.caption("Fetch historical 5-year CAGR to set expected return.")
    
    TICKER_OPTIONS = {
        "S&P 500 (US Market)": "SPY",
        "KSE-100 (Pakistan Market)": "^KSE",
        "NASDAQ 100 (Tech Stocks)": "QQQ",
        "Bitcoin (Crypto)": "BTC-USD",
        "Gold (Commodity)": "GC=F",
        "Custom Symbol": "CUSTOM"
    }
    selected_market = st.selectbox("Select Market Benchmark", list(TICKER_OPTIONS.keys()))
    
    if TICKER_OPTIONS[selected_market] == "CUSTOM":
        ticker = st.text_input("Enter Custom Ticker", placeholder="e.g. AAPL")
    else:
        ticker = TICKER_OPTIONS[selected_market]
        
    # Default value
    cagr_pct = 19.85
    
    if ticker:
        with st.spinner("Fetching real-time data..."):
            try:
                hist = yf.Ticker(ticker).history(period="5y")
                if len(hist) > 1:
                    start_price = hist['Close'].iloc[0]
                    end_price = hist['Close'].iloc[-1]
                    start_date = hist.index[0]
                    end_date = hist.index[-1]
                    
                    # Calculate exact years between first and last data point
                    years_data = (end_date - start_date).days / 365.25
                    
                    if years_data > 0:
                        cagr = ((end_price / start_price) ** (1 / years_data)) - 1
                        cagr_pct = round(cagr * 100, 2)
                    else:
                        cagr_pct = 15.0  # fallback
                    
                    # Real-time stats
                    current_price = hist['Close'].iloc[-1]
                    if len(hist) > 1:
                        prev_price = hist['Close'].iloc[-2]
                        day_change_pct = ((current_price - prev_price) / prev_price) * 100
                    else:
                        day_change_pct = 0.0
                    
                    st.metric(label=f"{ticker} Current Price", value=f"{current_price:,.2f}", delta=f"{day_change_pct:.2f}% (Daily)")
                    st.success(f"5-Year CAGR for {ticker}: **{cagr_pct}%**")
                else:
                    st.warning("Could not fetch data. Using default 19.85%.")
            except Exception as e:
                st.warning("Error fetching ticker. Using default 19.85%.")

    st.divider()

    # Core inputs
    base_monthly_contribution = st.number_input("Base Monthly Contribution", 0, 100_000_000, 100_000, step=10_000, help="The amount you plan to invest every single month.")
    years = st.slider("Duration (years)", 1, 40, 10, help="How many years you will keep investing.")
    annuity_due = st.checkbox("Contribute at month start (Annuity Due)", value=True, help="Check this if you invest at the beginning of the month. Uncheck if at the end.")

    nominal_annual_return_pct = st.number_input("Expected Nominal Annual Return (%)", -100.0, 1000.0, float(cagr_pct), step=0.5, help="The average yearly growth rate you expect from your investments, before inflation.")
    annual_devaluation_pct = st.number_input("Expected Inflation/Devaluation (%)", 0.0, 100.0, 0.0, step=0.5, help="How much the purchasing power of your money decreases each year (e.g., inflation).")
    annual_fee_tax_drag_pct = st.number_input("Annual Fees + Tax Drag (%)", 0.0, 20.0, 0.0, step=0.1, help="Any yearly fees, taxes, or management costs that reduce your returns.")

    step_up_pct = st.number_input("Annual Step-up in Contribution (%)", 0.0, 100.0, 0.0, step=1.0, help="By what percentage you will increase your monthly contribution each year (e.g., 10% raise).")
    lump_sum = st.number_input("Initial Lump-Sum", 0, 1_000_000_000, 0, step=50_000, help="A one-time bulk investment made at the very beginning.")

    # Anchor month
    months_list = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    anchor_month = st.selectbox("Anchor Month (for step-ups)", options=months_list, index=0, help="The month of the year when your 'Annual Step-up' takes effect.")

    st.divider()
    st.subheader("🤖 AI Settings")
    st.caption("Our internal Magical AI Engine is initialized.")

months = years * 12
anchor_index = months_list.index(anchor_month)

# --- Monthly Customization UI ---
with st.expander("🗓️ Advanced Monthly Customization"):
    default_pattern = pd.DataFrame({
        "Month": months_list,
        "Contribution": [base_monthly_contribution]*12,
        "Extra Lump": [0]*12
    })
    pattern_df = st.data_editor(default_pattern, use_container_width=True, hide_index=True)
    use_monthly_customization = st.checkbox("Enable custom monthly pattern", value=False)

# --- Calculations ---
def eff_monthly_rate_from_annual(annual_pct):
    return (1 + annual_pct/100.0) ** (1/12) - 1

gross_monthly = eff_monthly_rate_from_annual(nominal_annual_return_pct)
drag_monthly = eff_monthly_rate_from_annual(annual_fee_tax_drag_pct)
net_nominal_monthly = (1 + gross_monthly) / (1 + drag_monthly) - 1
deval_monthly = eff_monthly_rate_from_annual(annual_devaluation_pct)

dates = pd.date_range(datetime.today().strftime('%Y-%m-01'), periods=months, freq="MS")
df = pd.DataFrame({"date": dates})
df["month_index"] = np.arange(len(df))
df["month_num_in_year"] = df["date"].dt.month - 1

if use_monthly_customization:
    contrib_map = dict(zip(pattern_df["Month"], pattern_df["Contribution"]))
    extra_map = dict(zip(pattern_df["Month"], pattern_df["Extra Lump"]))
    df["contribution"] = df["month_num_in_year"].map(lambda i: contrib_map[months_list[i]])
    df["extra_lump"] = df["month_num_in_year"].map(lambda i: extra_map[months_list[i]])
else:
    df["contribution"] = base_monthly_contribution
    df["extra_lump"] = 0.0

if step_up_pct > 0:
    is_anchor = (df["month_num_in_year"] == anchor_index)
    step_factor = np.ones(len(df))
    cum = 1.0
    for i in range(len(df)):
        if is_anchor.iloc[i] and i != 0:
            cum *= (1 + step_up_pct/100.0)
        step_factor[i] = cum
    df["contribution"] = df["contribution"] * step_factor

def simulate_series(contribution_series, extra_series, lump_sum=0, monthly_rate=0.01, annuity_due=True):
    balance = 0.0
    balances = []
    for i, (c, x) in enumerate(zip(contribution_series, extra_series)):
        if i == 0 and lump_sum > 0:
            balance += lump_sum
        if annuity_due:
            balance += c + x
            balance *= (1 + monthly_rate)
        else:
            balance *= (1 + monthly_rate)
            balance += c + x
        balances.append(balance)
    return np.array(balances)

df["nominal_balance"] = simulate_series(df["contribution"].values, df["extra_lump"].values, lump_sum, net_nominal_monthly, annuity_due)
discount_factors = (1 + deval_monthly) ** (df["month_index"] + 1)
df["real_balance"] = df["nominal_balance"] / discount_factors

# --- Summary Metrics ---
final_nominal = df["nominal_balance"].iloc[-1]
final_real = df["real_balance"].iloc[-1]
total_contrib = df["contribution"].sum() + df["extra_lump"].sum() + lump_sum
gain_nominal = final_nominal - total_contrib
gain_real = final_real - (total_contrib / ((1 + deval_monthly) ** months))

def format_currency(val):
    return f"{val:,.0f}"

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f'<div class="metric-card"><div class="metric-title">Final Nominal Value</div><div class="metric-value">{format_currency(final_nominal)}</div></div>', unsafe_allow_html=True)
col2.markdown(f'<div class="metric-card"><div class="metric-title">Final Real Value</div><div class="metric-value">{format_currency(final_real)}</div></div>', unsafe_allow_html=True)
col3.markdown(f'<div class="metric-card"><div class="metric-title">Total Contribution</div><div class="metric-value neutral">{format_currency(total_contrib)}</div></div>', unsafe_allow_html=True)
col4.markdown(f'<div class="metric-card"><div class="metric-title">Nominal Gain</div><div class="metric-value neutral">{format_currency(gain_nominal)}</div></div>', unsafe_allow_html=True)

# --- Visualization ---
st.subheader("📊 Growth Projection")
fig = go.Figure()

# Create a clean, modern chart
fig.add_trace(go.Scatter(
    x=df['date'], y=df['nominal_balance'], 
    mode='lines', name='Nominal Balance', 
    line=dict(color='#4CAF50', width=3), 
    fill='tozeroy', fillcolor='rgba(76, 175, 80, 0.1)'
))

fig.add_trace(go.Scatter(
    x=df['date'], y=df['real_balance'], 
    mode='lines', name='Real (Inflation-Adj) Balance', 
    line=dict(color='#03A9F4', width=3, dash='dot')
))

fig.add_trace(go.Scatter(
    x=df['date'], y=df['contribution'].cumsum() + df['extra_lump'].cumsum() + lump_sum, 
    mode='lines', name='Total Contributions', 
    line=dict(color='#9E9E9E', width=2)
))

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
    hovermode='x unified',
    margin=dict(l=0, r=0, t=20, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# --- AI Pitch Generator ---
st.divider()
st.subheader("✨ Magical AI Pitch Generator")
st.markdown("Use our proprietary AI to generate a tailored, professional investment pitch based on the current projections.")

if st.button("Generate Professional Pitch with AI", type="primary"):
    api_key = None
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        try:
            if "gemini_api_key" in st.secrets:
                api_key = st.secrets["gemini_api_key"]
            elif "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
                api_key = st.secrets["gemini"]["api_key"]
        except Exception:
            pass
    if not api_key:
        st.error("⚠️ AI Engine Configuration Missing: Please set 'GEMINI_API_KEY' in your environment variables or Streamlit secrets (.streamlit/secrets.toml).")
    else:
        with st.spinner("Our Magical AI is analyzing data and generating your pitch..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-flash-latest')
                
                context = f"""
                You are a highly professional, expert financial advisor creating a pitch for a high-net-worth client.
                The client is considering an investment plan with the following metrics:
                - Duration: {years} years
                - Base Monthly Contribution: {base_monthly_contribution}
                - Expected Annual Return: {nominal_annual_return_pct}%
                - Expected Inflation/Devaluation: {annual_devaluation_pct}%
                - Total Contributed over {years} years: {format_currency(total_contrib)}
                - Final Projected Value (Nominal): {format_currency(final_nominal)}
                - Final Projected Value (Purchasing Power Adjusted): {format_currency(final_real)}
                
                Write a concise, compelling 3-paragraph executive summary to sell this investment strategy.
                - Paragraph 1: Highlight the sheer growth and the magic of compounding based on these numbers.
                - Paragraph 2: Address the inflation/devaluation factor gracefully, showing that even after adjusting for a {annual_devaluation_pct}% drop in purchasing power, the real value still makes it a sound investment.
                - Paragraph 3: A strong call to action.
                Use professional formatting (bolding, maybe a bullet or two). Do not use placeholders. Tone should be premium, authoritative, and inspiring.
                """
                
                response = model.generate_content(context)
                
                st.info("### 📝 Your Custom Pitch")
                st.markdown(response.text)
                
                st.download_button(
                    label="📥 Download Pitch as TXT",
                    data=response.text,
                    file_name="investment_pitch.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Error generating AI pitch: {str(e)}")

# Detailed Table Expander
with st.expander("🔍 View Detailed Monthly Ledger"):
    st.dataframe(
        df[["date", "contribution", "extra_lump", "nominal_balance", "real_balance"]].style.format({
            "contribution": "{:,.0f}",
            "extra_lump": "{:,.0f}",
            "nominal_balance": "{:,.0f}",
            "real_balance": "{:,.0f}"
        }),
        use_container_width=True
    )
