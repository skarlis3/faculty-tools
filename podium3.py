import streamlit as st
import streamlit.components.v1 as components
from ics import Calendar
from datetime import datetime, timedelta
import requests

# --- PRIVATE CONFIGURATION ---
CLASS_CALENDARS = {
    "ENGL 1170 (Mondays)": "https://calendar.google.com/calendar/ical/96bccc53c2e45d1bd36c7075b4c7421cfcfe6789f9f451e926f18e598c42e1a4%40group.calendar.google.com/public/basic.ics",
    "ENGL 1170 (Tuesdays)": "https://calendar.google.com/calendar/ical/f3df4847b18f876bda1420bdce9d5710558f73557203b228f5775fb4768ccad6%40group.calendar.google.com/public/basic.ics",
    "ENGL 1181 (Mon/Wed)": "https://calendar.google.com/calendar/ical/0157024f1bbf32b1bda8275d5fff0a01e688d60921bb75e13b0d994d429a20fe%40group.calendar.google.com/public/basic.ics",
    "ENGL 1181 (Tues/Thurs)": "https://calendar.google.com/calendar/ical/1ba2d62ad576db0224203216cfccbd583108a8ed3ddd170ca4c1aee9067d8fac%40group.calendar.google.com/public/basic.ics",
    "ENGL 1181 (Tuesdays—Hybrid)": "https://calendar.google.com/calendar/ical/80c43857f8868cc0830f775213c16804819b2663a63a4785b5a91ae183fda585%40group.calendar.google.com/public/basic.ics",
    "ENGL 1190 (Mon/Wed)": "https://calendar.google.com/calendar/ical/5ccac57e3b214413edfd731d32b4be4514c614f17bc034f363e61107d16c75f6%40group.calendar.google.com/public/basic.ics",
    "ENGL 1190 (Tues/Thurs)": "https://calendar.google.com/calendar/ical/39ba7ac909903e1b6b3698153819e6a813638bb279c7c14295dec343b7b9464e%40group.calendar.google.com/public/basic.ics"
}

# --- PAGE SETUP ---
st.set_page_config(page_title="Classroom Podium v3", page_icon="💻", layout="wide")

