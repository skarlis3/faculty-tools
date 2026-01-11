import streamlit as st
from ics import Calendar
from datetime import datetime, timedelta
import requests
import time

# --- PRIVATE CONFIGURATION ---
# Your specific class calendars
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

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .dashboard-title { font-size: 4em; font-weight: bold; color: #ffffff; margin-bottom: 0px; }
    .dashboard-subtitle { font-size: 1.5em; color: #aaaaaa; margin-bottom: 30px; }
    .agenda-box { background-color: #1E1E1E; border-left: 6px solid #00FF00; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
    .calendar-box { background-color: #1E1E1E; border-left: 6px solid #00AAFF; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
    .tfw-alert { background-color: #333300; border: 2px solid #FFD700; color: #FFD700; padding: 15px; text-align: center; font-size: 1.5em; font-weight: bold; border-radius: 10px; margin-top: 20px; }
    .focus-prompt { font-size: 2.8em; color: #ffffff; text-align: center; margin-top: 40px; margin-bottom: 40px; font-weight: bold; }
    .focus-timer { font-size: 3.5em; color: #88c0d0; text-align: center; font-family: 'Segoe UI', sans-serif; font-weight: 300; margin-top: 20px; }
    .focus-rules { font-size: 1.3em; color: #888; text-align: center; line-height: 1.8; margin-top: 50px; }
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
    st.header("🛠️ Classroom Setup")
    
    col1, col2 = st.columns(2)
    with col1:
        # Dropdown for Class Calendar
        selected_class = st.selectbox("Select Class:", list(CLASS_CALENDARS.keys()))
        cal_url = CLASS_CALENDARS[selected_class]
        
        agenda_text = st.text_area("Today's Agenda:", height=150, 
                                   value="• Quick Write\n• Discuss Reading\n• Group Work\n• Break")
    
    with col2:
        st.subheader("Tech-Free Writing")
        is_tfw = st.checkbox("Is today a TFW day?", value=True)
        
        if is_tfw:
            tfw_prompt = st.text_area("Prompt (Saved for later):", height=100, 
                                      value="What is a memory you have that feels like a ghost?")
            tfw_minutes = st.number_input("Duration (minutes):", value=10, min_value=1)
        else:
            tfw_prompt = ""
            tfw_minutes = 0

    st.write("")
    if st.button("🚀 Launch Welcome Screen", type="primary", use_container_width=True):
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
        st.markdown(f"<div class='dashboard-subtitle'>{datetime.now().strftime('%A, %B %d')}</div>", unsafe_allow_html=True)
    with c2:
        if st.button("⚙️ Edit Setup"):
            st.session_state.mode = 'setup'
            st.rerun()

    left_col, right_col = st.columns([1, 1])

    # LEFT: Agenda
    with left_col:
        st.markdown("### 📝 Today's Agenda")
        agenda_html = "".join([f"<li>{line.strip()}</li>" for line in st.session_state.agenda.split('\n') if line.strip()])
        st.markdown(f"<div class='agenda-box'><ul style='font-size: 1.3em; line-height: 1.6;'>{agenda_html}</ul></div>", unsafe_allow_html=True)
        
        if st.session_state.is_tfw:
            st.markdown("""
            <div class='tfw-alert'>
                📓 TECH-FREE WRITING TODAY<br>
                <span style='font-size:0.6em; font-weight:normal'>Please grab your TFW Journal and a pen.</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            if st.button("Start TFW Session ➡️", type="primary", use_container_width=True):
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
            except:
                pass

        st.markdown("### 📅 Today's Plan")
        if today_evs:
            today_html = "".join([f"<li>{x}</li>" for x in today_evs])
            st.markdown(f"<div class='calendar-box'><ul style='font-size: 1.2em;'>{today_html}</ul></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='calendar-box' style='color:#666'>No specific calendar events today.</div>", unsafe_allow_html=True)

        st.markdown("### 🔮 Due Next Week")
        if upcoming_evs:
            up_html = "".join([f"<li>{x}</li>" for x in upcoming_evs])
            st.markdown(f"<div class='calendar-box' style='border-left-color: #FFA500'><ul style='font-size: 1.2em;'>{up_html}</ul></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='calendar-box' style='color:#666; border-left-color: #FFA500'>No upcoming deadlines found.</div>", unsafe_allow_html=True)

# --- 3. FOCUS MODE ---
elif st.session_state.mode == 'focus':
    c1, c2 = st.columns([9, 1])
    with c1: st.write("")
    with c2: 
        if st.button("❌ Exit"):
            st.session_state.mode = 'welcome'
            st.rerun()

    st.markdown(f"<div class='focus-prompt'>{st.session_state.tfw_prompt}</div>", unsafe_allow_html=True)

    timer_placeholder = st.empty()
    st.markdown("""
    <div class='focus-rules'>
        • Put all technology away.<br>
        • Keep your pen moving the entire time.<br>
        • If you get stuck, write "I am stuck" until a new thought comes.
    </div>
    """, unsafe_allow_html=True)

    total_sec = st.session_state.tfw_minutes * 60
    progress_bar = st.progress(0)
    
    for i in range(total_sec, -1, -1):
        fuzzy_text = get_fuzzy_time(i)
        color = "#88c0d0"
        if i < 60: color = "#ebcb8b"
        
        timer_placeholder.markdown(f"<div class='focus-timer' style='color:{color}'>{fuzzy_text}</div>", unsafe_allow_html=True)
        progress_bar.progress((total_sec - i) / total_sec)
        time.sleep(1)
        
    st.balloons()
