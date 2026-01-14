import streamlit as st
import pandas as pd
from ics import Calendar
from datetime import datetime, timedelta
import re

# --- PAGE SETUP ---
st.set_page_config(page_title="Faculty Tools", page_icon="💻", layout="wide")

st.title("🎓 Faculty Tools")
st.markdown("Tools to automate your syllabus, door signs, calendar dates, and assignment sheets.")

# Banner
st.warning("⚠️ **Note:** These faculty tools are a work-in-progress. Double-check all output for accuracy.")

# --- SIDEBAR NAVIGATION ---
tool_choice = st.sidebar.radio("Select Tool:", 
    ["📅 Syllabus Schedule", "🚪 Door Sign Generator", "📋 Faculty Assignment Sheet Helper", "⏳ Date Shifter & Calculator"])

# ==========================================
# TOOL 1: SYLLABUS SCHEDULE
# ==========================================
if tool_choice == "📅 Syllabus Schedule":
    st.header("Syllabus Schedule Generator")
    
    st.markdown("### 🛠 Instructions")
    col_inst1, col_inst2 = st.columns(2)
    
    with col_inst1:
        st.write("**1. Get your .ics File:**")
        st.caption("""
            * **From Canvas:** Click the **Calendar icon** on the left navigation. On the right-hand sidebar, click **Calendar Feed**. 
            * **From Other Apps:** Upload an `.ics` file from Google, Outlook, or Apple Calendar.
        """)

    with col_inst2:
        st.write("**2. Generate & Paste:**")
        st.caption("""
            * Select the specific class from the dropdown menu.
            * Copy the HTML code and paste it into the **Simple Syllabus** HTML/code field (< >).
        """)

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("First Day of Semester", value=datetime(2026, 1, 12))
        class_format = st.selectbox("Format", ["In-Person", "Hybrid", "Online"])
    with col2:
        uploaded_file = st.file_uploader("Upload your .ics file here", type="ics", key="syl_upload")

    if uploaded_file:
        c = Calendar(uploaded_file.read().decode("utf-8"))
        all_events = list(c.events)
        course_pattern = r'([A-Z]{3,4}\s*[-]?\s*\d{4}(?:[\s-][A-Z0-9]{4,6})?)'
        
        found_codes = []
        for e in all_events:
            found_codes.extend(re.findall(course_pattern, e.name))
            if e.description:
                found_codes.extend(re.findall(course_pattern, e.description))
        
        unique_raw = sorted(list(set(found_codes)), key=len, reverse=True)
        course_codes = []
        for code in unique_raw:
            if not any(code in longer_code for longer_code in course_codes):
                course_codes.append(code)
        course_codes.sort()
        
        selected_course = None
        if len(course_codes) > 1:
            st.info("💡 Multiple sections found. Please select:")
            selected_course = st.selectbox("Select Class & Section:", course_codes)
            filtered_events = [e for e in all_events if selected_course in e.name or (e.description and selected_course in e.description)]
        elif len(course_codes) == 1:
            selected_course = course_codes[0]
            filtered_events = [e for e in all_events if selected_course in e.name or (e.description and selected_course in e.description)]
        else:
            filtered_events = all_events

        events = sorted([e for e in filtered_events if e.begin.date() >= (start_date.date() if hasattr(start_date, 'date') else start_date)], key=lambda x: x.begin)

        if events:
            html_output = ["<div style='font-family: sans-serif; max-width: 800px; margin: 0 auto;'>"]
            if class_format in ["Hybrid", "Online"]:
                events_by_week = {}
                for e in events:
                    monday = e.begin.date() - timedelta(days=e.begin.date().weekday())
                    if monday not in events_by_week: events_by_week[monday] = []
                    events_by_week[monday].append(e)
                for week_start in sorted(events_by_week.keys()):
                    we = events_by_week[week_start]
                    is_break = any("break" in x.name.lower() or "holiday" in x.name.lower() for x in we)
                    calc_start = start_date.date() if hasattr(start_date, 'date') else start_date
                    week_num = ((week_start - calc_start).days // 7) + 1
                    label = f"🍂 Week {week_num} (Break)" if is_break else f"Week {week_num}: {week_start.strftime('%b %d')}"
                    html_output.append(f"<div style='border:1px solid #ccc; padding:15px; margin-bottom:15px; border-radius:5px;'><h3>{label}</h3><ul>")
                    for e in we:
                        display_name = e.name.replace(selected_course, "").strip(": ") if selected_course else e.name
                        etype = "color:#900; font-weight:bold;" if "due" in display_name.lower() else "color:#333;"
                        html_output.append(f"<li style='{etype}'>{display_name}</li>")
                    html_output.append("</ul></div>")
            else:
                for e in events:
                    display_name = e.name.replace(selected_course, "").strip(": ") if selected_course else e.name
                    html_output.append(f"<div style='border-bottom:1px solid #eee; padding:10px;'><strong>{e.begin.format('ddd, MMM D')}:</strong> {display_name}</div>")
            html_output.append("</div>")
            st.code("\n".join(html_output), language="html")
            st.download_button("Download HTML", "\n".join(html_output), "schedule.html", "text/html")

# ==========================================
# TOOL 2: DOOR SIGN GENERATOR
# ==========================================
elif tool_choice == "🚪 Door Sign Generator":
    st.header("Visual Faculty Door Sign")
    st.markdown("Copy your schedule from self-service and paste it below. Office hours will automatically be labeled in full for student clarity.")

    raw_schedule = st.text_area("1. Paste Class Schedule:", height=150, placeholder="ENGL-1181-O0812\n8/19/25-10/15/25\nENGL-1190-S1628\nMW 9:00 AM - 10:30 AM")
    oh_text = st.text_input("2. Office Hours (e.g., 'M-Th 11-1, Fri 9-10' or Mon/Wed 10-12, Virtual Mon-Tue 5-6):")
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

        months = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        events = []
        online_data = {} # full_code -> month_string
        lines = raw_schedule.split('\n')
        current_class_name, current_section = None, None

        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Identify Class + Section
            class_match = re.search(r'ENGL[- ](\d+)[- ]([A-Z0-9]+)', line)
            if class_match:
                current_class_name = f"ENGL {class_match.group(1)}"
                current_section = class_match.group(2)
                full_code = f"{current_class_name} {current_section}"
                if current_section.startswith('O'):
                    if full_code not in online_data:
                        online_data[full_code] = ""

            # Look for Start Date (e.g. 8/19/25)
            date_match = re.search(r'(\d{1,2})/\d{1,2}/\d{2,4}', line)
            if date_match and current_class_name:
                full_code = f"{current_class_name} {current_section}"
                if full_code in online_data:
                    m_idx = int(date_match.group(1))
                    online_data[full_code] = f" ({months[m_idx]} start)"

            # Look for Time/Day pattern (for Hybrid/In-Person)
            t_match = re.search(r'([MTWRFS/]+)\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)', line)
            if t_match and current_class_name:
                full_code = f"{current_class_name} {current_section}"
                # If it has a time, it's not "Online Only" for the bottom list
                if full_code in online_data: del online_data[full_code]
                
                days_list = []
                raw_days = t_match.group(1)
                for char, code in zip(['M','T','W','R','F'],['M','T','W','Th','F']):
                    if char in raw_days: days_list.append(code)
                room_match = re.search(r'\b([A-Z]{1,3}-\d{3,4})\b', line)
                loc = "Remote" if "remote" in line.lower() else (room_match.group(1) if room_match else "")
                events.append({"type": "class", "name": full_code, "days": days_list, "start": get_minutes(t_match.group(2)), "end": get_minutes(t_match.group(3)), "loc": loc})

        # OFFICE HOUR RANGE PARSER
        day_map_list = ['M', 'T', 'W', 'Th', 'F']
        day_name_to_idx = {'MON':0, 'M':0, 'TUE':1, 'T':1, 'WED':2, 'W':2, 'THU':3, 'TH':3, 'R':3, 'FRI':4, 'F':4}

        for part in oh_text.split(','):
            part = part.strip()
            if not part: continue
            is_virtual = "virtual" in part.lower()
            search_string = part.upper().replace("VIRTUAL", "")
            
            range_match = re.search(r'([A-Z]+)\s*-\s*([A-Z]+)', search_string)
            found_days = []
            if range_match:
                start_day_idx = day_name_to_idx.get(range_match.group(1))
                end_day_idx = day_name_to_idx.get(range_match.group(2))
                if start_day_idx is not None and end_day_idx is not None:
                    found_days = day_map_list[start_day_idx : end_day_idx + 1]
            else:
                for dname, dcode in day_name_to_idx.items():
                    if dname in search_string: 
                        if day_map_list[dcode] not in found_days:
                            found_days.append(day_map_list[dcode])

            time_parts = re.findall(r'(\d{1,2}(?::\d{2})?)', part)
            if len(time_parts) >= 2:
                def parse_oh_time(t_str):
                    h, m = (map(int, t_str.split(':')) if ':' in t_str else (int(t_str), 0))
                    if 1 <= h <= 7: h += 12
                    return h * 60 + m
                s_min, e_min = parse_oh_time(time_parts[0]), parse_oh_time(time_parts[1])
                if e_min <= s_min: e_min += 12 * 60
                events.append({"type": "oh", "name": "Virtual Office Hours" if is_virtual else "Office Hours", "days": found_days, "start": s_min, "end": e_min, "loc": ""})

        if events:
            all_times = [e['start'] for e in events] + [e['end'] for e in events]
            start_hr, end_hr = max(0, (min(all_times)//60)-1), min(23, (max(all_times)//60)+1)
        else:
            start_hr, end_hr = 9, 17

        total_slots, html_events = (end_hr - start_hr) * 4, ""
        colors_cool = ["#e8f4f8", "#e3f2fd", "#e0f2f1", "#f3e5f5", "#fff3e0", "#f1f8e9"]
        color_map, col_map = {}, {"M": 2, "T": 3, "W": 4, "Th": 5, "F": 6}
        
        for ev in events:
            start_off, end_off = ev['start'] - (start_hr * 60), ev['end'] - (start_hr * 60)
            row_s, row_span = int(start_off/15)+2, max(1, int((end_off-start_off)/15))
            bg, border = ("#fff8e1", "#d84315") if ev['type'] == 'oh' else (color_map.setdefault(ev['name'], colors_cool[len(color_map)%len(colors_cool)]), "#546e7a")
            for d in ev['days']:
                if d in col_map:
                    loc_h = f"<br>{ev['loc']}" if ev['loc'] else ""
                    html_events += f'<div class="event" style="grid-column:{col_map[d]}; grid-row:{row_s}/span {row_span}; background:{bg}; border-left:4px solid {border}; color:#000;"><strong>{ev['name']}</strong>{loc_h}</div>'
        
        html_times = ""
        for h in range(start_hr, end_hr + 1):
            r = (h - start_hr) * 4 + 2
            html_times += f'<div class="time-label" style="grid-row:{r};">{h%12 or 12} {"AM" if h<12 else "PM"}</div><div class="grid-line" style="grid-row:{r};"></div>'

        online_list = [f"{k}{v}" for k, v in online_data.items()]
        online_h = f"<div style='margin-top:30px; border-top:2px solid #eee; padding-top:10px; width:100%; max-width:850px; text-align:center;'><strong>Online Classes:</strong><br>{', '.join(online_list)}</div>" if online_list else ""
        
        final_html = f"""<!DOCTYPE html><html><head><style>
            body {{ font-family: 'Segoe UI', sans-serif; padding: 20px; display: flex; flex-direction: column; align-items: center; }}
            h1 {{ text-align: center; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 20px; }}
            .calendar {{ display: grid; grid-template-columns: 60px repeat(5, 1fr); grid-template-rows: 35px repeat({total_slots}, 1fr); width: 100%; max-width: 850px; border: none; }}
            .header {{ font-weight: bold; text-align: center; border-bottom: 1px solid #ccc; font-size: 16px; padding-top: 5px; }}
            .time-label {{ font-size: 10px; color: #444; text-align: right; padding-right: 12px; transform: translateY(-50%); }}
            .grid-line {{ grid-column: 2 / span 5; border-top: 1px solid #eee; height: 0; }}
            .event {{ margin: 1px; padding: 4px; font-size: 11px; border-radius: 0px; line-height: 1.2; print-color-adjust: exact; -webkit-print-color-adjust: exact; overflow: hidden; }}
            @media print {{ @page {{ margin: 0.5in; }} .calendar {{ height: auto; }} }}
        </style></head><body><h1>{title_text}</h1><div class="calendar"><div class="header" style="grid-column:1"></div><div class="header">Mon</div><div class="header">Tue</div><div class="header">Wed</div><div class="header">Thu</div><div class="header">Fri</div>{html_times}{html_events}</div>{online_h}</body></html>"""
        st.success("✅ Door Sign Generated!")
        st.download_button("Download HTML", data=final_html, file_name="door_sign.html", mime="text/html")

# ==========================================
# TOOL 3: FACULTY ASSIGNMENT SHEET HELPER
# ==========================================
elif tool_choice == "📋 Faculty Assignment Sheet Helper":
    st.header("📋 Faculty Assignment Sheet Helper")
    messy_text = st.text_area("Paste Schedule from Self-Service:", height=300)
    if st.button("Generate FAS Table Rows", type="primary"):
        if not messy_text:
            st.warning("Please paste some text.")
        else:
            hour_map = {"1170": (1,1,2), "1181": (4,4,5), "1190": (4,4,5), "1210": (3,3,4), "1220": (3,3,4), "1211": (3,3,4), "1221": (3,3,4)}
            course_pattern = r'([A-Z]{3,4}-\d{4}-[A-Z0-9]+)'
            starts = [m.start() for m in re.finditer(course_pattern, messy_text)] + [len(messy_text)]
            blocks = [messy_text[starts[i]:starts[i+1]] for i in range(len(starts)-1)]
            rows = []
            for block in blocks:
                name_match = re.search(course_pattern, block)
                if not name_match: continue
                f_code = name_match.group(1)
                c_num, s_code = f_code.split('-')[1], f_code.split('-')[2]
                cr, cont, eq = hour_map.get(c_num, (3,3,3))
                date_finds = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', block)
                b_date, e_date = (date_finds[0] if date_finds else ""), (date_finds[-1] if date_finds else "")
                t_match = re.search(r'(\d{1,2}:\d{2}(?:\s*[AP]M)?\s*-\s*\d{1,2}:\d.2\s*[AP]M)', block, re.I)
                time_s, days_f = (t_match.group(1).upper() if t_match else ""), set()
                if t_match:
                    up_block = block.upper()
                    if "M/W" in up_block or "MW" in up_block: days_f.update(["Mon","Wed"])
                    if "T/TH" in up_block or "TTH" in up_block or "T/R" in up_block: days_f.update(["Tue","Thu"])
                    if re.search(r'\bM\b', up_block): days_f.add("Mon")
                    if re.search(r'\bT\b', up_block): days_f.add("Tue")
                    if re.search(r'\bW\b', up_block): days_f.add("Wed")
                    if re.search(r'\bR\b', up_block) or "TH" in up_block: days_f.add("Thu")
                    if re.search(r'\bF\b', up_block): days_f.add("Fri")
                physical = f"S{re.search(r'SOU-([A-Z]),\s*(\d+)', block).group(1)}-{re.search(r'SOU-([A-Z]),\s*(\d+)', block).group(2)}" if re.search(r'SOU-([A-Z]),\s*(\d+)', block) else ""
                room_d = physical if physical else ("Remote" if "REMOTE" in block.upper() else "")
                rows.append({"Course Code /Section": f_code.replace("-"," "), "Cr Hrs": cr, "Cont Hrs": cont, "Eq Hrs": eq, "Begin Date": b_date, "End Date": e_date, "Mon": time_s if "Mon" in days_f else "", "Tue": time_s if "Tue" in days_f else "", "Wed": time_s if "Wed" in days_f else "", "Thu": time_s if "Thu" in days_f else "", "Fri": time_s if "Fri" in days_f else "", "Room": room_d, "Online": ("Yes" if "ONLINE" in block.upper() and not time_s else "")})
            if rows:
                df = pd.DataFrame(rows)
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                st.code(edited_df.to_csv(sep='\t', index=False, header=False), language="text")

# ==========================================
# TOOL 4: DATE SHIFTER & CALCULATOR
# ==========================================
elif tool_choice == "⏳ Date Shifter & Calculator":
    st.header("⏳ Date Shift Calculator")
    calc_col1, calc_col2, calc_col3 = st.columns(3)
    with calc_col1: old_ref = st.date_input("Old Ref Date", value=datetime(2025, 8, 25))
    with calc_col2: new_ref = st.date_input("New Ref Date", value=datetime(2026, 1, 12))
    with calc_col3: canvas_adj = st.checkbox("Add +1 day for Canvas?", value=True)
    f_shift = (new_ref - old_ref).days + (1 if canvas_adj else 0)
    st.metric("Total Days to Shift", f"{f_shift} days")
    st.divider()
    shift_file = st.file_uploader("Upload OLD .ics file", type="ics")
    if shift_file:
        c = Calendar(shift_file.read().decode("utf-8"))
        if st.button(f"Generate Shifted ICS (+{f_shift})"):
            new_c = Calendar()
            for e in c.events:
                e.begin += timedelta(days=f_shift)
                e.end += timedelta(days=f_shift)
                new_c.events.add(e)
            st.download_button("Download Shifted ICS", str(new_c), "shifted.ics")

st.divider()
st.caption("Contact Sarah Karlis with any questions.")
