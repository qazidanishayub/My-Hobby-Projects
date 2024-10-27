import streamlit as st
from datetime import datetime, timedelta

# Application title
st.title("Scrap-Invest-Cross-Profit Calculator")

# User inputs
st.write("## Investment Details")
total_investment = st.number_input("Enter your total investment:", min_value=0.0, value=1000.0)
use_date = st.checkbox("Do you want to specify investment period with dates?")

# Date input options
if use_date:
    start_date = st.date_input("Start Date", value=datetime.today())
    end_date = st.date_input("End Date", value=datetime.today() + timedelta(days=30))
    if end_date < start_date:
        st.error("End date must be after the start date.")
    num_months = ((end_date - start_date).days // 30)
else:
    num_months = st.number_input("Number of months:", min_value=1, value=12)

# Profit rate
profit_rate = 0.03

# Show detailed monthly breakdown option
show_details = st.checkbox("Show detailed monthly profit breakdown")

# Calculation logic
def calculate_profit(initial_investment, months, rate, detailed=False):
    current_amount = initial_investment
    monthly_profits = []
    for month in range(1, months + 1):
        profit = current_amount * rate
        current_amount += profit
        monthly_profits.append((month, profit, current_amount))
    total_profit = current_amount - initial_investment
    return total_profit, monthly_profits

# Perform the calculation
total_profit, monthly_profits = calculate_profit(total_investment, num_months, profit_rate)

# Display results
st.write("## Results")
st.write(f"**Total Profit:** {total_profit:.2f}")
st.write(f"**Total Amount After {num_months} Month(s):** {total_investment + total_profit:.2f}")

if show_details:
    st.write("### Monthly Profit Breakdown")
    for month, profit, amount in monthly_profits:
        st.write(f"Month {month}: Profit = {profit:.2f}, Total Amount = {amount:.2f}")
