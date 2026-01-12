import streamlit as st
import streamlit.components.v1 as components
from ics import Calendar
from datetime import datetime, timedelta
import requests
import json

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

# --- GLOBAL CSS ---
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #050a10; 
        background-image: radial-gradient(circle at 0% 0%, #111a2e 0%, #050a10 60%);
    }
    
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, sans-serif;
        font-weight: 300;
        color: #e6edf3;
    }
    
    /* GLASS CARDS (Welcome Screen) */
    .glass-card { 
        background: rgba(13, 17, 23, 0.6); 
        backdrop-filter: blur(12px); 
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.2); 
        border-radius: 12px; 
        padding: 25px; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
    }
    
    /* HEADERS */
    .dashboard-title { 
        font-size: 5em; 
        font-weight: 200; 
        color: #ffffff; 
        margin-top: -20px; 
        margin-bottom: 0px; 
        letter-spacing: -1px;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.2);
    }
    
    .dashboard-subtitle { 
        font-size: 2em; 
        color: #38bdf8; 
        margin-bottom: 50px; 
        font-weight: 500;
        letter-spacing: 1px;
    }
    
    .card-header {
        font-size: 1.1em;
        color: #38bdf8; 
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
        padding-bottom: 8px;
    }
    
    .card-list {
        font-size: 1.1em; /* UPDATED: Changed from 1.3em to 1.1em */
        line-height: 1.6;
        color: #e6edf3;
        list-style-position: inside;
        padding-left: 5px;
    }
    
    /* TFW Notice Box */
    .tfw-notice { 
        background: linear-gradient(90deg, rgba(3, 105, 161, 0.2) 0%, rgba(3, 105, 161, 0.05) 100%);
        border-left: 4px solid #0284c7; 
        color: #e0f2fe; 
        padding: 20px; 
        margin-top: 10px; 
        border-radius: 0 8px 8px 0;
        font-size: 1.2em;
    }
    
    /* BUTTONS: GHOST STYLE */
    div.stButton > button {
        background: transparent !important;
        color: rgba(56, 189, 248, 0.7) !important; 
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 4px;
        padding: 6px 15px;
        font-weight: 300;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.8em;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        border-color: #38bdf8 !important;
        color: #ffffff !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if 'mode' not in st.session_state:
    st.session_state.mode = 'setup' 

# --- 1. SETUP SCREEN ---
if st.session_state.mode == 'setup':
    st.markdown("## Podium Setup")
    col1, col2 = st.columns(2)
    with col1:
        selected_class = st.selectbox("Select Class", list(CLASS_CALENDARS.keys()))
        cal_url = CLASS_CALENDARS[selected_class]
        agenda_text = st.text_area("Today's Agenda", height=150, value="Freewrite\nTopic\nTopic")
    with col2:
        st.subheader("Tech-Free Writing")
        is_tfw = st.checkbox("Is today a TFW day?", value=True)
        if is_tfw:
            tfw_prompt = st.text_area("Writing Prompt", height=100, value="Write about whatever is in your head right now—stress, lunch plans, traffic, or your to-do list. ")
            tfw_minutes = st.number_input("Duration (minutes)", value=7, min_value=1)
        else:
            tfw_prompt = ""
            tfw_minutes = 0

    st.write("")
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
    left_col, right_col = st.columns([1.5, 1], gap="large")

    with left_col:
        st.markdown(f"<div class='dashboard-title'>Welcome to Class</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='dashboard-subtitle'>{datetime.now().strftime('%A, %B %d')}</div>", unsafe_allow_html=True)
        
        if st.session_state.is_tfw:
            st.markdown("""<div class='tfw-notice'><strong>Tech-Free Writing Today &nbsp</strong>Please get your TFW journal and make sure you have a pen/pencil.</div>""", unsafe_allow_html=True)
            st.write(""); st.write("")
            if st.button("Start Writing Session"):
                st.session_state.mode = 'focus'
                st.rerun()

        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        if st.button("Edit Setup"):
            st.session_state.mode = 'setup'
            st.rerun()

    with right_col:
        agenda_items = "".join([f"<li>{line.strip()}</li>" for line in st.session_state.agenda.split('\n') if line.strip()])
        st.markdown(f"<div class='glass-card'><div class='card-header'>Today's Agenda</div><ul class='card-list'>{agenda_items}</ul></div>", unsafe_allow_html=True)

        upcoming_evs = []
        if st.session_state.cal_url:
            try:
                r = requests.get(st.session_state.cal_url)
                if r.status_code == 200:
                    c = Calendar(r.text)
                    now = datetime.now().date()
                    sorted_events = sorted(list(c.events), key=lambda x: x.begin)
                    for e in sorted_events:
                        edate = e.begin.date()
                        if now <= edate <= (now + timedelta(days=7)):
                            day_label = "Today" if edate == now else edate.strftime('%a')
                            # UPDATED: Removed explicit font-size so it inherits 1.1em from parent
                            upcoming_evs.append(f"{e.name} <span style='color:#38bdf8; font-weight:600; margin-left:8px;'>({day_label})</span>")
            except: pass
        
        up_content = f"<ul class='card-list'>{''.join([f'<li>{x}</li>' for x in upcoming_evs])}</ul>" if upcoming_evs else "<div style='color:#94a3b8; font-style:italic;'>No upcoming deadlines found.</div>"
        st.markdown(f"<div class='glass-card'><div class='card-header'>Upcoming</div>{up_content}</div>", unsafe_allow_html=True)

# --- 3. FOCUS MODE (JAVASCRIPT VERSION) ---
elif st.session_state.mode == 'focus':
    c1, c2 = st.columns([11, 1])
    with c1: st.write("")
    with c2: 
        if st.button("Exit"):
            st.session_state.mode = 'welcome'
            st.rerun()

    total_minutes = st.session_state.tfw_minutes
    prompt_text = st.session_state.tfw_prompt
    
    # HTML/JS Code Block
    focus_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            background-color: transparent;
            font-family: 'Segoe UI', Roboto, sans-serif;
            color: white;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 800px;
        }}
        .prompt {{
            font-size: 2.5em;
            color: #ffffff;
            text-align: center;
            margin-top: 50px;
            margin-bottom: 60px;
            font-weight: 300;
            width: 80%;
            line-height: 1.3;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            width: 90%;
            max-width: 1200px;
        }}
        .card {{
            background: rgba(13, 17, 23, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 12px;
            padding: 30px;
            height: 300px;
            /* Top Align */
            display: flex;
            flex-direction: column;
            justify-content: flex-start; 
            position: relative;
        }}
        .card-header {{
            font-size: 1.1em;
            color: #38bdf8;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 1px solid rgba(56, 189, 248, 0.2);
            padding-bottom: 10px;
            position: absolute;
            top: 25px;
            left: 30px;
            right: 30px;
        }}
        .content-box {{
            margin-top: 60px; /* Push content down below header */
        }}
        
        /* Reminders Text */
        ul {{
            font-size: 1.25em; /* Lighter sizing */
            font-weight: 200; /* Thin font */
            color: #e2e8f0;
            line-height: 1.6;
            padding-left: 20px;
            margin: 0;
        }}
        
        /* Timer Text */
        #timer {{
            font-size: 1.2em; /* Small */
            font-weight: 200; /* Thin */
            color: #7dd3fc;
            text-align: center;
            opacity: 0.7; /* Background focus */
            margin-top: 80px; /* Push down to center-ish */
        }}
        
        #progress-container {{
            width: 100%;
            background-color: rgba(56, 189, 248, 0.1);
            height: 4px; /* Thinner bar */
            border-radius: 2px;
            margin-top: 20px;
            overflow: hidden;
        }}
        #progress-bar {{
            height: 100%;
            background-color: #0ea5e9;
            width: 0%;
            transition: width 1s linear;
        }}
    </style>
    </head>
    <body>
        <div class="prompt">{prompt_text}</div>
        
        <div class="grid">
            <div class="card">
                <div class="card-header">Reminders</div>
                <div class="content-box">
                    <ul>
                        <li>Put all technology away.</li>
                        <li>Keep your pen moving.</li>
                        <li>If stuck, write "I am stuck".</li>
                    </ul>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">Time Remaining</div>
                <div class="content-box">
                    <div id="timer">Loading...</div>
                    <div id="progress-container">
                        <div id="progress-bar"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const totalMinutes = {total_minutes};
            const totalSeconds = totalMinutes * 60;
            let remaining = totalSeconds;
            
            function getFuzzy(seconds) {{
                let minutes = seconds / 60;
                if (minutes >= 5) return "About " + Math.round(minutes) + " minutes";
                if (minutes >= 3.5) return "About 4 minutes";
                if (minutes >= 2.75) return "About 3 minutes";
                if (minutes >= 2.25) return "About 2.5 minutes";
                if (minutes >= 1.75) return "About 2 minutes";
                if (minutes >= 1.25) return "About 1.5 minutes";
                if (minutes >= 0.75) return "About 1 minute";
                if (minutes > 0) return "< 1 minute";
                return "Time is up";
            }}

            const timerEl = document.getElementById('timer');
            const barEl = document.getElementById('progress-bar');
            
            const interval = setInterval(() => {{
                remaining--;
                timerEl.innerText = getFuzzy(remaining);
                
                if (remaining < 60) {{
                    timerEl.style.color = "#facc15"; 
                }}

                const pct = ((totalSeconds - remaining) / totalSeconds) * 100;
                barEl.style.width = pct + "%";

                if (remaining <= 0) {{
                    clearInterval(interval);
                    timerEl.innerText = "Time is up";
                    barEl.style.width = "100%";
                }}
            }}, 1000);
            
            timerEl.innerText = getFuzzy(remaining);
        </script>
    </body>
    </html>
    """
    
    components.html(focus_html, height=850, scrolling=False)
