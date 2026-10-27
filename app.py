import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from streamlit_mic_recorder import speech_to_text
from PIL import Image

from supabase import create_client, Client
load_dotenv() # This loads your .env file

# Initialize Database Connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ==========================================
# 0. AUTHENTICATION GATEKEEPER
# ==========================================
# Initialize login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# If not logged in, show ONLY the login screen
if not st.session_state.logged_in:
    # Golden Hour Login CSS
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { 
            background: linear-gradient(-45deg, rgba(20, 15, 5, 0.9), rgba(5, 5, 5, 0.95)) !important;
            font-family: 'Inter', sans-serif;
        }
        [data-testid="stSidebar"] { display: none; } /* Hide sidebar on login page */
        [data-testid="stHeader"] { background-color: transparent !important; }
        
        .login-card {
            background: rgba(10, 10, 10, 0.75);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(245, 158, 11, 0.4);
            border-radius: 20px;
            padding: 50px 40px;
            max-width: 400px;
            margin: 100px auto;
            text-align: center;
            box-shadow: 0 0 45px rgba(245, 158, 11, 0.2);
        }
        .login-title { color: #FFFFFF; font-size: 2rem; font-weight: 800; margin-bottom: 5px; }
        .login-subtitle { color: #FCD34D; font-size: 0.9rem; margin-bottom: 30px; }
        
        .stButton>button { background: linear-gradient(90deg, #F59E0B, #D97706) !important; color: white !important; border: none !important; border-radius: 50px !important; width: 100%; font-weight: bold; margin-top: 15px; }
        .stTextInput>div>div>input { background-color: #121212 !important; color: white !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class='login-card'>
            <div class='login-title'>Livelihood AI</div>
            <div class='login-subtitle'>Secure Portal Access</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Place inputs inside columns to center them under the card visually
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.button("Access Portal"):
            if username.strip().lower() == "admin" and password.strip() == "admin":
                st.session_state.logged_in = True
                st.rerun() # Refreshes the app to show the main content
            else:
                st.error("Invalid credentials. Try admin / admin")
    
    # STOP execution here if not logged in
    st.stop()

# ==========================================
# 1. MAIN APP STARTS HERE (Only runs if logged_in is True)
# ==========================================
# (Your existing Sidebar, CSS, and Page Routing code should remain exactly as it is below this line)
# ==========================================
# 1. SETUP & SESSION STATE ROUTING
# ==========================================
# Must be the very first Streamlit command!
st.set_page_config(page_title="Livelihood AI | Team IDEAFORGE", page_icon="🛠️", layout="wide", initial_sidebar_state="expanded")

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ACTIVE_MODEL = 'gemma-4-26b-a4b-it' # Change to 'gemma-4-26b-a4b-it' before judging!

# Initialize app memory so it remembers where you are
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Home"
if 'active_tool' not in st.session_state:
    st.session_state.active_tool = "🎙️ Voice Input"

# Smart Router: Catches clicks from the Home Page Badges
if "tool" in st.query_params:
    if st.query_params["tool"] == "voice":
        st.session_state.current_page = "✨ AI Mapper"
        st.session_state.active_tool = "🎙️ Voice Input"
    elif st.query_params["tool"] == "vision":
        st.session_state.current_page = "✨ AI Mapper"
        st.session_state.active_tool = "📸 Document Upload"
    elif st.query_params["tool"] == "text":
        st.session_state.current_page = "✨ AI Mapper"
        st.session_state.active_tool = "⌨️ Text Input"
    st.query_params.clear() # Clears the URL after routing

# ==========================================
# 2. CSS STYLING (Golden Hour Cinematic Theme)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* ANIMATIONS */
    @keyframes gradientPan {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes breathingGlow {
        0% { box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); }
        50% { box-shadow: 0 0 45px rgba(245, 158, 11, 0.4); }
        100% { box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); }
    }

   /* 1. Bulletproof DUAL-IMAGE Background */
    .stApp, [data-testid="stAppViewContainer"] { 
        background-image: 
            /* Layer 1: Dark gradient in the center */
            linear-gradient(90deg, rgba(30, 15, 0, 0.4) 0%, rgba(10, 10, 10, 0.98) 45%, rgba(10, 10, 10, 0.98) 55%, rgba(30, 15, 0, 0.4) 100%),
            /* Layer 2: Left Image (Traditional Potter) */
            url("https://images.unsplash.com/photo-1531988042231-d39a936b19a6?w=1000&auto=format&fit=crop"),
            /* Layer 3: Right Image (Master Weaver) */
            url("https://images.unsplash.com/photo-1605814522774-68ebf03c004c?w=1000&auto=format&fit=crop") !important;
        
        background-position: center, left center, right center !important;
        background-repeat: no-repeat, no-repeat, no-repeat !important;
        background-size: 100% 100%, 50% 100%, 50% 100% !important;
        background-attachment: fixed !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* 2. Transparent header */
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* 3. Pitch Black Sidebar with Amber Accent Line */
    [data-testid="stSidebar"] { 
        background-color: #050505 !important; 
        border-right: 1px solid #F59E0B !important; 
    }
    
    /* 4. The Main Hero Container - Breathing Gold Glow */
    .hero { 
        background: rgba(10, 10, 10, 0.75); 
        backdrop-filter: blur(15px); 
        -webkit-backdrop-filter: blur(15px); 
        border: 1px solid rgba(245, 158, 11, 0.4); 
        border-radius: 20px; 
        padding: 60px 40px; 
        margin: 40px auto; 
        max-width: 950px; 
        animation: breathingGlow 4s infinite ease-in-out;
        text-align: center; 
    }
    
    /* Typography - High Contrast Whites and Warm Golds */
    .hero-tag { background: rgba(245, 158, 11, 0.15); border: 1px solid #F59E0B; padding: 6px 16px; border-radius: 50px; font-size: 0.85rem; color: #FCD34D; display: inline-block; margin-bottom: 20px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; }
    .hero-title { font-size: 4.5rem; font-weight: 900; line-height: 1.1; margin-bottom: 20px; color: #FFFFFF; letter-spacing: -1px; }
    .hero-title-accent { background: linear-gradient(90deg, #FDE68A, #F59E0B); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .hero-desc { font-size: 1.15rem; color: #d1d5db; max-width: 700px; margin: 0 auto 40px auto; line-height: 1.6; }

    /* Interactive Badges - Upgraded Hover Animations */
    .badge-row { display: flex; justify-content: center; gap: 20px; margin-top: 40px; flex-wrap: wrap; }
    .glass-badge { background: rgba(15, 15, 15, 0.85); border: 1px solid rgba(245, 158, 11, 0.25); padding: 15px 25px; border-radius: 12px; display: flex; align-items: center; gap: 15px; text-align: left; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; }
    .glass-badge:hover { background: rgba(30, 20, 5, 0.95); transform: translateY(-8px) scale(1.02); border-color: #F59E0B; box-shadow: 0 15px 35px rgba(245, 158, 11, 0.4); }
    .badge-icon { font-size: 26px; }
    .badge-val { font-weight: 800; font-size: 1.1rem; color: #FFFFFF; }
    .badge-lbl { font-size: 0.85rem; color: #9ca3af; }
    a { text-decoration: none !important; }
    
    /* Streamlit Native Elements - Redesigned to Amber */
    .stButton>button { background: linear-gradient(90deg, #F59E0B, #D97706) !important; color: white !important; border: 1px solid #FCD34D !important; border-radius: 50px !important; padding: 12px 30px !important; font-weight: bold !important; width: 100%; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.2); }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 8px 30px rgba(245, 158, 11, 0.6); color: white !important; }
    
    /* Radio Buttons */
    div[role="radiogroup"] > label { padding: 10px 20px; background: #121212; border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; margin-right: 10px; color: #d1d5db;}
    div[role="radiogroup"] > label[data-checked="true"] { background: rgba(245, 158, 11, 0.15); border-color: #F59E0B; color: #FCD34D; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)
# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("## 🛠️ Livelihood AI")
    st.markdown("**Team IDEAFORGE**")
    st.divider()
    
    # Navigation ties into the smart session state
    st.session_state.current_page = st.radio(
        "Navigation Menu", 
        ["🏠 Home", "✨ AI Mapper", "ℹ️ About"],
        index=["🏠 Home", "✨ AI Mapper", "ℹ️ About"].index(st.session_state.current_page)
    )
    st.divider()
    st.success(f"Status: Connected 🟢\n\nModel: {ACTIVE_MODEL}")

# ==========================================
# 4. PAGE LOGIC & MULTILINGUAL AI
# ==========================================
if st.session_state.current_page == "🏠 Home":
    st.markdown("""
<div class="hero">
<div class="hero-tag"> Track 1: Best Use of Google Gemma 4</div>
<div class="hero-title">Map Your Skills.<br><span class="hero-title-accent">Build Your Future.</span></div>
<div class="hero-desc">Unlock empowering job opportunities with AI-powered skill extraction, smart micro-learning, and personalized livelihood recommendations.</div>

<div class="badge-row">
    <!-- Clickable Links added to Badges -->
    <a href="?tool=voice" target="_self">
        <div class="glass-badge"><div class="badge-icon">🎙️</div><div><div class="badge-val">Voice-First</div><div class="badge-lbl">Audio AI Profiling</div></div></div>
    </a>
    <a href="?tool=text" target="_self">
        <div class="glass-badge"><div class="badge-icon">⌨️</div><div><div class="badge-val">Text Input</div><div class="badge-lbl">Manual AI Profiling</div></div></div>
    </a>
    <a href="?tool=vision" target="_self">
        <div class="glass-badge"><div class="badge-icon">📸</div><div><div class="badge-val">Visual Auth</div><div class="badge-lbl">Document Parsing</div></div></div>
    </a>
</div>
</div>
""", unsafe_allow_html=True)

elif st.session_state.current_page == "✨ AI Mapper":
    st.markdown("<h2 style='text-align: center; color: white;'>✨ Live AI Profiler</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #d1d5db; margin-bottom: 20px;'>Select your preferred input method below.</p>", unsafe_allow_html=True)
    
    # 1. CENTERED TOOL SELECTOR
    col_t1, col_t2, col_t3 = st.columns([1, 2, 1])
    with col_t2:
        st.session_state.active_tool = st.radio(
            "Select Tool", 
            ["🎙️ Voice Input", "⌨️ Text Input", "📸 Document Upload"], 
            horizontal=True,
            index=["🎙️ Voice Input", "⌨️ Text Input", "📸 Document Upload"].index(st.session_state.active_tool),
            label_visibility="collapsed"
        )
    
    # Elegant Golden Divider
    st.markdown("<hr style='border: 1px solid rgba(245, 158, 11, 0.2); margin: 25px 0;'>", unsafe_allow_html=True)

    if st.session_state.active_tool == "🎙️ Voice Input":
        # CENTERED LANGUAGE SELECTOR
        lang_dict = {"English": "en", "Hindi (हिंदी)": "hi", "Kannada (ಕನ್ನಡ)": "kn"}
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            st.markdown("<p style='text-align: center; color: #FCD34D; font-weight: 600; margin-bottom: 5px;'>🌐 Select Language / ಭಾಷೆ / भाषा</p>", unsafe_allow_html=True)
            chosen_lang = st.radio("Language", list(lang_dict.keys()), horizontal=True, label_visibility="collapsed")
            lang_code = lang_dict[chosen_lang]

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.markdown("<h3 style='color: white;'>1. Speak Background</h3>", unsafe_allow_html=True)
            st.info("Tap the button below and describe your daily work, traditional crafts, or hobbies.")
            user_speech = speech_to_text(language=lang_code, start_prompt="🟢 Start Recording", stop_prompt="🛑 Stop Recording", key=f'STT_{lang_code}')
            if user_speech:
                st.success(f'**Transcript:** "{user_speech}"')
                
        with col2:
            st.markdown("<h3 style='color: white;'>2. Generate Pathway</h3>", unsafe_allow_html=True)
            st.info("Gemma 4 will map your spoken skills directly to real-world opportunities.")
            if st.button("✨ Analyze Voice Profile", key="voice_btn"):
                if user_speech:
                    with st.spinner("Analyzing and saving to database..."):
                        try:
                            # 1. Generate AI Response
                            model = genai.GenerativeModel(ACTIVE_MODEL)
                            prompt = f"You are an AI Livelihood Assistant. Analyze this input: '{user_speech}'. You MUST translate and reply entirely in {chosen_lang}. Output strictly in Markdown: 1. 👤 Profile Summary 2. 💡 Extracted Skills 3. 🚀 Job Pathways 4. 📚 Next Steps."
                            ai_response = model.generate_content(prompt).text
                            
                            # 2. Display on screen
                            st.markdown(ai_response)
                            
                            # 3. Save to Supabase
                            supabase.table("ai_pathways").insert({
                                "input_method": "Voice Input",
                                "user_background": user_speech,
                                "gemma_response": ai_response
                            }).execute()
                            st.toast("✅ Saved successfully to Supabase!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please record your voice first.")

    elif st.session_state.active_tool == "⌨️ Text Input":
        col1_text, col2_text = st.columns([1, 1], gap="large")
        with col1_text:
            st.markdown("<h3 style='color: white;'>1. Type Background</h3>", unsafe_allow_html=True)
            st.info("Type out your past experiences, skills, or daily tasks.")
            user_text = st.text_area("Describe your background:", placeholder="E.g., I have 3 years of experience fixing bicycles in my neighborhood...", height=150, label_visibility="collapsed")
            
        with col2_text:
            st.markdown("<h3 style='color: white;'>2. Generate Pathway</h3>", unsafe_allow_html=True)
            st.info("Gemma 4 will extract your competencies and suggest career moves.")
            if st.button("✨ Analyze Text Profile", key="text_btn"):
                if user_text and user_text.strip() != "":
                    with st.spinner("Analyzing and saving to database..."):
                        try:
                            # 1. Generate AI Response
                            model = genai.GenerativeModel(ACTIVE_MODEL)
                            prompt = f"You are an AI Livelihood Assistant. Analyze: '{user_text}'. Output strictly in Markdown: 1. 👤 Profile Summary 2. 💡 Extracted Skills 3. 🚀 Job Pathways 4. 📚 Next Steps."
                            ai_response = model.generate_content(prompt).text
                            
                            # 2. Display on screen
                            st.markdown(ai_response)
                            
                            # 3. Save to Supabase
                            supabase.table("ai_pathways").insert({
                                "input_method": "Text Input",
                                "user_background": user_text,
                                "gemma_response": ai_response
                            }).execute()
                            st.toast("✅ Saved successfully to Supabase!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please type your background first.")

    elif st.session_state.active_tool == "📸 Document Upload":
        col3, col4 = st.columns([1, 1], gap="large")
        with col3:
            st.markdown("<h3 style='color: white;'>1. Upload Image</h3>", unsafe_allow_html=True)
            st.info("Upload a photo of a traditional craft, instrument, tool, or certificate.")
            uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
            if uploaded_file:
                from PIL import Image
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True, clamp=True)
                
        with col4:
            st.markdown("<h3 style='color: white;'>2. Verify Skills</h3>", unsafe_allow_html=True)
            st.info("Gemma 4 will visually verify the skill and recommend micro-jobs.")
            if st.button("✨ Extract Visual Skills", key="img_btn"):
                if uploaded_file:
                    with st.spinner("Extracting visual data and saving..."):
                        try:
                            # 1. Generate AI Response
                            model = genai.GenerativeModel(ACTIVE_MODEL)
                            img_prompt = "Analyze this image. What task or tool is shown? What skill does it prove? Recommend a micro-job."
                            ai_response = model.generate_content([img_prompt, image]).text
                            
                            # 2. Display on screen
                            st.markdown(ai_response)
                            
                            # 3. Save to Supabase
                            supabase.table("ai_pathways").insert({
                                "input_method": "Image Upload",
                                "user_background": f"Uploaded Image: {uploaded_file.name}",
                                "gemma_response": ai_response
                            }).execute()
                            st.toast("✅ Saved successfully to Supabase!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please upload an image first.")
elif st.session_state.current_page == "ℹ️ About":
    st.markdown("## ℹ️ About TEAM IDEAFORGE")
    st.write("This project was built for Hacktoberfest Track 1: Best Use of Google Gemma 4.")
    st.write("**Architecture:**")
    st.write("- **Frontend:** Streamlit with custom Glassmorphism UI")
    st.write("- **Audio:** `streamlit-mic-recorder`")
    st.write("- **Backend:** Google Gemini API (`gemma-4-26b-a4b-it`)")