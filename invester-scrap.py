import streamlit as st
from datetime import datetime, timedelta

# Title and Introduction
st.title("Scrap-Invest-Cross-Profit Calculator")
st.subheader("Calculate your monthly compounded profit over a specified period!")

# User Input
investment = st.number_input("Enter your total investment (in your currency):", min_value=0.0, value=1000.0)
profit_rate = st.number_input("Enter the monthly profit rate (default is 3%):", min_value=0.0, value=0.03) / 100

# Optional time-based inputs
st.write("**Optional Time Specifications**")
start_date = st.date_input("Investment start date (optional)", value=datetime.today())
end_date = st.date_input("Investment end date (optional)", value=start_date + timedelta(days=30))

# Calculate duration in months if both dates are provided, else ask for the number of months
if end_date > start_date:
    num_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
else:
    num_months = st.number_input("Enter the number of months for calculation:", min_value=1, value=12)

# Options for viewing details
show_monthly_details = st.checkbox("Show profit division for each month")

# Calculate profit
total_amount = investment
profits = []

for month in range(1, num_months + 1):
    monthly_profit = total_amount * profit_rate
    total_amount += monthly_profit
    profits.append((month, monthly_profit, total_amount))

# Display results
st.write("## Results")
if show_monthly_details:
    st.write("### Monthly Profit Division")
    for month, monthly_profit, current_total in profits:
        st.write(f"Month {month}: Profit = {monthly_profit:.2f}, Total Amount = {current_total:.2f}")
else:
    total_profit = total_amount - investment
    st.write(f"Total Profit after {num_months} months: {total_profit:.2f}")
    st.write(f"Total Amount after {num_months} months: {total_amount:.2f}")
