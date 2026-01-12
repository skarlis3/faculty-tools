import streamlit as st
from ics import Calendar
from datetime import datetime, timedelta
import re
import random
import requests

# --- PAGE SETUP ---
st.set_page_config(page_title="Faculty Tools", page_icon="💻", layout="wide")

st.title("🎓 Faculty Tools")
st.markdown("Tools to automate your syllabus, door signs, and calendar dates.")

# --- SIDEBAR NAVIGATION ---
tool_choice = st.sidebar.radio("Select Tool:", 
    ["📅 Syllabus Scheduler", "🚪 Door Sign Generator", "⏳ ICS Date Shifter"])

# ==========================================
# TOOL 1: SYLLABUS SCHEDULER
# ==========================================
if tool_choice == "📅 Syllabus Scheduler":
    st.header("Syllabus Schedule Generator")
    st.info("Upload your Canvas .ics file to generate a clean HTML schedule.")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("First Day of Semester", value=datetime(2026, 1, 12))
        class_number = st.text_input("Class Number (e.g. 1190)", value="1190")
    with col2:
        class_format = st.selectbox("Format", ["In-Person", "Hybrid", "Online"])
        
    st.write(" **Meeting Days (for In-Person/Hybrid):**")
    cols = st.columns(5)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    valid_days = [i for i, d in enumerate(days) if cols[i].checkbox(d, value=(d=="Tue"))]

    uploaded_file = st.file_uploader("Upload .ics file", type="ics", key="syl_upload")

    if uploaded_file:
        c = Calendar(uploaded_file.read().decode("utf-8"))
        events = sorted([e for e in c.events if e.begin.date() >= start_date], key=lambda x: x.begin)
        
        html_output = ["<div style='font-family: sans-serif; max-width: 800px; margin: 0 auto;'>"]
        
        if class_format in ["Hybrid", "Online"]:
            events_by_week = {}
            for e in events:
                monday = e.begin.date() - timedelta(days=e.begin.date().weekday())
                if monday not in events_by_week: events_by_week[monday] = []
                events_by_week[monday].append(e)
            
            for week_start in sorted(events_by_week.keys()):
                we = events_by_week[week_start]
                is_break = any("spring break" in x.name.lower() for x in we)
                week_num = ((week_start - start_date).days // 7) + 1
                label = f"🍂 Week {week_num} (Break)" if is_break else f"Week {week_num}: {week_start.strftime('%b %d')}"
                
                html_output.append(f"<div style='border:1px solid #ccc; padding:15px; margin-bottom:15px; border-radius:5px;'><h3>{label}</h3><ul>")
                for e in we:
                    etype = "color:#900; font-weight:bold;" if "due" in e.name.lower() else "color:#333;"
                    html_output.append(f"<li style='{etype}'>{e.name}</li>")
                html_output.append("</ul></div>")
        else:
            for e in events:
                html_output.append(f"<div style='border-bottom:1px solid #eee; padding:10px;'><strong>{e.begin.format('ddd, MMM D')}:</strong> {e.name}</div>")
        
        html_output.append("</div>")
        st.download_button("Download HTML", "\n".join(html_output), f"syllabus_{class_number}.html", "text/html")

# ==========================================
# TOOL 2: DOOR SIGN GENERATOR
# ==========================================
elif tool_choice == "🚪 Door Sign Generator":
    st.header("Visual Faculty Door Sign")
    st.markdown("Generates a clean, print-friendly grid (Mon-Fri, 9am-8pm).")

    raw_schedule = st.text_area("1. Paste Class Schedule (from software):", height=150, placeholder="2026 Winter Term\nENGL-1190-101 ... SF-310")
    oh_text = st.text_input("2. Office Hours (e.g., 'Mon/Wed 11-12, Virtual: Tue 5-6'):")
    title_text = st.text_input("3. Page Title:", value="Winter 2026 Schedule")

    if st.button("Generate Door Sign"):
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
        lines = raw_schedule.split('\n')
        current_class = None
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 1. Identify Class Name (ENGL-####)
            if line.startswith("ENGL-"):
                match = re.search(r'(ENGL-\d+)', line)
                current_class = match.group(1).replace("-", " ") if match else "Class"
            
            # 2. Extract Time
            t_match = re.search(r'([MTWRFS/]+)\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)', line)
            
            if t_match and current_class:
                days = t_match.group(1).split('/')
                
                # 3. Extract Room Number (Looks for pattern like SF-310, UC-202, usually Uppercase-Number)
                room_match = re.search(r'\b([A-Z]{1,4}-\d{3,4})\b', line)
                room_num = room_match.group(1) if room_match else ""
                
                # 4. Identify Remote
                is_remote = "Remote" in line or "remote" in line
                
                # Build Display Name
                display_name = current_class
                if room_num:
                    display_name += f" ({room_num})"
                
                loc_label = "Remote" if is_remote else ""
                
                events.append({
                    "type": "class", 
                    "name": display_name, 
                    "days": days, 
                    "start": get_minutes(t_match.group(2)), 
                    "end": get_minutes(t_match.group(3)), 
                    "loc": loc_label
                })

        # Process Office Hours
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
                name_label = "Virtual Office Hours" if is_virtual else "Office Hours"
                events.append({"type": "oh", "name": name_label, "days": found_days, "start": s_min, "end": e_min, "loc": ""})

        # --- HTML GENERATION ---
        start_hr, end_hr = 9, 20
        total_slots = (end_hr - start_hr) * 4
        
        # Colors that print well
        colors_cool = ["#d1e7dd", "#cfe2ff", "#e2e3e5", "#f8d7da"] # Bootstrap-ish pastels
        colors_warm = ["#fff3cd", "#ffecb5"]
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
                base_name = ev['name'].split('(')[0].strip() # Color based on class name, not room
                if base_name not in color_map: color_map[base_name] = random.choice(colors_cool)
                bg, border_color = color_map[base_name], "#000"
            else:
                bg, border_color = random.choice(colors_warm), "#000"
                
            for d in ev['days']:
                if d in col_map:
                    html_events += f"""
                    <div class="event" style="
                        grid-column: {col_map[d]}; 
                        grid-row: {row_start} / span {row_span}; 
                        background: {bg} !important; 
                        border: 1px solid {border_color};
                        color: #000;">
                        <strong>{ev['name']}</strong><br>{ev['loc']}
                    </div>"""
        
        html_times = ""
        for h in range(start_hr, end_hr + 1):
            r = (h - start_hr) * 4 + 2
            label = f"{h%12 or 12} {('AM' if h<12 else 'PM')}"
            html_times += f'<div class="time-label" style="grid-row: {r};">{label}</div><div class="grid-line" style="grid-row: {r};"></div>'

        # Condensed CSS for one-page printing
        final_html = f"""<!DOCTYPE html><html><head><style>
            @media print {{
                @page {{ size: portrait; margin: 0.25in; }}
                body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            }}
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #fff; padding: 10px; }}
            h1 {{ text-align: center; color: #000; font-weight: bold; font-size: 24px; margin: 0 0 20px 0; text-transform: uppercase; }}
            
            .calendar {{ 
                display: grid; 
                grid-template-columns: 50px repeat(5, 1fr); 
                grid-template-rows: 30px repeat({total_slots}, 1fr); 
                border-top: 2px solid #000; 
                border-bottom: 2px solid #000; 
                height: 750px; /* Condensed Height */
                width: 100%; 
                margin: 0 auto; 
                background: #fff; 
                /* Subtle grid background */
                background-image: linear-gradient(to right, transparent 50px, #ccc 51px, transparent 51px);
            }}
            
            .header {{ 
                background: #f0f0f0; 
                color: #000; 
                font-weight: bold; 
                text-align: center; 
                padding-top: 5px; 
                font-size: 16px; 
                border-bottom: 2px solid #000; 
            }}
            
            .time-label {{ 
                grid-column: 1; 
                font-size: 10px; 
                color: #444; 
                text-align: right; 
                padding-right: 5px; 
                transform: translateY(-50%); 
            }}
            
            .grid-line {{ 
                grid-column: 2 / span 5; 
                border-top: 1px solid #ddd; 
                height: 0; 
            }}
            
            .event {{ 
                margin: 1px; 
                padding: 2px 4px; 
                font-size: 11px; 
                overflow: hidden; 
                z-index: 2; 
                line-height: 1.2; 
                box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            }}
        </style></head><body><h1>{title_text}</h1><div class="calendar"><div class="header" style="grid-column:1"></div><div class="header">Mon</div><div class="header">Tue</div><div class="header">Wed</div><div class="header">Thu</div><div class="header">Fri</div>{html_times}{html_events}</div></body></html>"""
        
        st.success("✅ Door Sign Generated!")
        st.download_button("Download Door Sign HTML", data=final_html, file_name="door_sign.html", mime="text/html")

# ==========================================
# TOOL 3: DATE SHIFTER
# ==========================================
elif tool_choice == "⏳ ICS Date Shifter":
    st.header("Class Date Shifter")
    shift_file = st.file_uploader("Upload OLD .ics file", type="ics")
    new_start_date = st.date_input("New Start Date")
    
    if shift_file:
        c = Calendar(shift_file.read().decode("utf-8"))
        events = sorted(list(c.events), key=lambda x: x.begin)
        if events:
            delta = new_start_date - events[0].begin.date()
            if st.button(f"Shift by {delta.days} days"):
                new_c = Calendar()
                for e in events:
                    if delta.days >= 0:
                        e.end += timedelta(days=delta.days)
                        e.begin += timedelta(days=delta.days)
                    else:
                        e.begin += timedelta(days=delta.days)
                        e.end += timedelta(days=delta.days)
                    new_c.events.add(e)
                st.download_button("Download ICS", str(new_c), "shifted.ics")
