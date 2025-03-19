import streamlit as st
from datetime import datetime, timedelta

# Sidebar configuration for language and breakdown toggle
st.sidebar.title("Settings")
language = st.sidebar.selectbox("Select Language / زبان منتخب کریں", ["English", "اردو"])
show_breakdown = st.sidebar.checkbox("Show monthly profit breakdown" if language == "English" else "ماہانہ منافع کی تفصیل دکھائیں", value=False)

# Main title and description based on language
if language == "English":
    st.title("Scrap-Invest-Cross-Profit Calculator")
    st.write("Calculate your monthly compounded profit and view a detailed breakdown, if desired.")
else:
    st.title("اسکریپ-انویسٹ-کراس-پرافٹ کیلکولیٹر")
    st.write("اپنے ماہانہ مرکب منافع کا حساب لگائیں اور اگر چاہیں تو تفصیلی بریک ڈاؤن دیکھیں۔")

# Input fields for user information
if language == "English":
    st.header("Investment Details")
    investment_type = st.selectbox("Select your investment amount type:", ["Millions", "Custom Amount", "Lacs"])
    
    if investment_type == "Millions":
        investment = st.number_input("Enter your total investment amount (in millions):", min_value=0.0, value=1.0, step=1.0) * 1_000_000
    elif investment_type == "Lacs":
        investment = st.number_input("Enter your total investment amount (in lacs):", min_value=0.0, value=5.0, step=1.0) * 100_000
    else:
        investment = st.number_input("Enter your total investment amount:", min_value=0.0, step=1.0)

    date_based_option = st.selectbox("Select investment calculation method:", [ "Number of Months", "Custom Dates", "Number of Quarters"])
    
    if date_based_option == "Custom Dates":
        investment_date = st.date_input("Select your investment start date:", value=None)
        calculation_date = st.date_input("Select profit calculation date:", value=None)
        months = None
    elif date_based_option == "Number of Months":
        investment_date = None
        calculation_date = None
        months = st.number_input("Enter the number of months:", min_value=1, step=1)
    else:
        investment_date = None
        calculation_date = None
        quarters = st.number_input("Enter the number of quarters:", min_value=1, step=1)
        months = quarters * 3

    profit_rate = st.number_input("Enter monthly profit rate (default is 3%):", min_value=0.0, value=3.0) / 100

# Calculate profit
current_amount = investment
total_profit = 0
monthly_profits = []

deduction_amount = st.number_input("Enter amount to subtract from profit each month:", min_value=0.0, step=1.0)

for month in range(1, months + 1):
    monthly_profit = current_amount * profit_rate
    if monthly_profit >= deduction_amount:
        monthly_profit -= deduction_amount
    else:
        monthly_profit = 0
    
    current_amount += monthly_profit
    monthly_profits.append((month, monthly_profit, current_amount))
    total_profit += monthly_profit

final_amount = current_amount

# Display results
if language == "English":
    st.header("Results")
    st.write(f"Total profit: **{total_profit:.2f}**")
    st.write(f"Total amount: **{final_amount:.2f}**")
else:
    st.header("نتائج")
    st.write(f"کل منافع: **{total_profit:.2f}**")
    st.write(f"کل رقم: **{final_amount:.2f}**")

# Button to view monthly profit increments
if st.button("View Monthly Profit Increments" if language == "English" else "ماہانہ منافع میں اضافہ دیکھیں"):
    if language == "English":
        st.subheader("Monthly Profit Increments")
    else:
        st.subheader("ماہانہ منافع میں اضافہ")
    
    increments_data = [{"Month": month, "Monthly Profit": f"{profit:.2f}", "Total Amount": f"{amount:.2f}"} for month, profit, amount in monthly_profits]
    st.table(increments_data)

# Thank you message
if language == "English":
    st.write("Thank you for using the Scrap-Invest-Cross-Profit Calculator!")
else:
    st.write("اسکریپ-انویسٹ-کراس-پرافٹ کیلکولیٹر استعمال کرنے کے لیے شکریہ!")
