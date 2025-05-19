import streamlit as st
import google.generativeai as genai

# Configure page
st.set_page_config(page_title="AI/ML LinkedIn Post Generator", layout="centered")
st.title("🤖 AI/ML LinkedIn Post Generator")

# Get Gemini API key from Streamlit secrets
api_key = st.secrets["gemini"]["api_key"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-001")

# Layout separator
st.markdown("### 🔍 Select How You Want to Guide the AI")

# Option to guide AI or let it choose
input_mode = st.radio(
    "Would you like to provide a specific topic or let the AI decide?",
    ("Let the AI choose", "I want to guide the topic"),
    index=0
)

user_idea = ""
if input_mode == "I want to guide the topic":
    user_idea = st.text_area(
        "✍️ Enter your custom idea, tool, result, or topic focus (Optional)",
        placeholder="e.g., Using RAG with LangChain and Pinecone for real-time knowledge retrieval...",
        height=100
    )

# Button to generate post
if st.button("🚀 Generate LinkedIn Post"):
    with st.spinner("Generating your expert-level post..."):

        # Prompt with expert structure and AI/ML topic scope
        base_prompt = """
You are a LinkedIn content strategist and writing expert focused on AI, ML, and Data Science topics. Your goal is to help a highly skilled AI/ML/SaaS engineer or thought leader consistently create powerful, professional, and engaging LinkedIn posts that:

• Showcase their expertise in cutting-edge technology  
• Educate and engage a technically-savvy audience  
• Generate organic leads and inbound interest from professionals and businesses  
• Position the user as a go-to expert in their niche  

Each post should focus on one or more of the following topic areas:
- Generative AI (GenAI)
- Large Language Models (LLMs)
- Retrieval-Augmented Generation (RAG)
- Agentic AI and autonomous agents
- GenAI-powered reporting and analytics
- Applied AI/ML/Data Science in SaaS products
- Infrastructure or tools (LangChain, LlamaIndex, vector DBs, etc.)
- Use cases and real-world implementations of AI in business

Your task is to generate a LinkedIn post (250–350 words) using a structure that maximizes engagement and value:

1. A compelling opening hook (question, bold statement, or insight)
2. A clear explanation of the core topic (challenge, opportunity, or concept)
3. A simple analogy or breakdown (if needed) to clarify complex ideas
4. A showcase of user expertise: tools used, results achieved, impact made
5. A strong call to action (CTA) to encourage engagement or connection
6. Optional: a question, poll idea, or comment prompt to increase interaction

If the user provides a custom topic, insight, or example, incorporate it seamlessly. Otherwise, rely on your own expert judgment to pick a relevant and high-value theme from the allowed topics above.

At the end of the post, automatically add trending and relevant hashtags (e.g., #GenerativeAI, #MachineLearning, #RAGsystems, #LangChain, #AIBusiness, #SaaS, etc.) based on the theme—without explicitly calling them out in the post body.

The tone must be:
- Confident and insightful
- Conversational, yet professional
- Optimized for readability (short paragraphs, lists, or bullets)

The output should be a single LinkedIn-ready post, clean and copy-pasteable text.
"""

        if user_idea:
            base_prompt += f"\n\nUser Input:\n{user_idea.strip()}"

        try:
            response = model.generate_content(base_prompt)
            final_post = response.text.strip()

            st.markdown("### ✅ Your LinkedIn-Ready Post")
            st.code(final_post, language=None)

            st.download_button(
                label="📋 Copy to Clipboard",
                data=final_post,
                file_name="linkedin_post.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"❌ Error generating content: {e}")
