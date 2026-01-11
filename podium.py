import streamlit as st
from ics import Calendar
from datetime import datetime, timedelta
import requests
import time

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
st.set_page_config(page_title="Classroom Podium", page_icon="💻", layout="wide")

# --- AERO / GLASS CSS ---
st.markdown("""
<style>
    /* Global Background & Font */
    .stApp {
        background-color: #0d1117; /* Very Dark Blue/Grey */
        background-image: radial-gradient(circle at 50% 0%, #1f2937 0%, #0d1117 70%);
    }
    
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, sans-serif;
        font-weight: 300;
        color: #e6edf3;
    }
    
    /* GLASSMOPRHISM CARD (Aero Style) */
    .glass-card { 
        background: rgba(255, 255, 255, 0.05); /* Very transparent */
        backdrop-filter: blur(12px); /* frosted glass effect */
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle white border */
        border-radius: 12px; 
        padding: 25px; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    
    /* HEADERS */
    .dashboard-title { 
        font-size: 4em; 
        font-weight: 200; 
        color: #ffffff; 
        margin-bottom: 0px; 
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(255,255,255,0.1);
    }
    
    /* Date Highlight - Make it Pop */
    .dashboard-subtitle { 
        font-size: 1.8em; 
        color: #7dd3fc; /* Bright Sky Blue */
        margin-bottom: 40px; 
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .card-header {
        font-size: 1.1em;
        color: #a5d6ff; /* Soft Blue */
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 8px;
    }
    
    .card-list {
        font-size: 1.3em;
        line-height: 1.6;
        color: #c9d1d9;
        list-style-position: inside;
        padding-left: 5px;
    }
    
    /* TFW Notice Box */
    .tfw-notice { 
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.1) 0%, rgba(56, 189, 248, 0.02) 100%);
        border-left: 4px solid #38bdf8; 
        color: #e0f2fe; 
        padding: 20px; 
        margin-top: 20px; 
        border-radius: 0 8px 8px 0;
    }

    /* CUSTOM BUTTON STYLING (Teal/Blue Gradient, No Red) */
    div.stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
        border-color: transparent;
    }

    /* PROGRESS BAR COLOR OVERRIDE */
    .stProgress > div > div > div > div {
        background-color: #38bdf8; /* Sky Blue bar */
    }

    /* --- FOCUS MODE --- */
    /* Vertical Center Wrapper */
    .focus-container {
        margin-top: 15vh; /* Pushes content down significantly */
    }

    .focus-prompt { 
        font-size: 2.2em; 
        color: #ffffff; 
        text-align: center; 
        margin-bottom: 50px; 
        font-weight: 300; 
        line-height: 1.4;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    
    /* Reminder List - Lighter Text */
    .rules-list {
        font-size: 1.3em; 
        color: #94a3b8; /* Slate-400 (Lighter Grey/Blue) */
        line-height: 2.0; 
        text-align: left;
    }
    
    /* Timer Text - Smaller & Softer */
    .focus-timer-text { 
        font-size: 2em; /* Smaller than before */
        color: #7dd3fc; /* Soft Blue */
        text-align: center; 
        font-weight: 300; 
        margin-bottom: 10px;
    }

</style>
""", unsafe_allow_html=True)

# Helper for Fuzzy Time
def get_fuzzy_time(seconds_left):
    minutes = seconds_left / 60
    if minutes >= 5: return f"About {int(round(minutes))} minutes remaining"
    elif 3.5 <= minutes < 5: return "About four minutes remaining"
    elif 2.75 <= minutes < 3.5: return "About three minutes remaining"
    elif 2.25 <= minutes < 2.75: return "About two and a half minutes remaining"
    elif 1.75 <= minutes < 2.25: return "About two minutes remaining"
    elif 1.25 <= minutes < 1.75: return "About a minute and a half remaining"
    elif 0.75 <= minutes < 1.25: return "About one minute remaining"
    elif 0 < minutes < 0.75: return "Less than a minute remaining"
    else: return "Time is up"

if 'mode' not in st.session_state:
    st.session_state.mode = 'setup' 

# --- 1. SETUP SCREEN ---
if st.session_state.mode == 'setup':
    st.markdown("## 🛠️ Podium Setup")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_class = st.selectbox("Select Class", list(CLASS_CALENDARS.keys()))
        cal_url = CLASS_CALENDARS[selected_class]
        agenda_text = st.text_area("Today's Agenda", height=150, 
                                   value="Quick Write\nDiscuss Reading\nGroup Work\nBreak")
    
    with col2:
        st.subheader("Tech-Free Writing")
        is_tfw = st.checkbox("Is today a TFW day?", value=True)
        if is_tfw:
            tfw_prompt = st.text_area("Writing Prompt", height=100, 
                                      value="What is a memory you have that feels like a ghost?")
            tfw_minutes = st.number_input("Duration (minutes)", value=10, min_value=1)
        else:
            tfw_prompt = ""
            tfw_minutes = 0

    st.write("")
    # Primary button style handled by CSS injection above
    if st.button("Launch Welcome Screen", type="primary", use_container_width=True):
        st.session_state.cal_url = cal_url
        st.session_state.agenda = agenda_text
        st.session_state.is_tfw = is_tfw
        st.session_state.tfw_prompt = tfw_prompt
        st.session_state.tfw_minutes = tfw_minutes
        st.session_state.mode = 'welcome'
        st.rerun()