# --- THE NUCLEAR CSS ---
st.markdown("""
<style>
    /* 1. REMOVE STREAMLIT PADDING - FORCES CONTENT TO THE EDGES */
    .block-container {
        padding: 1rem 2rem !important;
        max-width: 98% !important;
    }

    .stApp {
        background-color: #050a10; 
        background-image: radial-gradient(circle at 0% 0%, #111a2e 0%, #050a10 60%);
    }

    /* 2. FORCE HEADERS */
    .dashboard-title { 
        font-size: 7vw !important; 
        font-weight: 200 !important;
        line-height: 1 !important;
        color: white !important;
    }
    
    .dashboard-subtitle { 
        font-size: 2.5vw !important; 
        color: #38bdf8 !important; 
        margin-bottom: 2rem !important;
    }

    /* 3. THE AGENDA ITEMS (MASSIVE) */
    .card-header {
        font-size: 2vw !important; 
        color: #38bdf8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.4rem !important;
        border-bottom: 2px solid rgba(56, 189, 248, 0.3) !important;
        margin-bottom: 1.5rem !important;
    }

    .card-list {
        font-size: 5.5vw !important; /* Extremely large */
        font-weight: 400 !important; 
        line-height: 1.2 !important;
        list-style-type: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .card-list li {
        margin-bottom: 1.5rem !important;
        padding-left: 1.5rem !important;
        border-left: 10px solid #38bdf8 !important;
        color: #ffffff !important;
    }

    /* 4. NOTICES AND CARDS */
    .tfw-notice { 
        background: rgba(3, 105, 161, 0.3) !important;
        border-left: 5px solid #38bdf8 !important; 
        color: #e2e8f0 !important; 
        padding: 1.5vw !important; 
        font-size: 1.4vw !important; 
        width: 90% !important;
        margin-bottom: 2rem !important;
    }

    .glass-card { 
        background: rgba(13, 17, 23, 0.9) !important; 
        border: 2px solid rgba(56, 189, 248, 0.4) !important; 
        border-radius: 15px !important; 
        padding: 2.5vw !important;
        margin-bottom: 2rem !important;
    }

    /* Smaller buttons so they don't distract */
    div.stButton > button {
        font-size: 1vw !important;
        background: transparent !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        color: #94a3b8 !important;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if 'mode' not in st.session_state:
    st.session_state.mode = 'setup' 

# --- 1. SETUP SCREEN ---
if st.session_state.mode == 'setup':
    st.markdown("## Podium Setup (v3 - Nuclear Edition)")
    col1, col2 = st.columns(2)
    with col1:
        selected_class = st.selectbox("Select Class", list(CLASS_CALENDARS.keys()))
        cal_url = CLASS_CALENDARS[selected_class]
        agenda_text = st.text_area("Today's Agenda", height=150, value="Freewrite\nDiscussion\nGroup Work")
    with col2:
        st.subheader("Tech-Free Writing")
        is_tfw = st.checkbox("Is today a TFW day?", value=True)
        if is_tfw:
            tfw_prompt = st.text_area("Writing Prompt", height=100, value="What's on your mind today?")
            tfw_minutes = st.number_input("Duration (minutes)", value=7, min_value=1)
        else:
            tfw_prompt = ""
            tfw_minutes = 0

    if st.button("Launch Welcome Screen", type="primary", use_container_width=True):
        st.session_state.update({
            "cal_url": cal_url, "agenda": agenda_text, "is_tfw": is_tfw,
            "tfw_prompt": tfw_prompt, "tfw_minutes": tfw_minutes, "mode": "welcome"
        })
        st.rerun()

# --- 2. WELCOME SCREEN ---
elif st.session_state.mode == 'welcome':
    col_left, col_right = st.columns([0.8, 1.2], gap="large") 

    with col_left:
        st.markdown("<div class='dashboard-title'>Hello</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='dashboard-subtitle'>{datetime.now().strftime('%A, %b %d')}</div>", unsafe_allow_html=True)
        
        if st.session_state.is_tfw:
            st.markdown(f"<div class='tfw-notice'><strong>TFW Today:</strong> Prepare your journal.</div>", unsafe_allow_html=True)
            if st.button("Start Writing Session"):
                st.session_state.mode = 'focus'
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Edit Setup"):
            st.session_state.mode = 'setup'
            st.rerun()

    with col_right:
        # Agenda Card
        items = "".join([f"<li>{l.strip()}</li>" for l in st.session_state.agenda.split('\n') if l.strip()])
        st.markdown(f"<div class='glass-card'><div class='card-header'>Agenda</div><ul class='card-list'>{items}</ul></div>", unsafe_allow_html=True)

        # Upcoming Card (smaller font-size forced inline)
        upcoming_evs = []
        if st.session_state.cal_url:
            try:
                r = requests.get(st.session_state.cal_url)
                if r.status_code == 200:
                    c = Calendar(r.text)
                    now = datetime.now().date()
                    events = sorted([e for e in c.events if now <= e.begin.date() <= (now + timedelta(days=7))], key=lambda x: x.begin)
                    for e in events:
                        day = "Today" if e.begin.date() == now else e.begin.date().strftime('%a')
                        upcoming_evs.append(f"<li style='font-size: 2.5vw !important;'>{e.name} <span style='color:#38bdf8; opacity:0.8;'>({day})</span></li>")
            except: pass
        
        if upcoming_evs:
            up_list = "".join(upcoming_evs)
            st.markdown(f"<div class='glass-card'><div class='card-header'>Upcoming</div><ul class='card-list'>{up_list}</ul></div>", unsafe_allow_html=True)

# --- 3. FOCUS MODE ---
elif st.session_state.mode == 'focus':
    if st.button("Exit"):
        st.session_state.mode = 'welcome'
        st.rerun()

    prompt = st.session_state.tfw_prompt
    mins = st.session_state.tfw_minutes
    
    focus_html = f"""
    <div style="color:white; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; height:90vh; justify-content:center; text-align:center;">
        <div style="font-size:6vw; margin-bottom:5vh; font-weight:300; width:90%; color:#ffffff;">{prompt}</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:3vw; width:95%;">
            <div style="background:rgba(255,255,255,0.05); padding:3vw; border-radius:12px; border:1px solid rgba(56,189,248,0.2);">
                <div style="color:#38bdf8; font-size:2vw; text-transform:uppercase; margin-bottom:1vh;">Status</div>
                <div style="font-size:3vw;">Tech-Free</div>
            </div>
            <div style="background:rgba(255,255,255,0.05); padding:3vw; border-radius:12px; border:1px solid rgba(56,189,248,0.2);">
                <div style="color:#38bdf8; font-size:2vw; text-transform:uppercase; margin-bottom:1vh;">Time Remaining</div>
                <div id="t" style="font-size:6vw; color:#7dd3fc; font-weight:bold;">{mins}:00</div>
            </div>
        </div>
    </div>
    <script>
        let s = {mins} * 60;
        const display = document.getElementById('t');
        setInterval(() => {{
            if (s > 0) s--;
            let m = Math.floor(s/60);
            let sec = s % 60;
            display.innerText = m + ":" + (sec < 10 ? "0" + sec : sec);
            if (s < 60) display.style.color = "#facc15";
        }}, 1000);
    </script>
    """
    components.html(focus_html, height=850)
