import streamlit as st
from datetime import datetime, timedelta

# Set the title and description of the app
st.title("Scrap-Invest-Cross-Profit Calculator")
st.write("Calculate your monthly compounded profit and view a detailed breakdown, if desired.")

# Input fields for user information
st.header("Investment Details")

# Investment amount
investment = st.number_input("Enter your total investment amount:", min_value=0.0, step=1.0)

# Time period information (optional)
investment_time = st.text_input("Investment start date (optional, format: YYYY-MM-DD):")
if investment_time:
    try:
        investment_date = datetime.strptime(investment_time, "%Y-%m-%d")
    except ValueError:
        st.warning("Please enter a valid date format (YYYY-MM-DD).")
        investment_date = None
else:
    investment_date = None

# Duration (either in months or as an end date)
st.subheader("Duration")
months = st.number_input("Enter the number of months:", min_value=1, step=1)

# Profit rate (with default 3% but customizable)
profit_rate = st.number_input("Enter monthly profit rate (default is 3%):", min_value=0.0, value=3.0) / 100

# Calculate the monthly compounded profit
current_amount = investment
monthly_profits = []
total_profit = 0

for month in range(1, months + 1):
    monthly_profit = current_amount * profit_rate
    current_amount += monthly_profit
    monthly_profits.append((month, monthly_profit, current_amount))
    total_profit += monthly_profit

# Display results
st.header("Results")
st.write(f"Total profit after {months} months: **{total_profit:.2f}**")
st.write(f"Total amount after {months} months: **{current_amount:.2f}**")

# Show detailed monthly breakdown
show_breakdown = st.checkbox("Show monthly profit breakdown")

if show_breakdown:
    st.subheader("Monthly Breakdown")
    breakdown_data = []
    for month, profit, amount in monthly_profits:
        month_info = {
            "Month": month,
            "Monthly Profit": f"{profit:.2f}",
            "Total Amount": f"{amount:.2f}"
        }
        if investment_date:
            month_date = investment_date + timedelta(days=30 * (month - 1))
            month_info["Date"] = month_date.strftime("%Y-%m-%d")
        breakdown_data.append(month_info)
    
    # Display breakdown as a table
    st.write(breakdown_data)
else:
    st.write("Monthly breakdown hidden.")

st.write("Thank you for using the Scrap-Invest-Cross-Profit Calculator!")