# --- 2. WELCOME SCREEN ---
elif st.session_state.mode == 'welcome':
    c1, c2 = st.columns([8, 2])
    with c1:
        st.markdown(f"<div class='dashboard-title'>Welcome to Class</div>", unsafe_allow_html=True)
        # Lighter, popping date
        st.markdown(f"<div class='dashboard-subtitle'>{datetime.now().strftime('%A, %B %d')}</div>", unsafe_allow_html=True)
    with c2:
        if st.button("Edit Setup"):
            st.session_state.mode = 'setup'
            st.rerun()

    left_col, right_col = st.columns([1, 1], gap="large")

    # LEFT: Agenda
    with left_col:
        agenda_items = "".join([f"<li>{line.strip()}</li>" for line in st.session_state.agenda.split('\n') if line.strip()])
        st.markdown(f"""
        <div class='glass-card'>
            <div class='card-header'>Today's Agenda</div>
            <ul class='card-list'>{agenda_items}</ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.is_tfw:
            st.markdown("""
            <div class='tfw-notice'>
                <strong>Tech-Free Writing Today</strong>
                Please prepare your journal and a pen.
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            if st.button("Start Writing Session", type="primary", use_container_width=True):
                st.session_state.mode = 'focus'
                st.rerun()

    # RIGHT: Calendar
    with right_col:
        today_evs, upcoming_evs = [], []
        if st.session_state.cal_url:
            try:
                r = requests.get(st.session_state.cal_url)
                if r.status_code == 200:
                    c = Calendar(r.text)
                    now = datetime.now().date()
                    sorted_events = sorted(list(c.events), key=lambda x: x.begin)
                    
                    for e in sorted_events:
                        edate = e.begin.date()
                        if edate == now:
                            today_evs.append(e.name)
                        elif now < edate <= (now + timedelta(days=7)):
                            upcoming_evs.append(f"{e.name} ({edate.strftime('%a')})")
            except: pass

        if today_evs:
            today_html = "".join([f"<li>{x}</li>" for x in today_evs])
            st.markdown(f"""
            <div class='glass-card'>
                <div class='card-header'>Today's Plan</div>
                <ul class='card-list'>{today_html}</ul>
            </div>""", unsafe_allow_html=True)
        
        if upcoming_evs:
            up_html = "".join([f"<li>{x}</li>" for x in upcoming_evs])
            st.markdown(f"""
            <div class='glass-card'>
                <div class='card-header'>Due Next Week</div>
                <ul class='card-list'>{up_html}</ul>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='glass-card'>
                <div class='card-header'>Due Next Week</div>
                <div style='color:#6c757d; font-style:italic;'>No upcoming deadlines found.</div>
            </div>""", unsafe_allow_html=True)

# --- 3. FOCUS MODE ---
elif st.session_state.mode == 'focus':
    # Top Right Exit
    c1, c2 = st.columns([11, 1])
    with c1: st.write("")
    with c2: 
        if st.button("Exit"):
            st.session_state.mode = 'welcome'
            st.rerun()

    # Vertical Spacer to center content
    st.markdown("<div class='focus-container'></div>", unsafe_allow_html=True)

    # Prompt
    st.markdown(f"<div class='focus-prompt'>{st.session_state.tfw_prompt}</div>", unsafe_allow_html=True)

    # Two Column Layout
    col_rules, col_timer = st.columns([1, 1], gap="large")

    # LEFT: Reminders (Glass Card)
    with col_rules:
        st.markdown("""
        <div class='glass-card'>
            <div class='card-header'>Reminders</div>
            <ul class='rules-list'>
                <li>Put all technology away.</li>
                <li>Keep your pen moving the entire time.</li>
                <li>If you get stuck, write "I am stuck" until a new thought comes.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # RIGHT: Timer (Glass Card)
    with col_timer:
        timer_placeholder = st.empty()
        
        # Timer Logic
        total_sec = st.session_state.tfw_minutes * 60
        progress_bar = st.progress(0)
        
        for i in range(total_sec, -1, -1):
            fuzzy_text = get_fuzzy_time(i)
            
            # Subtle color shift for text only
            color = "#bae6fd" # Very light blue
            if i < 60: color = "#fde047" # Soft yellow
            
            # Timer Display
            timer_placeholder.markdown(f"""
            <div class='glass-card' style='display:flex; flex-direction:column; justify-content:center; align-items:center; height:100%;'>
                <div class='focus-timer-text' style='color:{color}'>{fuzzy_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar.progress((total_sec - i) / total_sec)
            time.sleep(1)
            
        st.balloons()
