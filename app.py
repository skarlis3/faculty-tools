import streamlit as st
import pandas as pd
from ics import Calendar
from datetime import datetime, timedelta
import re
import random

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
            * **From Canvas:** Click the **Calendar icon** on the left navigation. On the right-hand sidebar, click **Calendar Feed**. Then click the words **Click to view Calendar Feed** in the pop-up window.
            * **From Other Apps:** You can also upload an `.ics` file from **Google Calendar**, Outlook, or Apple Calendar.
        """)

    with col_inst2:
        st.write("**2. Generate & Paste:**")
        st.caption("""
            * Upload the file below.
            * If you uploaded a Canvas .ics file, select the specific class from the dropdown menu that appears.
            * Copy the HTML code and paste it into the **Simple Syllabus** HTML/code field (< >).
        """)

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("First Day of Semester", value=datetime(2026, 1, 12))
        class_format = st.selectbox("Format", ["In-Person", "Hybrid", "Online"])
    with col2:
        uploaded_file = st.file_uploader("Upload your .ics file from Canvas or any calendar app (Google, etc.) here", type="ics", key="syl_upload")

    if uploaded_file:
        c = Calendar(uploaded_file.read().decode("utf-8"))
        all_events = list(c.events)

        # Regex captures: "ENGL 1170 S1628" or "ENGL-1170-O0823"
        course_pattern = r'([A-Z]{3,4}\s*[-]?\s*\d{4}(?:[\s-][A-Z0-9]{4,6})?)'
        
        found_codes = []
        for e in all_events:
            found_codes.extend(re.findall(course_pattern, e.name))
            if e.description:
                found_codes.extend(re.findall(course_pattern, e.description))
        
        # DEDUPLICATION LOGIC:
        # Keeps the most specific version (e.g., keeps "ENGL 1170 S1628" and removes "ENGL 1170")
        unique_raw = sorted(list(set(found_codes)), key=len, reverse=True)
        course_codes = []
        for code in unique_raw:
            if not any(code in longer_code for longer_code in course_codes):
                course_codes.append(code)
        course_codes.sort() # Alphabetical for dropdown
        
        selected_course = None
        if len(course_codes) > 1:
            st.info("💡 **Multiple sections/classes found.** Please select the specific section for this schedule:")
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
            st.subheader(f"HTML Code for {selected_course if selected_course else 'Schedule'}")
            st.code("\n".join(html_output), language="html")
            st.download_button("Download HTML File", "\n".join(html_output), "syllabus_schedule.html", "text/html")
        else:
            st.error("No events found after the selected start date.")

# ==========================================
# TOOL 2: DOOR SIGN GENERATOR (UPDATED)
# ==========================================
elif tool_choice == "🚪 Door Sign Generator":
    st.header("Visual Faculty Door Sign")
    st.markdown("Generates a print-friendly grid. Now includes Fridays and dynamic hour scaling.")

    raw_schedule = st.text_area("1. Paste Class Schedule (from software):", height=150, placeholder="2026 Winter Term\nENGL-1181-O0812\nENGL-1190-H1234\nMW 9:00 AM - 10:30 AM...")
    oh_text = st.text_input("2. Office Hours (e.g., 'Mon/Wed 11-12, Fri 9-10'):")
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
        online_only_classes = []
        lines = raw_schedule.split('\n')
        
        # Step 1: Parse the text into distinct class blocks or lines
        current_class_name = None
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Identify Class + Section
            class_match = re.search(r'ENGL[- ](\d+)[- ]([A-Z0-9]+)', line)
            if class_match:
                current_class_name = f"ENGL {class_match.group(1)}"
                current_section = class_match.group(2)
                full_code = f"{current_class_name} {current_section}"
                
                # Check if it's an Online class (Starts with O)
                # We flag it. If no time is found in subsequent lines for this class, it stays online.
                if current_section.startswith('O'):
                    if full_code not in online_only_classes:
                        online_only_classes.append(full_code)

            # Look for Time/Day pattern
            t_match = re.search(r'([MTWRFS/]+)\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)', line)
            if t_match and current_class_name:
                # If we found a time, and it was previously in the online_only list (because of section O), 
                # remove it from online_only because it actually has a meeting time (like a Hybrid or Sync class)
                full_code = f"{current_class_name} {current_section}"
                if full_code in online_only_classes:
                    online_only_classes.remove(full_code)
                
                days_list = []
                raw_days = t_match.group(1)
                # Map standard abbreviations to our col_map keys
                if 'M' in raw_days: days_list.append('M')
                if 'T' in raw_days: days_list.append('T')
                if 'W' in raw_days: days_list.append('W')
                if 'R' in raw_days or 'TH' in raw_days.upper(): days_list.append('Th')
                if 'F' in raw_days: days_list.append('F')
                
                room_match = re.search(r'\b([A-Z]{1,3}-\d{3,4})\b', line)
                room_num = room_match.group(1) if room_match else ""
                loc = "Remote" if ("Remote" in line or "remote" in line) else (room_num if room_num else "")
                
                events.append({
                    "type": "class", 
                    "name": full_code, 
                    "days": days_list, 
                    "start": get_minutes(t_match.group(2)), 
                    "end": get_minutes(t_match.group(3)), 
                    "loc": loc
                })

        # Step 2: Parse Office Hours
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
                if s_raw < 8: s_min += 12*60
                if e_raw < 8: e_min += 12*60
                if e_raw < s_raw: e_min += 12*60
                name_label = "Virtual Office Hours" if is_virtual else "Office Hours"
                events.append({"type": "oh", "name": name_label, "days": found_days, "start": s_min, "end": e_min, "loc": ""})

        # Step 3: Determine Dynamic Hour Range
        if events:
            min_time = min(e['start'] for e in events)
            max_time = max(e['end'] for e in events)
            start_hr = max(0, (min_time // 60) - 1)  # 1 hour padding
            end_hr = min(23, (max_time // 60) + 1)   # 1 hour padding
        else:
            start_hr, end_hr = 9, 17 # Default if empty

        total_slots = (end_hr - start_hr) * 4
        colors_cool = ["#e8f4f8", "#e3f2fd", "#e0f2f1", "#f3e5f5", "#fff3e0", "#f1f8e9"]
        color_map = {}
        html_events = ""
        col_map = {"M": 2, "T": 3, "W": 4, "Th": 5, "F": 6}
        
        for ev in events:
            start_offset = ev['start'] - (start_hr * 60)
            end_offset = ev['end'] - (start_hr * 60)
            row_start = int(start_offset / 15) + 2
            row_span = int((end_offset - start_offset) / 15)
            if row_span < 1: row_span = 1
            
            if ev['type'] == 'class':
                if ev['name'] not in color_map: color_map[ev['name']] = colors_cool[len(color_map) % len(colors_cool)]
                bg, border = color_map[ev['name']], "#546e7a"
            else:
                bg, border = "#fff8e1", "#d84315"
                
            for d in ev['days']:
                if d in col_map:
                    loc_html = f"<br>{ev['loc']}" if ev['loc'] else ""
                    html_events += f"""<div class="event" style="grid-column: {col_map[d]}; grid-row: {row_start} / span {row_span}; background: {bg}; border-left: 4px solid {border}; color: #000;"><strong>{ev['name']}</strong>{loc_html}</div>"""
        
        html_times = ""
        for h in range(start_hr, end_hr + 1):
            r = (h - start_hr) * 4 + 2
            label = f"{h%12 or 12} {('AM' if h<12 else 'PM')}"
            html_times += f'<div class="time-label" style="grid-row: {r};">{label}</div><div class="grid-line" style="grid-row: {r};"></div>'

        # Build Online Classes Section
        online_section_html = ""
        if online_only_classes:
            online_section_html = "<div class='online-list'><strong>Online Classes:</strong> " + ", ".join(online_only_classes) + "</div>"

        final_html = f"""<!DOCTYPE html><html><head><style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #fff; padding: 20px; display: flex; flex-direction: column; align-items: center; }}
            h1 {{ text-align: center; color: #000; font-weight: normal; font-size: 24px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1.5px; }}
            .calendar {{ display: grid; grid-template-columns: 60px repeat(5, 1fr); grid-template-rows: 35px repeat({total_slots}, 1fr); border: none; height: 750px; width: 100%; max-width: 850px; background: #fff; }}
            .header {{ background: #fff; color: #000; font-weight: bold; text-align: center; padding-top: 5px; font-size: 16px; border-bottom: 1px solid #ccc; }}
            .time-label {{ grid-column: 1; font-size: 10px; color: #444; text-align: right; padding-right: 12px; transform: translateY(-50%); }}
            .grid-line {{ grid-column: 2 / span 5; border-top: 1px solid #eee; height: 0; }}
            .event {{ margin: 1px; padding: 4px; font-size: 11px; border-radius: 0px; overflow: hidden; z-index: 2; line-height: 1.2; print-color-adjust: exact; }}
            .online-list {{ margin-top: 30px; width: 100%; max-width: 850px; font-size: 14px; border-top: 2px solid #eee; padding-top: 10px; text-align: center; }}
            @media print {{ @page {{ margin: 0.5in; }} .calendar {{ height: auto; min-height: 600px; }} }}
        </style></head><body><h1>{title_text}</h1><div class="calendar"><div class="header" style="grid-column:1"></div><div class="header">Mon</div><div class="header">Tue</div><div class="header">Wed</div><div class="header">Thu</div><div class="header">Fri</div>{html_times}{html_events}</div>{online_section_html}</body></html>"""
        
        st.success("✅ Door Sign Generated!")
        st.download_button("Download Door Sign HTML", data=final_html, file_name="door_sign.html", mime="text/html")


# ==========================================
# TOOL 3: FACULTY ASSIGNMENT SHEET HELPER
# ==========================================
elif tool_choice == "📋 Faculty Assignment Sheet Helper":
    st.header("📋 Faculty Assignment Sheet Helper")
    st.info("Instructions: Copy/paste your schedule directly from Self-Service below. Select 'BASE' or 'EC' for each row, then copy the result.")
    
    messy_text = st.text_area("Paste Schedule Text from Self-Service:", height=300)

    if st.button("Generate FAS Table Rows", type="primary"):
        if not messy_text:
            st.warning("Please paste some text first.")
        else:
            hour_map = {"1170": (1, 1, 2), "1181": (4, 4, 5), "1190": (4, 4, 5), "1210": (3, 3, 4), "1220": (3, 3, 4), "1211": (3, 3, 4), "1221": (3, 3, 4)}
            course_pattern = r'([A-Z]{3,4}-\d{4}-[A-Z0-9]+)'
            starts = [m.start() for m in re.finditer(course_pattern, messy_text)]
            starts.append(len(messy_text)) 
            blocks = [messy_text[starts[i]:starts[i+1]] for i in range(len(starts)-1)]

            rows = []
            for block in blocks:
                name_match = re.search(course_pattern, block)
                if not name_match: continue
                full_code = name_match.group(1)
                course_num, section_code = full_code.split('-')[1], full_code.split('-')[2]
                cr, cont, eq = hour_map.get(course_num, (3, 3, 3))
                date_finds = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', block)
                begin_date, end_date = (date_finds[0] if date_finds else ""), (date_finds[-1] if date_finds else "")
                t_match = re.search(r'(\d{1,2}:\d{2}(?:\s*[AP]M)?\s*-\s*\d{1,2}:\d{2}\s*[AP]M)', block, re.IGNORECASE)
                time_str = t_match.group(1).upper() if t_match else ""
                days_found = set()
                if t_match:
                    for line in block.split('\n'):
                        if t_match.group(0) in line:
                            up_line = line.upper()
                            if "M/W" in up_line or "MW" in up_line: days_found.update(["Mon", "Wed"])
                            if "T/TH" in up_line or "TTH" in up_line or "T/R" in up_line: days_found.update(["Tue", "Thu"])
                            if re.search(r'\bM\b', up_line): days_found.add("Mon")
                            if re.search(r'\bT\b', up_line): days_found.add("Tue")
                            if re.search(r'\bW\b', up_line): days_found.add("Wed")
                            if re.search(r'\bR\b', up_line) or "TH" in up_line: days_found.add("Thu")
                            if re.search(r'\bF\b', up_line): days_found.add("Fri")

                is_hybrid = section_code.startswith("H")
                has_remote_label, has_online_label = "REMOTE" in block.upper(), "ONLINE" in block.upper()
                room_match = re.search(r'SOU-([A-Z]),\s*(\d+)', block)
                physical_room = f"S{room_match.group(1)}-{room_match.group(2)}" if room_match else ""
                room_display, online_section_val = "", ""

                if is_hybrid:
                    room_display = physical_room if physical_room else ("Remote" if has_remote_label else "")
                else:
                    if physical_room: room_display = physical_room
                    elif has_remote_label: room_display = "Remote"
                    elif has_online_label and not time_str: online_section_val = "Yes"

                rows.append({"Course Code /Section": full_code.replace("-", " "), "Cr Hrs": cr, "Cont Hrs": cont, "Eq Hrs": eq, "Contract Type(s)": "", "Combined With": "", "Begin Date": begin_date, "End Date": end_date, "Mon": time_str if "Mon" in days_found else "", "Tue": time_str if "Tue" in days_found else "", "Wed": time_str if "Wed" in days_found else "", "Thu": time_str if "Thu" in days_found else "", "Fri": time_str if "Fri" in days_found else "", "Sat": time_str if "Sat" in days_found else "", "Room": room_display, "Online Section": online_section_val})

            if rows:
                cols = ["Course Code /Section", "Cr Hrs", "Cont Hrs", "Eq Hrs", "Contract Type(s)", "Combined With", "Begin Date", "End Date", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Room", "Online Section"]
                df = pd.DataFrame(rows, columns=cols)
                st.success(f"Parsed {len(df)} classes.")
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                tsv = edited_df.to_csv(sep='\t', index=False, header=False)
                st.write("### Excel Copy Block")
                st.code(tsv, language="text")

# ==========================================
# TOOL 4: DATE SHIFTER & CALCULATOR
# ==========================================
elif tool_choice == "⏳ Date Shifter & Calculator":
    st.header("⏳ Date Shift Calculator & Shifter")
    st.subheader("1. Calculate Your Offset")
    calc_col1, calc_col2, calc_col3 = st.columns(3)
    with calc_col1: old_ref_date = st.date_input("Old Reference Date", value=datetime(2025, 8, 25))
    with calc_col2: new_ref_date = st.date_input("New Reference Date", value=datetime(2026, 1, 12))
    with calc_col3: canvas_adjustment = st.checkbox("Add +1 day for Canvas?", value=True)
    raw_delta = (new_ref_date - old_ref_date).days
    final_shift = raw_delta + 1 if canvas_adjustment else raw_delta
    st.metric("Total Days to Shift", f"{final_shift} days", delta=f"{raw_delta} raw + {'1 canvas' if canvas_adjustment else '0'}")
    st.divider()
    st.subheader("2. Apply to ICS File (Optional)")
    shift_file = st.file_uploader("Upload OLD .ics file", type="ics")
    if shift_file:
        c = Calendar(shift_file.read().decode("utf-8"))
        events = sorted(list(c.events), key=lambda x: x.begin)
        if events:
            st.write(f"Parsed {len(events)} events.")
            if st.button(f"Generate New ICS with +{final_shift} Day Shift"):
                new_c = Calendar()
                for e in events:
                    e.begin += timedelta(days=final_shift)
                    e.end += timedelta(days=final_shift)
                    new_c.events.add(e)
                st.success(f"Shifted by {final_shift} days.")
                st.download_button("Download Shifted ICS", str(new_c), f"shifted_{final_shift}_days.ics")

# Footer
st.divider()
st.caption("Contact Sarah Karlis with any questions or suggestions about these faculty tools.")
