import streamlit as st
import pandas as pd
import datetime
import os
from twilio.rest import Client

# ---------------------------------------------------------
# Configuration Setup
# ---------------------------------------------------------
EXCEL_FILE = "feedback_records.xlsx"

# Your specific Twilio Credentials
TWILIO_ACCOUNT_SID = "AC1baa5b610d8ecb88f8aa7699ba000d8d"
TWILIO_AUTH_TOKEN = "c93d2f804c19c8612456ea178f6b8af8"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+4915888620339"  # Sender
TARGET_WHATSAPP_NUMBER = "whatsapp:+34674990399"    # Recipient

def save_to_excel(data):
    """Appends submission data to an Excel file."""
    df_new = pd.DataFrame([data])
    if os.path.exists(EXCEL_FILE):
        df_existing = pd.read_excel(EXCEL_FILE)
        df_updated = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_updated = df_new
    
    df_updated.to_excel(EXCEL_FILE, index=False)

def send_whatsapp_alert(entry):
    """Sends a dynamic text message via Twilio API."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Build dynamic text payload
        message_body = (
            f"📌 *New Feedback/Complaint Submission*\n\n"
            f"• *Category:* {entry['Type']}\n"
            f"• *Target Staff/Teacher:* {entry['Teacher Name']}\n"
            f"• *Submitted By:* {entry['Submitted By']}\n"
            f"• *Contact:* {entry['Contact Info']}\n"
            f"• *Rating:* {entry['Rating']}\n\n"
            f"📝 *Details:*\n{entry['Feedback / Details']}\n\n"
            f"🕒 *Time:* {entry['Timestamp']}"
        )
        
        # Using body instead of ContentSid for custom text messages
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=TARGET_WHATSAPP_NUMBER
        )
        return True, message.sid
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------
# Streamlit Interface
# ---------------------------------------------------------
st.set_page_config(page_title="Teacher Feedback & Complaint Portal", layout="centered")

st.title("🏫 Feedback & Complaint Portal")
st.write("Submit your feedback or complaints securely. You can choose to remain anonymous.")

with st.form("feedback_form", clear_on_submit=True):
    category = st.selectbox("Category", ["General Feedback", "Complaint", "Suggestion"])
    teacher_name = st.text_input("Target Teacher / Staff Member Name (Optional)")
    
    rating = st.slider("Rating (1 = Poor, 5 = Excellent)", 1, 5, 3) if category == "General Feedback" else None
    
    details = st.text_area("Detailed Message / Complaint*", height=150)
    
    st.subheader("Identity Settings")
    is_anonymous = st.checkbox("Submit Anonymously", value=True)
    
    if not is_anonymous:
        submittor_name = st.text_input("Your Full Name")
        submittor_contact = st.text_input("Your Email or Phone (Optional)")
    else:
        submittor_name = "Anonymous"
        submittor_contact = "N/A"
        
    send_whatsapp = st.checkbox("Forward alert to Admin via WhatsApp", value=True)
    
    submitted = st.form_submit_button("Submit Form")

if submitted:
    if not details.strip():
        st.error("Please enter details before submitting.")
    else:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        record = {
            "Timestamp": timestamp,
            "Type": category,
            "Teacher Name": teacher_name if teacher_name else "N/A",
            "Rating": rating if rating else "N/A",
            "Submitted By": submittor_name,
            "Contact Info": submittor_contact,
            "Feedback / Details": details
        }
        
        # 1. Excel Recording
        save_to_excel(record)
        st.success("Your submission has been recorded in the Excel database!")
        
        # 2. WhatsApp Notification
        if send_whatsapp:
            success, response = send_whatsapp_alert(record)
            if success:
                st.info(f"WhatsApp alert dispatched successfully! (Message SID: {response})")
            else:
                st.warning(f"Saved to Excel, but WhatsApp delivery failed: {response}")
