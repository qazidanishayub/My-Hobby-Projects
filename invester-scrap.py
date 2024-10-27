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
    investment_type = st.selectbox("Select your investment amount type:", ["Custom Amount", "Millions", "Lacs"])
    
    if investment_type == "Millions":
        investment = st.number_input("Enter your total investment amount (in millions):", min_value=0.0, step=1.0) * 1_000_000
    elif investment_type == "Lacs":
        investment = st.number_input("Enter your total investment amount (in lacs):", min_value=0.0, step=1.0) * 100_000
    else:
        investment = st.number_input("Enter your total investment amount:", min_value=0.0, step=1.0)

    date_based_option = st.selectbox("Select investment calculation method:", ["Custom Dates", "Number of Months", "Number of Quarters"])
    
    if date_based_option == "Custom Dates":
        investment_date = st.date_input("Select your investment start date:", value=None)
        calculation_date = st.date_input("Select profit calculation date:", value=None)
        months = None  # Disable months input
    elif date_based_option == "Number of Months":
        investment_date = None  # Disable date input
        calculation_date = None  # Disable date input
        months = st.number_input("Enter the number of months:", min_value=1, step=1)
    else:  # Number of Quarters
        investment_date = None  # Disable date input
        calculation_date = None  # Disable date input
        quarters = st.number_input("Enter the number of quarters:", min_value=1, step=1)
        months = quarters * 3  # Calculate total months from quarters

    profit_rate = st.number_input("Enter monthly profit rate (default is 3%):", min_value=0.0, value=3.0) / 100

else:
    st.header("سرمایہ کاری کی تفصیلات")
    investment_type = st.selectbox("اپنی سرمایہ کاری کی رقم کی قسم منتخب کریں:", ["حسب ضرورت رقم", "ملین", "لاکھ"])
    
    if investment_type == "ملین":
        investment = st.number_input("اپنی کل سرمایہ کاری کی رقم درج کریں (ملین میں):", min_value=0.0, step=1.0) * 1_000_000
    elif investment_type == "لاکھ":
        investment = st.number_input("اپنی کل سرمایہ کاری کی رقم درج کریں (لاکھ میں):", min_value=0.0, step=1.0) * 100_000
    else:
        investment = st.number_input("اپنی کل سرمایہ کاری کی رقم درج کریں:", min_value=0.0, step=1.0)

    date_based_option = st.selectbox("سرمایہ کاری کی حساب کتاب کے طریقہ کار کا انتخاب کریں:", ["حسب ضرورت تاریخیں", "مہینوں کی تعداد", "رُب کی تعداد"])
    
    if date_based_option == "حسب ضرورت تاریخیں":
        investment_date = st.date_input("سرمایہ کاری کی تاریخ کا انتخاب کریں:", value=None)
        calculation_date = st.date_input("منافع کی حساب کتاب کی تاریخ کا انتخاب کریں:", value=None)
        months = None  # Disable months input
    elif date_based_option == "مہینوں کی تعداد":
        investment_date = None  # Disable date input
        calculation_date = None  # Disable date input
        months = st.number_input("مہینوں کی تعداد درج کریں:", min_value=1, step=1)
    else:  # رُب کی تعداد
        investment_date = None  # Disable date input
        calculation_date = None  # Disable date input
        quarters = st.number_input("رُب کی تعداد درج کریں:", min_value=1, step=1)
        months = quarters * 3  # Calculate total months from quarters

    profit_rate = st.number_input("ماہانہ منافع کی شرح درج کریں (پہلے سے طے شدہ 3% ہے):", min_value=0.0, value=3.0) / 100

# Calculate monthly compounded profit based on dates if provided
if investment_date and calculation_date:
    investment_date = datetime.combine(investment_date, datetime.min.time())
    calculation_date = datetime.combine(calculation_date, datetime.min.time())
    duration_days = (calculation_date - investment_date).days
    if duration_days < 0:
        st.warning("Profit calculation date must be after the investment date.")
    else:
        total_profit = 0
        total_months = duration_days // 30
        remaining_days = duration_days % 30

        # Calculate profit for complete months
        for month in range(total_months):
            monthly_profit = investment * profit_rate
            total_profit += monthly_profit
            investment += monthly_profit

        # Calculate profit for remaining days
        daily_profit = (investment * profit_rate) / 30
        remaining_profit = daily_profit * remaining_days
        total_profit += remaining_profit

        final_amount = investment + remaining_profit
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
        # Generate breakdown based on custom dates
        for month in range(total_months):
            month_profit = investment * profit_rate
            investment += month_profit
            breakdown_data.append({
                "Month" if language == "English" else "مہینہ": month + 1,
                "Monthly Profit" if language == "English" else "ماہانہ منافع": f"{month_profit:.2f}",
                "Total Amount" if language == "English" else "کل رقم": f"{investment:.2f}"
            })

        # Add remaining days profit to the last month
        remaining_days_profit = daily_profit * remaining_days
        breakdown_data.append({
            "Month" if language == "English" else "مہینہ": f"Remaining Days ({remaining_days})",
            "Monthly Profit" if language == "English" else "ماہانہ منافع": f"{remaining_days_profit:.2f}",
            "Total Amount" if language == "English" else "کل رقم": f"{investment + remaining_days_profit:.2f}"
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

# Thank you message
if language == "English":
    st.write("Thank you for using the Scrap-Invest-Cross-Profit Calculator!")
else:
    st.write("اسکریپ-انویسٹ-کراس-پرافٹ کیلکولیٹر استعمال کرنے کے لیے شکریہ!")
