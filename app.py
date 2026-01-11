import streamlit as st
from ics import Calendar
from datetime import datetime, timedelta
import re
import random
from io import StringIO
import zipfile
import io
from collections import defaultdict

# --- PAGE SETUP ---
st.set_page_config(page_title="Faculty Toolkit", page_icon="🎓", layout="wide")

st.title("🎓 Faculty Tools")
st.markdown("One-stop shop for Syllabus Schedules and Door Signs.")

# --- SIDEBAR NAVIGATION ---
tool_choice = st.sidebar.radio("Select Tool:", ["📅 Syllabus Scheduler", "🚪 Door Sign Generator"])

# ==========================================
# TOOL 1: SYLLABUS SCHEDULER
# ==========================================
if tool_choice == "📅 Syllabus Scheduler":
    st.header("Syllabus Schedule Generator")
    st.info("Upload your Canvas .ics file to generate a clean HTML schedule.")

    # 1. Inputs
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("First Day of Semester", value=datetime(2026, 1, 6))
        class_number = st.text_input("Class Number (e.g. 1190)", value="1190")
    with col2:
        class_format = st.selectbox("Format", ["In-Person", "Hybrid", "Online"])
        
    st.write(" **Meeting Days (for In-Person/Hybrid):**")
    d_col1, d_col2, d_col3, d_col4, d_col5 = st.columns(5)
    meet_mon = d_col1.checkbox("Mon", value=False)
    meet_tue = d_col2.checkbox("Tue", value=True)
    meet_wed = d_col3.checkbox("Wed", value=False)
    meet_thu = d_col4.checkbox("Thu", value=False)
    meet_fri = d_col5.checkbox("Fri", value=False)

    valid_days = []
    if meet_mon: valid_days.append(0)
    if meet_tue: valid_days.append(1)
    if meet_wed: valid_days.append(2)
    if meet_thu: valid_days.append(3)
    if meet_fri: valid_days.append(4)

    # 2. File Upload
    uploaded_file = st.file_uploader("Upload .ics file", type="ics")

    if uploaded_file is not None:
        # Process File
        c = Calendar(uploaded_file.read().decode("utf-8"))
        
        # Filter events
        semester_events = [e for e in c.events if e.begin.date() >= start_date]
        semester_events.sort(key=lambda x: x.begin)
        
        # --- HTML GENERATION (Your Logic) ---
        html_output = []
        
        # CSS Block
        css_block = f"""
        <style>
            .syllabus-container {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; color: #222; line-height: 1.6; }}
            .info-box {{ border: 2px solid #ddd; background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; border-radius: 8px; }}
            .week-card {{ border: 2px solid #ddd; background-color: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .week-header {{ font-size: 1.25em; font-weight: bold; color: #004494; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }}
            .day-row {{ display: flex; border-bottom: 1px solid #eee; padding: 12px 0; align-items: baseline; }}
            .date-col {{ flex: 0 0 160px; font-weight: bold; color: #004494; }}
            .content-col {{ flex: 1; }}
            .list-clean {{ list-style-type: none; padding: 0; margin: 0; }}
            .list-item {{ margin-bottom: 8px; padding-left: 0; }}
            .type-deadline {{ color: #222; }} 
            .type-reminder {{ font-style: italic; color: #444; }}
            .type-topic {{ color: #111; }}
            .cal-link {{ color: #004494; text-decoration: underline; }}
        </style>
        """
        html_output.append(css_block)
        html_output.append("<div class='syllabus-container'>")
        html_output.append(f"""
        <div class='info-box'>
            <strong>Subject to Change:</strong> This schedule is a guide. 
            For the most up-to-date dates, please verify on the 
            <a href='https://{class_number}.skarlis.org/calendar/' class='cal-link' target='_blank'>Class Calendar</a>.
        </div>
        """)

        # Helper Functions
        def clean_title(name): return re.sub(r'\[.*?\]', '', name).strip()
        def get_event_type(name):
            if "due" in name.lower(): return "deadline"
            elif "reminder" in name.lower(): return "reminder"
            return "topic"
        def get_week_label(ev_date, start, week_evs):
            for e in week_evs:
                if "spring break" in e.name.lower() or "no class" in e.name.lower(): return "Break"
            days_diff = (ev_date - start).days
            return f"Week {(days_diff // 7) + 1}"

        # Logic Branching
        if class_format in ["Hybrid", "Online"]:
            # Group by Week
            events_by_week = defaultdict(list)
            for e in semester_events:
                monday = e.begin.date() - timedelta(days=e.begin.date().weekday())
                events_by_week[monday].append(e)
            
            for week_start in sorted(events_by_week.keys()):
                week_events = events_by_week[week_start]
                label = get_week_label(week_start, start_date, week_events)
                end_week = week_start + timedelta(days=4)
                
                display_label = f"🍂 {label} / No Class" if "Break" in label else f"{label}: {week_start.strftime('%b %d')} – {end_week.strftime('%b %d')}"
                
                html_output.append(f"<div class='week-card'><div class='week-header'>{display_label}</div>")
                
                in_person, remote = [], []
                for e in week_events:
                    clean = clean_title(e.name)
                    etype = get_event_type(clean)
                    item_html = f"<li class='list-item type-{etype}'>{clean}</li>"
                    
                    if class_format == "Hybrid" and e.begin.weekday() in valid_days and etype == "topic":
                        in_person.append(item_html)
                    else:
                        remote.append(item_html)

                if class_format == "Hybrid" and in_person:
                    html_output.append(f"<strong style='color:#004494; display:block; margin-bottom:5px;'>In-Person Meeting:</strong>")
                    html_output.append(f"<ul class='list-clean'>{''.join(in_person)}</ul>")
                    html_output.append(f"<div style='margin-top:15px; margin-bottom:5px;'><strong>Remote / Deadlines:</strong></div>")
                
                if remote: html_output.append(f"<ul class='list-clean'>{''.join(remote)}</ul>")
                html_output.append("</div>")

        else:
            # Group by Day (In Person)
            daily_groups = defaultdict(list)
            for e in semester_events: daily_groups[e.begin.date()].append(e)
            
            html_output.append("<div role='list'>")
            for d_key in sorted(daily_groups.keys()):
                day_events = daily_groups[d_key]
                date_str = day_events[0].begin.format('ddd, MMM D')
                content_html = ""
                for e in day_events:
                    clean = clean_title(e.name)
                    etype = get_event_type(clean)
                    content_html += f"<div class='type-{etype}' style='margin-bottom: 6px;'>{clean}</div>"
                
                html_output.append(f"<div class='day-row'><div class='date-col'>{date_str}</div><div class='content-col'>{content_html}</div></div>")
            html_output.append("</div>")
        
        html_output.append("</div>")
        final_html = "\n".join(html_output)
        
        # Download Button
        st.success("✅ Syllabus Generated!")
        st.download_button("Download HTML Syllabus", data=final_html, file_name=f"syllabus_{class_number}.html", mime="text/html")

