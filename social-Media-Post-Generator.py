import streamlit as st
import google.generativeai as genai
import os

# Set page configuration
st.set_page_config(page_title="AI-Based LinkedIn Post Generator", layout="centered")
st.title("🤖 AI-Driven LinkedIn Post Generator")

# Get API key from secrets
api_key = st.secrets["gemini"]["api_key"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-001")

# Sidebar navigation
st.sidebar.title("🧭 Navigation")
mode = st.sidebar.radio("Choose Generation Mode:", ["⚡ Quick Post", "🛠️ Guided Journey"])

# Domain options
domains = [
    "AI/ML/GenAI/RAG (default)",
    "Data Science & Analytics",
    "Agentic AI / Autonomous Agents",
    "SaaS Business Applications",
    "Healthcare AI",
    "Fintech + AI",
    "eCommerce AI/ML",
    "LegalTech / RegTech",
    "Scientific Research + GenAI",
    "Content Creation & AI",
    "Custom Domain..."
]

def build_prompt(user_idea, domain):
    base_prompt = f"""
You are a LinkedIn content strategist and writing expert focused on cutting-edge technology domains. Your goal is to help a highly skilled expert create professional, engaging LinkedIn posts that:

• Showcase expertise in their field  
• Educate a technically-savvy audience  
• Generate leads and interest from peers or clients  
• Position the user as a thought leader

This post should focus on the domain: **{domain}**

Your task is to generate a LinkedIn post (250–350 words) that includes:
1. A compelling opening hook
2. A brief problem/opportunity statement
3. Simple breakdown or analogy (if needed)
4. A showcase of user expertise, tools, or impact
5. A CTA to drive engagement
6. Add relevant, trending hashtags at the end based on the theme (without explaining them)

If user guidance is given, integrate it naturally. Otherwise, choose a theme in the selected domain.

The tone should be:
- Confident and insightful
- Conversational yet professional
- Clean, short paragraphs or bullets for readability

Output a clean, copy-pasteable LinkedIn post.
"""
    if user_idea:
        base_prompt += f"\n\nUser Input:\n{user_idea.strip()}"
    return base_prompt

if mode == "⚡ Quick Post":
    st.markdown("### ⚡ Quick AI-Based Post Generation")
    user_idea = st.text_area("Optional: Add a focus or idea", "", height=100)
    selected_domain = st.selectbox("Choose your content domain:", domains)
    
    if selected_domain == "Custom Domain...":
        selected_domain = st.text_input("Enter your custom domain")

    if st.button("🚀 Generate Post"):
        with st.spinner("Crafting your post..."):
            prompt = build_prompt(user_idea, selected_domain)
            try:
                response = model.generate_content(prompt)
                final_post = response.text.strip()
                st.markdown("### ✅ Your LinkedIn Post")
                st.text_area("", value=final_post, height=400)
                st.download_button("📋 Copy to Clipboard", data=final_post, file_name="linkedin_post.txt")
            except Exception as e:
                st.error(f"Error: {e}")

elif mode == "🛠️ Guided Journey":
    st.markdown("### 🧭 Guided Post Builder")
    with st.form("guided_form"):
        role = st.selectbox("Your Role", ["AI Engineer", "ML Researcher", "Tech Founder", "Product Manager", "Consultant", "Other"])
        industry = st.selectbox("Industry", ["Technology", "Healthcare", "Finance", "Education", "Legal", "Other"])
        product_type = st.text_input("What product or service are you working on?")
        market = st.selectbox("Target Market", ["B2B", "B2C", "Enterprise", "Startups", "Mixed"])
        region = st.selectbox("Regional Focus", ["Global", "North America", "Europe", "APAC", "Other"])
        tone = st.selectbox("Preferred Tone", ["Professional", "Conversational", "Technical", "Inspiring"])
        domain = st.selectbox("Post Domain", domains)
        custom_topic = st.text_area("Any specific idea, success, or insight to include?")
        submitted = st.form_submit_button("🚀 Generate My Post")

    if submitted:
        if domain == "Custom Domain...":
            domain = st.text_input("Enter your custom domain")
        user_idea = f"Role: {role}\nIndustry: {industry}\nProduct: {product_type}\nMarket: {market}\nRegion: {region}\nTone: {tone}\nCustom Input: {custom_topic}"
        prompt = build_prompt(user_idea, domain)

        with st.spinner("Generating your LinkedIn post..."):
            try:
                response = model.generate_content(prompt)
                final_post = response.text.strip()
                st.markdown("### ✅ Post Preview")
                st.text_area("", value=final_post, height=400)
                st.download_button("📋 Copy to Clipboard", data=final_post, file_name="linkedin_post.txt")
            except Exception as e:
                st.error(f"Error: {e}")
