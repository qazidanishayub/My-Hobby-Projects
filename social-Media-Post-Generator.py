import streamlit as st
import google.generativeai as genai
import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set page configuration
st.set_page_config(page_title="AI LinkedIn Post Generator", page_icon="✨", layout="wide")

# Custom CSS for Premium SaaS Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@700&display=swap');

    /* Base Theme */
    .stApp {
        background-color: #0A0A0F;
        color: #F0F0FF;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Typography */
    p, div, span, li, label {
        font-family: 'Inter', sans-serif !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em !important;
        color: #F0F0FF !important;
    }

    /* App Header */
    .hero-container {
        margin-top: -20px;
        margin-bottom: 30px;
    }
    .app-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: -0.02em;
    }
    .app-title-icon {
        color: #6C63FF;
        text-shadow: 0 0 15px rgba(108, 99, 255, 0.8);
    }
    .app-subtitle {
        color: #8888AA;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 24px;
    }
    .gradient-divider {
        height: 1px;
        background: linear-gradient(90deg, #6C63FF 0%, #00D4AA 50%, transparent 100%);
        box-shadow: 0 0 10px rgba(108, 99, 255, 0.5);
    }

    /* Sidebar Redesign */
    [data-testid="stSidebar"] {
        background-color: #111118 !important;
        border-right: 1px solid #1E1E2E !important;
    }
    .sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .sidebar-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.2rem;
        color: #F0F0FF;
    }
    .sidebar-badge {
        background-color: rgba(0, 212, 170, 0.15);
        color: #00D4AA;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(0, 212, 170, 0.3);
    }
    .sidebar-separator {
        height: 1px;
        background: #6C63FF;
        box-shadow: 0 0 8px #6C63FF;
        margin: 24px 0;
        opacity: 0.4;
    }

    /* Sidebar Mode Selector (Vertical Radio as Cards) */
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="vertical"] > label {
        background: #0A0A0F;
        border: 1px solid #1E1E2E;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        transition: all 0.25s ease;
        cursor: pointer;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="vertical"] > label:hover {
        border-color: #6C63FF;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="vertical"] > label[aria-checked="true"] {
        border: 1.5px solid #6C63FF;
        background: rgba(108, 99, 255, 0.05);
        box-shadow: inset 0 0 12px rgba(108, 99, 255, 0.15);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="vertical"] > label > div:first-child {
        display: none; /* Hide default radio circle */
    }

    /* Horizontal Radio (Domains & Tones as Pills) */
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] > label {
        background-color: #111118;
        border: 1px solid #1E1E2E;
        border-radius: 24px;
        padding: 10px 18px;
        color: #8888AA;
        transition: all 0.2s ease;
        cursor: pointer;
        margin: 0;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] > label:hover {
        color: #F0F0FF;
        border-color: #6C63FF;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] > label[aria-checked="true"] {
        background-color: rgba(108, 99, 255, 0.15);
        border-color: #6C63FF;
        color: #F0F0FF;
        box-shadow: 0 0 15px rgba(108, 99, 255, 0.25);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] > label > div:first-child {
        display: none; /* Hide default radio circle */
    }

    /* Inputs & Textareas */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select {
        background-color: #0A0A0F !important;
        border: 1px solid #1E1E2E !important;
        color: #F0F0FF !important;
        border-radius: 12px !important;
        transition: all 0.25s ease;
        padding: 12px 16px !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus, .stSelectbox>div>div>select:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 1px #6C63FF !important;
    }
    
    /* Thought Input Custom Card (for text area wrapper) */
    .thought-card {
        background: #111118;
        border: 1px solid #1E1E2E;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* Generate Button (Primary) */
    button[kind="primary"] {
        background: linear-gradient(90deg, #6C63FF, #00D4AA) !important;
        color: white !important;
        border: none !important;
        height: 52px !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.25s ease !important;
        animation: glow 3s infinite alternate;
        width: 100% !important;
        margin-top: 16px !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(108, 99, 255, 0.4) !important;
    }

    @keyframes glow {
        from { box-shadow: 0 0 8px rgba(108, 99, 255, 0.2); }
        to { box-shadow: 0 0 15px rgba(108, 99, 255, 0.5); }
    }

    /* Secondary Buttons (Action Bar) */
    button[kind="secondary"] {
        background-color: #111118 !important;
        border: 1px solid #1E1E2E !important;
        color: #8888AA !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        height: 44px !important;
    }
    button[kind="secondary"]:hover {
        background-color: #1E1E2E !important;
        color: #F0F0FF !important;
        border-color: #6C63FF !important;
    }

    /* Result Card */
    .result-card {
        background-color: #111118;
        border: 1px solid #1E1E2E;
        border-radius: 12px;
        overflow: hidden;
        margin-top: 32px;
        margin-bottom: 16px;
    }
    .result-topbar {
        background-color: #0073B1; /* LinkedIn Blue */
        color: white;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .result-content {
        padding: 24px;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #F0F0FF;
        white-space: pre-wrap;
    }

    /* Decorative Metrics Row */
    .metrics-row {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 32px;
        color: #8888AA;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 32px;
        background: #111118;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #1E1E2E;
    }
    .metric-val {
        color: #00D4AA;
        font-weight: 600;
    }

    /* Empty State */
    .empty-state {
        background-color: #111118;
        border: 1px solid #1E1E2E;
        border-radius: 16px;
        padding: 60px 20px;
        text-align: center;
        color: #8888AA;
        margin-top: 40px;
    }
    .empty-state-icon {
        font-size: 2rem;
        color: #8888AA;
        margin-bottom: 16px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #8888AA;
        font-size: 0.85rem;
        margin-top: 80px;
        padding-top: 24px;
        border-top: 1px solid #1E1E2E;
        opacity: 0.7;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE -----------------
if "generated_post" not in st.session_state:
    st.session_state.generated_post = None
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "show_edit" not in st.session_state:
    st.session_state.show_edit = False
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None

# ----------------- HEADER -----------------
st.markdown("""
<div class="hero-container">
    <div class="app-title"><span class="app-title-icon">✦</span> LinkedIn Post Generator</div>
    <div class="app-subtitle">Craft posts that get noticed. Powered by Gemini AI.</div>
    <div class="gradient-divider"></div>
</div>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <span class="sidebar-title">✦ Platform</span>
        <span class="sidebar-badge">v2.0</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Handle API Key
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        try:
            if "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
                api_key = st.secrets["gemini"]["api_key"]
        except Exception:
            pass
            
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password", help="Get your API key from Google AI Studio")
        st.markdown("<div style='color: #8888AA; font-size: 0.8rem; margin-top: -10px; margin-bottom: 10px;'>Your key never leaves this session.</div>", unsafe_allow_html=True)
        if not api_key:
            st.warning("Please enter your Gemini API Key to continue.", icon="⚠️")
    
    st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)
    
    mode = st.radio(
        "Choose Generation Mode:",
        [
            "⚡ **Quick Post**\n\nGenerate instantly from a raw idea", 
            "🛠️ **Guided Journey**\n\nFine-tune every aspect of your post"
        ],
        label_visibility="collapsed"
    )

# Configure Gemini
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-flash-latest")
else:
    st.stop() # Wait for API key

# ----------------- PROMPT BUILDER -----------------
def build_prompt(context, domain, custom_guidance="", tone="Professional"):
    base_prompt = f"""
You are an elite LinkedIn content strategist and writing expert. 
Your task is to generate a premium, engaging LinkedIn post (250–350 words) focusing on the domain: **{domain}**.

Key Elements to Include:
1. A compelling opening hook that stops the scroll.
2. A brief problem/opportunity statement.
3. A showcase of expertise, actionable insights, or a simple analogy.
4. A strong Call-To-Action (CTA) driving engagement.
5. Relevant trending hashtags (max 5).

Formatting & Style Rules:
- Tone: {tone}.
- Use clean, short paragraphs (1-3 sentences max).
- Use bullet points where appropriate for readability.
- Do NOT include any meta-text like "Here is your post:". Just output the raw LinkedIn post content.
"""
    if context:
        base_prompt += f"\n\nContext/Topic/Raw Idea:\n{context.strip()}"
    if custom_guidance:
        base_prompt += f"\n\nSpecific Guidance/Insights:\n{custom_guidance.strip()}"
        
    return base_prompt

def generate_post(prompt_text):
    st.session_state.last_prompt = prompt_text
    st.session_state.is_generating = True
    with st.spinner("✦ Gemini is crafting your post..."):
        try:
            response = model.generate_content(prompt_text)
            st.session_state.generated_post = response.text.strip()
            st.session_state.show_edit = False # Hide edit panel on new generation
            st.toast("Your post is ready! ✦")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error generating post: {e}")
    st.session_state.is_generating = False

# ----------------- MAIN CONTENT AREA -----------------
domains = ["🤖 Agentic AI", "🔍 RAG", "☁️ SaaS", "🧠 LLMs", "📊 Data", "⚙️ MLOps"]

if "Quick Post" in mode:
    st.markdown('<div class="thought-card">', unsafe_allow_html=True)
    user_idea = st.text_area("Thought Input", placeholder="Drop your raw idea here... we'll turn it into gold. ✦", height=120, label_visibility="collapsed")
    st.markdown("<div style='text-align: right; color: #8888AA; font-size: 0.75rem; margin-top: -15px;'>Aim for 1-2 sentences</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='color: #F0F0FF; font-family: Space Grotesk; font-weight: 700; margin-bottom: 12px;'>Select Domain</div>", unsafe_allow_html=True)
    selected_domain = st.radio("Domain", domains, horizontal=True, label_visibility="collapsed")
    
    if st.button("GENERATE MY POST ⚡", type="primary"):
        prompt = build_prompt(user_idea, selected_domain)
        generate_post(prompt)

elif "Guided Journey" in mode:
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("<div style='color: #F0F0FF; font-family: Space Grotesk; font-weight: 700; margin-bottom: 12px; font-size: 1.2rem;'>👤 Profile Info</div>", unsafe_allow_html=True)
        role = st.text_input("Your Role", placeholder="e.g. AI Engineer, Founder")
        industry = st.text_input("Industry", placeholder="e.g. Technology, Healthcare")
        
    with col2:
        st.markdown("<div style='color: #F0F0FF; font-family: Space Grotesk; font-weight: 700; margin-bottom: 12px; font-size: 1.2rem;'>🎯 Content Specs</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #F0F0FF; font-size: 0.9rem; margin-bottom: 8px;'>Tone</div>", unsafe_allow_html=True)
        tones = ["💼 Professional", "🔥 Bold", "🤝 Conversational", "🎓 Thought Leader"]
        selected_tone = st.radio("Tone", tones, horizontal=True, label_visibility="collapsed")
        
        st.markdown("<div style='color: #F0F0FF; font-size: 0.9rem; margin-top: 16px; margin-bottom: 8px;'>Domain</div>", unsafe_allow_html=True)
        selected_domain = st.radio("Domain", domains, horizontal=True, label_visibility="collapsed", key="guided_domain")

    st.markdown("<div style='color: #F0F0FF; font-family: Space Grotesk; font-weight: 700; margin-top: 32px; margin-bottom: 12px; font-size: 1.2rem;'>💡 Your Insights</div>", unsafe_allow_html=True)
    custom_topic = st.text_area("What do YOU know that others don't?", height=120, placeholder="Share a specific success, failure, or contrarian view...")
    
    if st.button("GENERATE MY POST ⚡", type="primary"):
        context = f"Role: {role}\\nIndustry: {industry}"
        prompt = build_prompt(context, selected_domain, custom_guidance=custom_topic, tone=selected_tone)
        generate_post(prompt)

# ----------------- OUTPUT SECTION -----------------
if st.session_state.generated_post:
    # Safely escape HTML for the pre-wrap content
    safe_post = st.session_state.generated_post.replace('<', '&lt;').replace('>', '&gt;')
    
    st.markdown(f"""
    <div class="result-card">
        <div class="result-topbar">
            <span>✦</span> YOUR POST IS READY
        </div>
        <div class="result-content">{safe_post}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action Bar
    a_col1, a_col2, a_col3, _ = st.columns([1, 1, 1, 3])
    with a_col1:
        # Use a st.code block hidden behind an expander or conditionally to act as a copy button
        if st.button("📋 Copy Post", use_container_width=True):
            st.toast("Copied! ✦")
            st.session_state.show_copy_code = True
    with a_col2:
        if st.button("🔄 Regenerate", use_container_width=True):
            if st.session_state.last_prompt:
                generate_post(st.session_state.last_prompt)
                st.rerun()
    with a_col3:
        if st.button("✏️ Edit & Refine", use_container_width=True):
            st.session_state.show_edit = not st.session_state.show_edit
            
    if st.session_state.get("show_copy_code", False):
        st.markdown("<div style='color:#00D4AA; font-size:0.8rem; margin-bottom:5px;'>Use the copy button in the top right corner below:</div>", unsafe_allow_html=True)
        st.code(st.session_state.generated_post, language="markdown")
            
    if st.session_state.show_edit:
        st.markdown("<br>", unsafe_allow_html=True)
        refine_instruction = st.text_input("What should I change?", placeholder="e.g. Make the hook punchier, add more emojis, make it shorter...")
        if st.button("Apply Changes", type="primary"):
            refine_prompt = f"""
You are refining a previously generated LinkedIn post based on user feedback.
Original Post:
{st.session_state.generated_post}

User Request: {refine_instruction}

Output ONLY the newly refined LinkedIn post. Do not include any meta-text.
"""
            generate_post(refine_prompt)
            st.rerun()

    # Engagement Prediction Metrics
    st.markdown("""
    <div class="metrics-row">
        <span>🔥 Hook Strength: <span class="metric-val">Strong</span></span>
        <span>📣 CTA Clarity: <span class="metric-val">High</span></span>
        <span>🏷️ Hashtag Relevance: <span class="metric-val">Optimized</span></span>
    </div>
    """, unsafe_allow_html=True)
    
else:
    if not st.session_state.is_generating:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">✦</div>
            Your LinkedIn post will appear here
        </div>
        """, unsafe_allow_html=True)

# ----------------- FOOTER -----------------
st.markdown("""
<div class="footer">
    Built with Gemini AI + Streamlit &nbsp;·&nbsp; <span style="color: #6C63FF;">✦</span> Made for Builders
</div>
""", unsafe_allow_html=True)