# ==========================================
# TOOL 2: DOOR SIGN GENERATOR
# ==========================================
elif tool_choice == "🚪 Door Sign Generator":
    st.header("Visual Faculty Door Sign")
    st.markdown("Generates a clean, print-friendly grid (Mon-Fri, 9am-8pm).")

    # Inputs
    raw_schedule = st.text_area("1. Paste Class Schedule (from software):", height=150, placeholder="2026 Winter Term\nENGL-1190...")
    oh_text = st.text_input("2. Office Hours (e.g., 'Mon/Wed 11-12, Virtual: Tue 5-6'):")
    title_text = st.text_input("3. Page Title:", value="Winter 2026 Schedule")

    if st.button("Generate Door Sign"):
        # --- PARSING LOGIC ---
        def get_minutes(time_str):
            time_str = time_str.upper().strip()
            if ':' not in time_str:
                try:
                    val = int(time_str)
                    if val == 12: return 12 * 60
                    if 1 <= val <= 7: return (val + 12) * 60
                    return val * 60
                except: return 0
            try:
                parts = re.split('[: ]+', time_str)
                h, m = int(parts[0]), int(parts[1])
                is_pm = 'PM' in time_str
                if is_pm and h != 12: h += 12
                if not is_pm and h == 12: h = 0
                return h * 60 + m
            except: return 0

        events = []
        # Parse Classes
        lines = raw_schedule.split('\n')
        current_class = None
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith("ENGL-"):
                match = re.search(r'(ENGL-\d+)', line)
                current_class = match.group(1).replace("-", " ") if match else "Class"
            
            t_match = re.search(r'([MTWRFS/]+)\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)', line)
            if t_match and current_class:
                days = t_match.group(1).split('/')
                loc = "Remote" if "Remote" in line else "In-Person"
                events.append({"type": "class", "name": current_class, "days": days, "start": get_minutes(t_match.group(2)), "end": get_minutes(t_match.group(3)), "loc": ""})

        # Parse OH
        day_map = {'Mon': 'M', 'Tue': 'T', 'Wed': 'W', 'Thu': 'Th', 'Fri': 'F'}
        for part in oh_text.split(','):
            part = part.strip()
            if not part: continue
            is_virtual = "virtual" in part.lower()
            found_days = [dcode for dname, dcode in day_map.items() if dname in part or dname.lower() in part.lower()]
            nums = re.findall(r'\d+', part)
            if len(nums) >= 2:
                s_raw, e_raw = int(nums[0]), int(nums[1])
                s_min, e_min = s_raw * 60, e_raw * 60
                if s_raw < 9: s_min += 12*60
                if e_raw < 9: e_min += 12*60
                if e_raw < s_raw: e_min += 12*60
                events.append({"type": "oh", "name": "Virtual Office Hours" if is_virtual else "Office Hours", "days": found_days, "start": s_min, "end": e_min, "loc": ""})

        # --- HTML GENERATION (Clean Print Style) ---
        start_hr, end_hr = 9, 20
        total_slots = (end_hr - start_hr) * 4
        colors_cool = ["#e8f4f8", "#e3f2fd", "#e0f2f1", "#f3e5f5"]
        colors_warm = ["#fff8e1", "#fff3e0", "#fbe9e7"]
        color_map = {}
        
        html_events = ""
        col_map = {"M": 2, "T": 3, "W": 4, "Th": 5, "F": 6}
        
        for ev in events:
            start_offset = ev['start'] - (start_hr * 60)
            end_offset = ev['end'] - (start_hr * 60)
            if start_offset < 0: continue
            
            row_start = int(start_offset / 15) + 2
            row_span = int((end_offset - start_offset) / 15)
            if row_span < 1: row_span = 1
            
            if ev['type'] == 'class':
                if ev['name'] not in color_map: color_map[ev['name']] = random.choice(colors_cool)
                bg, border = color_map[ev['name']], "#546e7a"
            else:
                bg, border = random.choice(colors_warm), "#d84315"
                
            for d in ev['days']:
                if d in col_map:
                    html_events += f"""
                    <div class="event" style="grid-column: {col_map[d]}; grid-row: {row_start} / span {row_span}; background: {bg}; border-left: 4px solid {border}; color: #000;">
                        <strong>{ev['name']}</strong><br>{ev['loc']}
                    </div>"""
        
        html_times = ""
        for h in range(start_hr, end_hr + 1):
            r = (h - start_hr) * 4 + 2
            label = f"{h%12 or 12} {('AM' if h<12 else 'PM')}"
            html_times += f'<div class="time-label" style="grid-row: {r};">{label}</div><div class="grid-line" style="grid-row: {r};"></div>'

        final_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #fff; padding: 20px; }}
                h1 {{ text-align: center; color: #000; font-weight: normal; font-size: 28px; margin-bottom: 30px; text-transform: uppercase; letter-spacing: 1px; }}
                .calendar {{ display: grid; grid-template-columns: 60px repeat(5, 1fr); grid-template-rows: 40px repeat({total_slots}, 1fr); border-top: 2px solid #333; border-bottom: 2px solid #333; height: 900px; width: 100%; max-width: 1000px; margin: 0 auto; background: #fff; background-image: linear-gradient(to right, transparent 60px, #eee 61px, transparent 61px, transparent calc(60px + 20%), #eee calc(60px + 20% + 1px), transparent calc(60px + 20% + 1px), transparent calc(60px + 40%), #eee calc(60px + 40% + 1px), transparent calc(60px + 40% + 1px), transparent calc(60px + 60%), #eee calc(60px + 60% + 1px), transparent calc(60px + 60% + 1px), transparent calc(60px + 80%), #eee calc(60px + 80% + 1px), transparent calc(60px + 80% + 1px)); }}
                .header {{ background: #fff; color: #000; font-weight: normal; text-align: center; padding-top: 10px; font-size: 18px; border-bottom: 1px solid #ccc; }}
                .time-label {{ grid-column: 1; font-size: 11px; color: #444; text-align: right; padding-right: 10px; transform: translateY(-50%); }}
                .grid-line {{ grid-column: 2 / span 5; border-top: 1px solid #eee; height: 0; }}
                .event {{ margin: 2px; padding: 4px; font-size: 12px; border-radius: 0px; overflow: hidden; z-index: 2; line-height: 1.3; }}
            </style>
        </head>
        <body>
            <h1>{title_text}</h1>
            <div class="calendar">
                <div class="header" style="grid-column:1"></div><div class="header">Mon</div><div class="header">Tue</div><div class="header">Wed</div><div class="header">Thu</div><div class="header">Fri</div>
                {html_times}
                {html_events}
            </div>
        </body>
        </html>
        """
        
        st.success("✅ Door Sign Generated!")
        st.download_button("Download Door Sign HTML", data=final_html, file_name="door_sign.html", mime="text/html")
        
        # Preview
        st.write("Preview:")
        st.components.v1.html(final_html, height=600, scrolling=True)
