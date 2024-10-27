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
    investment = st.number_input("Enter your total investment amount:", min_value=0.0, step=1.0)
    investment_date = st.date_input("Select your investment start date (optional):", value=None)
    calculation_date = st.date_input("Select profit calculation date (optional):", value=None)
    months = st.number_input("Enter the number of months:", min_value=1, step=1)
    profit_rate = st.number_input("Enter monthly profit rate (default is 3%):", min_value=0.0, value=3.0) / 100
else:
    st.header("سرمایہ کاری کی تفصیلات")
    investment = st.number_input("اپنی کل سرمایہ کاری کی رقم درج کریں:", min_value=0.0, step=1.0)
    investment_date = st.date_input("سرمایہ کاری کی تاریخ کا انتخاب کریں (اختیاری):", value=None)
    calculation_date = st.date_input("منافع کی حساب کتاب کی تاریخ کا انتخاب کریں (اختیاری):", value=None)
    months = st.number_input("مہینوں کی تعداد درج کریں:", min_value=1, step=1)
    profit_rate = st.number_input("ماہانہ منافع کی شرح درج کریں (پہلے سے طے شدہ 3% ہے):", min_value=0.0, value=3.0) / 100

# Calculate monthly compounded profit based on dates if provided
if investment_date and calculation_date:
    investment_date = datetime.combine(investment_date, datetime.min.time())
    calculation_date = datetime.combine(calculation_date, datetime.min.time())
    duration_days = (calculation_date - investment_date).days
    if duration_days < 0:
        st.warning("Profit calculation date must be after the investment date.")
    else:
        # Calculate profit based on days if within the same month
        monthly_profit = investment * profit_rate
        daily_profit = monthly_profit / 30
        total_profit = daily_profit * duration_days
        final_amount = investment + total_profit
else:
    # Calculate profit based on number of months if no dates provided
    current_amount = investment
    total_profit = 0
    monthly_profits = []

    for month in range(1, months + 1):
        monthly_profit = current_amount * profit_rate
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

# Display optional monthly breakdown if selected
if show_breakdown:
    if language == "English":
        st.subheader("Monthly Breakdown")
    else:
        st.subheader("ماہانہ تفصیل")

    breakdown_data = []
    if investment_date and calculation_date:
        # Generate breakdown based on days
        for day in range(duration_days):
            day_date = investment_date + timedelta(days=day)
            day_profit = daily_profit
            final_amount += day_profit
            breakdown_data.append({
                "Date" if language == "English" else "تاریخ": day_date.strftime("%Y-%m-%d"),
                "Daily Profit" if language == "English" else "روزانہ منافع": f"{day_profit:.2f}",
                "Total Amount" if language == "English" else "کل رقم": f"{final_amount:.2f}"
            })
    else:
        # Generate breakdown based on months
        for month, profit, amount in monthly_profits:
            month_info = {
                "Month" if language == "English" else "مہینہ": month,
                "Monthly Profit" if language == "English" else "ماہانہ منافع": f"{profit:.2f}",
                "Total Amount" if language == "English" else "کل رقم": f"{amount:.2f}"
            }
            breakdown_data.append(month_info)
    
    # Display breakdown as a formatted table
    if language == "English":
        st.table(breakdown_data)
    else:
        st.table(breakdown_data)
else:
    if language == "English":
        st.write("Monthly breakdown hidden.")
    else:
        st.write("ماہانہ تفصیل چھپی ہوئی ہے۔")

# Thank you message
if language == "English":
    st.write("Thank you for using the Scrap-Invest-Cross-Profit Calculator!")
else:
    st.write("اسکریپ-انویسٹ-کراس-پرافٹ کیلکولیٹر استعمال کرنے کے لیے شکریہ!")
