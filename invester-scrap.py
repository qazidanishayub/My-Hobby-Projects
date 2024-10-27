import streamlit as st
from datetime import datetime, timedelta

# Language selection
language = st.selectbox("Select Language / زبان منتخب کریں", ["English", "اردو"])

# Set the title and description based on the language
if language == "English":
    st.title("Scrap-Invest-Cross-Profit Calculator")
    st.write("Calculate your monthly compounded profit and view a detailed breakdown, if desired.")
else:
    st.title("اسکریپ-انویسٹ-کراس-پرافٹ کیلکولیٹر")
    st.write("اپنے ماہانہ مرکب منافع کا حساب لگائیں اور اگر چاہیں تو تفصیلی بریک ڈاؤن دیکھیں۔")

# Input fields for user information
if language == "English":
    st.header("Investment Details")
    investment = st.number_input("Enter your total investment amount:", min_value=0.0, step=1.0)
    investment_time = st.text_input("Investment start date (optional, format: YYYY-MM-DD):")
    st.subheader("Duration")
    months = st.number_input("Enter the number of months:", min_value=1, step=1)
    profit_rate = st.number_input("Enter monthly profit rate (default is 3%):", min_value=0.0, value=3.0) / 100
else:
    st.header("سرمایہ کاری کی تفصیلات")
    investment = st.number_input("اپنی کل سرمایہ کاری کی رقم درج کریں:", min_value=0.0, step=1.0)
    investment_time = st.text_input("سرمایہ کاری کی تاریخ (اختیاری، فارمیٹ: YYYY-MM-DD):")
    st.subheader("مدت")
    months = st.number_input("مہینوں کی تعداد درج کریں:", min_value=1, step=1)
    profit_rate = st.number_input("ماہانہ منافع کی شرح درج کریں (پہلے سے طے شدہ 3% ہے):", min_value=0.0, value=3.0) / 100

# Processing the investment details
if investment_time:
    try:
        investment_date = datetime.strptime(investment_time, "%Y-%m-%d")
    except ValueError:
        if language == "English":
            st.warning("Please enter a valid date format (YYYY-MM-DD).")
        else:
            st.warning("براہ کرم درست تاریخ کا فارمیٹ درج کریں (YYYY-MM-DD)")
        investment_date = None
else:
    investment_date = None

# Calculate compounded profit
current_amount = investment
monthly_profits = []
total_profit = 0

for month in range(1, months + 1):
    monthly_profit = current_amount * profit_rate
    current_amount += monthly_profit
    monthly_profits.append((month, monthly_profit, current_amount))
    total_profit += monthly_profit

# Displaying results
if language == "English":
    st.header("Results")
    st.write(f"Total profit after {months} months: **{total_profit:.2f}**")
    st.write(f"Total amount after {months} months: **{current_amount:.2f}**")
else:
    st.header("نتائج")
    st.write(f"{months} مہینوں کے بعد کل منافع: **{total_profit:.2f}**")
    st.write(f"{months} مہینوں کے بعد کل رقم: **{current_amount:.2f}**")

# Optional breakdown
show_breakdown = st.checkbox("Show monthly profit breakdown" if language == "English" else "ماہانہ منافع کی تفصیل دکھائیں")

if show_breakdown:
    if language == "English":
        st.subheader("Monthly Breakdown")
    else:
        st.subheader("ماہانہ تفصیل")
    
    breakdown_data = []
    for month, profit, amount in monthly_profits:
        month_info = {
            "Month" if language == "English" else "مہینہ": month,
            "Monthly Profit" if language == "English" else "ماہانہ منافع": f"{profit:.2f}",
            "Total Amount" if language == "English" else "کل رقم": f"{amount:.2f}"
        }
        if investment_date:
            month_date = investment_date + timedelta(days=30 * (month - 1))
            month_info["Date" if language == "English" else "تاریخ"] = month_date.strftime("%Y-%m-%d")
        breakdown_data.append(month_info)
    
    # Display breakdown as a table
    st.write(breakdown_data)
else:
    if language == "English":
        st.write("Monthly breakdown hidden.")
    else:
        st.write("ماہانہ تفصیل چھپی ہوئی ہے۔")

if language == "English":
    st.write("Thank you for using the Scrap-Invest-Cross-Profit Calculator!")
else:
    st.write("اسکریپ-انویسٹ-کراس-پرافٹ کیلکولیٹر استعمال کرنے کے لیے شکریہ!")
