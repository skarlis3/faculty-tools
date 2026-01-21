import streamlit as st
import pandas as pd
from ics import Calendar
from datetime import datetime, timedelta
import re

# --- PAGE SETUP ---
st.set_page_config(page_title="Faculty Tools", page_icon="📚", layout="wide")

# Custom CSS for clean, professional look with dark mode support
st.markdown("""
<style>
    /* Light mode styles */
    .instruction-box {
        background-color: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        color: #1e293b;
        line-height: 1.8;
    }
    .instruction-box strong {
        color: #0f172a;
    }
    
    /* Dark mode styles */
    @media (prefers-color-scheme: dark) {
        .instruction-box {
            background-color: #1e293b;
            border-left: 4px solid #60a5fa;
            color: #e2e8f0;
        }
        .instruction-box strong {
            color: #f1f5f9;
        }
    }
    
    .stButton button {
        border-radius: 0.5rem;
        font-weight: 500;
    }
    
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #0891b2;
        color: white;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #0e7490;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS ---
COURSE_PATTERN = r'([A-Z]{3,4}\s*[-]?\s*\d{4}(?:[\s-][A-Z0-9]{4,6})?)'
TIME_PATTERN = r'(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)'
MONTHS = ["", "January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]
HOUR_MAP = {
    "1170": (1, 1, 2),
    "1181": (4, 4, 5),
    "1190": (4, 4, 5),
    "1210": (3, 3, 4),
    "1220": (3, 3, 4),
    "1211": (3, 3, 4),
    "1221": (3, 3, 4)
}

# --- HELPER FUNCTIONS ---

@st.cache_data
def parse_calendar_file(file_contents):
    """Parse ICS calendar file with caching"""
    try:
        return Calendar(file_contents)
    except Exception as e:
        st.error(f"Error reading calendar file: {str(e)}")
        return None

def get_minutes(time_str):
    """Convert time string to minutes since midnight"""
    time_str = time_str.upper().strip()
    
    if ':' not in time_str:
        try:
            val = int(time_str)
            if val == 12:
                return 12 * 60
            if 1 <= val <= 7:
                return (val + 12) * 60
            return val * 60
        except:
            return 0
    
    try:
        parts = re.split('[: ]+', time_str)
        h, m = int(parts[0]), int(parts[1])
        is_pm = 'PM' in time_str
        if is_pm and h != 12:
            h += 12
        if not is_pm and h == 12:
            h = 0
        return h * 60 + m
    except:
        return 0

def parse_office_hours_time(time_str):
    """Parse office hours time format"""
    h, m = (map(int, time_str.split(':')) if ':' in time_str else (int(time_str), 0))
    if 1 <= h <= 7:
        h += 12
    return h * 60 + m

def extract_course_codes(events):
    """Extract unique course codes from calendar events"""
    found_codes = []
    for e in events:
        found_codes.extend(re.findall(COURSE_PATTERN, e.name))
        if e.description:
            found_codes.extend(re.findall(COURSE_PATTERN, e.description))
    
    unique_raw = sorted(list(set(found_codes)), key=len, reverse=True)
    course_codes = []
    for code in unique_raw:
        if not any(code in longer_code for longer_code in course_codes):
            course_codes.append(code)
    course_codes.sort()
    return course_codes

# --- MAIN APP ---

st.title("Faculty Tools")
st.markdown("Tools to automate your syllabus, door signs, calendar dates, and assignment sheets.")

st.info("Note: These faculty tools are a work-in-progress. Double-check all output for accuracy.")

# --- SIDEBAR NAVIGATION ---
tool_choice = st.sidebar.radio("Select Tool:", [
    "Syllabus Schedule",
    "Door Sign Generator",
    "Assignment Sheet Helper",
    "Date Shifter & Calculator"
])

# ==========================================
# TOOL 1: SYLLABUS SCHEDULE
# ==========================================
if tool_choice == "Syllabus Schedule":
    st.header("Syllabus Schedule Generator")
    
    with st.expander("How to Use This Tool", expanded=True):
        st.markdown("""
        <div class="instruction-box">
        <strong>Step 1: Get your .ics File</strong>
        <ul>
            <li><strong>From Canvas:</strong> Click the Calendar icon on the left navigation. 
            On the right-hand sidebar, click Calendar Feed.</li>
            <li><strong>From Other Apps:</strong> Upload an .ics file from Google, Outlook, or Apple Calendar.</li>
        </ul>
        
        <strong>Step 2: Generate & Paste</strong>
        <ul>
            <li>Select the specific class from the dropdown menu.</li>
            <li>Copy the HTML code and paste it into the Simple Syllabus HTML/code field (&lt; &gt;).</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("First Day of Semester", value=datetime(2026, 1, 12))
        class_format = st.selectbox("Format", ["In-Person", "Hybrid", "Online"])
    with col2:
        uploaded_file = st.file_uploader("Upload your .ics file", type="ics", key="syl_upload")

    if uploaded_file:
        with st.spinner("Parsing calendar..."):
            calendar = parse_calendar_file(uploaded_file.read().decode("utf-8"))
            
        if not calendar:
            st.stop()
            
        all_events = list(calendar.events)
        course_codes = extract_course_codes(all_events)
        
        selected_course = None
        if len(course_codes) > 1:
            st.info("Multiple sections found. Please select:")
            selected_course = st.selectbox("Select Class & Section:", course_codes)
            filtered_events = [
                e for e in all_events 
                if selected_course in e.name or (e.description and selected_course in e.description)
            ]
        elif len(course_codes) == 1:
            selected_course = course_codes[0]
            filtered_events = [
                e for e in all_events 
                if selected_course in e.name or (e.description and selected_course in e.description)
            ]
        else:
            filtered_events = all_events

        # Filter events by start date
        start_date_obj = start_date.date() if hasattr(start_date, 'date') else start_date
        events = sorted(
            [e for e in filtered_events if e.begin.date() >= start_date_obj],
            key=lambda x: x.begin
        )

        if events:
            html_output = ["<div style='font-family: sans-serif; max-width: 800px; margin: 0 auto;'>"]
            
            if class_format in ["Hybrid", "Online"]:
                # Group by week
                events_by_week = {}
                for e in events:
                    monday = e.begin.date() - timedelta(days=e.begin.date().weekday())
                    if monday not in events_by_week:
                        events_by_week[monday] = []
                    events_by_week[monday].append(e)
                
                for week_start in sorted(events_by_week.keys()):
                    week_events = events_by_week[week_start]
                    is_break = any(
                        "break" in x.name.lower() or "holiday" in x.name.lower() 
                        for x in week_events
                    )
                    week_num = ((week_start - start_date_obj).days // 7) + 1
                    
                    if is_break:
                        label = f"Week {week_num} (Break)"
                    else:
                        label = f"Week {week_num}: {week_start.strftime('%b %d')}"
                    
                    html_output.append(
                        f"<div style='border:1px solid #ccc; padding:15px; margin-bottom:15px; "
                        f"border-radius:5px;'><h3>{label}</h3><ul>"
                    )
                    
                    for e in week_events:
                        display_name = (
                            e.name.replace(selected_course, "").strip(": ") 
                            if selected_course else e.name
                        )
                        style = (
                            "color:#900; font-weight:bold;" 
                            if "due" in display_name.lower() 
                            else "color:#333;"
                        )
                        html_output.append(f"<li style='{style}'>{display_name}</li>")
                    
                    html_output.append("</ul></div>")
            else:
                # In-person format
                for e in events:
                    display_name = (
                        e.name.replace(selected_course, "").strip(": ") 
                        if selected_course else e.name
                    )
                    html_output.append(
                        f"<div style='border-bottom:1px solid #eee; padding:10px;'>"
                        f"<strong>{e.begin.format('ddd, MMM D')}:</strong> {display_name}</div>"
                    )
            
            html_output.append("</div>")
            final_html = "\n".join(html_output)
            
            st.success("Schedule generated successfully!")
            st.code(final_html, language="html")
            st.download_button(
                "Download HTML",
                final_html,
                "schedule.html",
                "text/html"
            )

# ==========================================
# TOOL 2: DOOR SIGN GENERATOR
# ==========================================
elif tool_choice == "Door Sign Generator":
    st.header("Visual Faculty Door Sign")
    
    with st.expander("How to Use This Tool", expanded=True):
        st.markdown("""
        <div class="instruction-box">
        <strong>This tool generates a visual weekly schedule for your office door.</strong>
        <ul>
            <li>Sections starting with <strong>O</strong> are listed at the bottom as online classes</li>
            <li>Sections starting with <strong>H</strong> or <strong>S</strong> appear on the grid</li>
            <li>Overlapping sections at the same time will be automatically merged</li>
        </ul>
        
        <strong>Steps:</strong>
        <ol>
            <li>Paste your class schedule from Self-Service</li>
            <li>Enter your office hours</li>
            <li>Add a page title (e.g., "Winter 2026 Schedule")</li>
            <li>Click Generate and download the HTML file</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    raw_schedule = st.text_area(
        "1. Paste Class Schedule:",
        height=150,
        placeholder="ENGL-1181-S1601\nM/W 12:00 PM - 1:55 PM\nENGL-1181-S1602\nM/W 12:00 PM - 1:55 PM"
    )
    
    oh_col1, oh_col2 = st.columns([20, 1])
    with oh_col1:
        oh_text = st.text_input(
            "2. Office Hours:",
            placeholder="M-Th 11-1, Fri 9-10"
        )
    with oh_col2:
        st.markdown("<div style='height: 32px'></div>", unsafe_allow_html=True)  # Spacer to align with input
        st.popover("ℹ️").markdown("""
**Supported formats:**

• `M-Th 11-1, Fri 9-10`
• `Mon/Wed 10-12`
• `Virtual Tue 5-6`
• `Monday: 11 AM-12 PM, 2-3 PM; 5-6 PM (virtual)`

**Tips:**
- Use commas or semicolons to separate time slots
- Add "virtual" anywhere to mark virtual hours
- Full day names or abbreviations both work
""")
    
    title_text = st.text_input("3. Page Title:", value="Winter 2026 Schedule")

    if st.button("Generate Door Sign", type="primary"):
        if not raw_schedule:
            st.warning("Please paste your schedule.")
            st.stop()
            
        with st.spinner("Generating door sign..."):
            events = []
            online_data = {}
            lines = raw_schedule.split('\n')
            current_class_name = None
            current_section = None

            # Parse schedule
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify Class + Section
                class_match = re.search(r'ENGL[- ](\d+)[- ]([A-Z0-9]+)', line)
                if class_match:
                    current_class_name = f"ENGL {class_match.group(1)}"
                    current_section = class_match.group(2)
                    full_code = f"{current_class_name} {current_section}"
                    if current_section.startswith('O'):
                        if full_code not in online_data:
                            online_data[full_code] = ""

                # Look for Start Date Month
                date_match = re.search(r'(\d{1,2})/\d{1,2}/\d{2,4}', line)
                if date_match and current_class_name:
                    full_code = f"{current_class_name} {current_section}"
                    if full_code in online_data:
                        m_idx = int(date_match.group(1))
                        online_data[full_code] = f" ({MONTHS[m_idx]} start)"

                # Look for Time/Day pattern
                t_match = re.search(
                    r'([MTWRFSh/]+)\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)',
                    line
                )
                
                if t_match and current_class_name:
                    full_code = f"{current_class_name} {current_section}"
                    if full_code in online_data:
                        del online_data[full_code]
                    
                    # Parse days
                    days_list = []
                    raw_days = t_match.group(1)
                    if 'M' in raw_days:
                        days_list.append('M')
                    if 'T' in raw_days:
                        days_list.append('T')
                    if 'W' in raw_days:
                        days_list.append('W')
                    if 'R' in raw_days or 'Th' in raw_days:
                        days_list.append('Th')
                    if 'F' in raw_days:
                        days_list.append('F')
                    
                    start_val = get_minutes(t_match.group(2))
                    end_val = get_minutes(t_match.group(3))
                    
                    # Determine location
                    room_match = re.search(r'\b([A-Z]{1,3}-\d{3,4})\b', line)
                    loc = (
                        "Remote" if "remote" in line.lower() 
                        else (room_match.group(1) if room_match else "")
                    )

                    # Check for duplicates and merge
                    duplicate_found = False
                    for existing in events:
                        if (existing['start'] == start_val and 
                            existing['end'] == end_val and 
                            set(existing['days']) == set(days_list)):
                            if current_class_name in existing['name']:
                                if current_section not in existing['name']:
                                    existing['name'] += f"/{current_section}"
                                duplicate_found = True
                                break
                    
                    if not duplicate_found:
                        events.append({
                            "type": "class",
                            "name": full_code,
                            "days": days_list,
                            "start": start_val,
                            "end": end_val,
                            "loc": loc
                        })

            # Parse Office Hours - flexible parser for multiple formats
            # Supported formats:
            # - "M-Th 11-1, Fri 9-10"
            # - "Mon/Wed 10-12, Virtual Mon-Tue 5-6"
            # - "Monday: 11 AM-12 PM, 2-3 PM (in-person); 5-6 PM (virtual)"
            # - "Tuesday: 11 AM-12 PM (in-person); 5-6 PM (virtual)"
            
            day_map_list = ['M', 'T', 'W', 'Th', 'F']
            day_name_to_idx = {
                'MONDAY': 0, 'MON': 0, 'M': 0,
                'TUESDAY': 1, 'TUE': 1, 'T': 1,
                'WEDNESDAY': 2, 'WED': 2, 'W': 2,
                'THURSDAY': 3, 'THU': 3, 'TH': 3, 'R': 3,
                'FRIDAY': 4, 'FRI': 4, 'F': 4
            }
            
            def parse_oh_time_flexible(time_str):
                """Parse time in various formats: '11 AM', '11:00 AM', '11', '2-3 PM', etc."""
                time_str = time_str.strip().upper()
                
                # Handle "11 AM", "11:00 AM", "2 PM", "2:30 PM"
                match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?', time_str)
                if match:
                    h = int(match.group(1))
                    m = int(match.group(2)) if match.group(2) else 0
                    period = match.group(3)
                    
                    if period == 'PM' and h != 12:
                        h += 12
                    elif period == 'AM' and h == 12:
                        h = 0
                    elif period is None:
                        # No AM/PM - assume PM for typical office hours (1-7)
                        if 1 <= h <= 7:
                            h += 12
                    
                    return h * 60 + m
                return 0
            
            def extract_time_ranges(text, inherit_period=None):
                """Extract all time ranges from text, returns list of (start_min, end_min, is_virtual)"""
                ranges = []
                text_upper = text.upper()
                is_virtual = 'VIRTUAL' in text_upper
                
                # Pattern for "11 AM-12 PM", "11:00 AM - 12:00 PM", "2-3 PM", "5-6 PM"
                time_range_pattern = r'(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)\s*[-–—]\s*(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)'
                
                for match in re.finditer(time_range_pattern, text, re.IGNORECASE):
                    start_str = match.group(1).strip()
                    end_str = match.group(2).strip()
                    
                    # If end has AM/PM but start doesn't, inherit it
                    end_period_match = re.search(r'(AM|PM)', end_str, re.IGNORECASE)
                    start_period_match = re.search(r'(AM|PM)', start_str, re.IGNORECASE)
                    
                    if end_period_match and not start_period_match:
                        # Append the period to start time for parsing
                        start_str = start_str + ' ' + end_period_match.group(1)
                    
                    s_min = parse_oh_time_flexible(start_str)
                    e_min = parse_oh_time_flexible(end_str)
                    
                    if e_min <= s_min:
                        e_min += 12 * 60  # Assume crossed noon
                    
                    if s_min > 0 and e_min > s_min:
                        ranges.append((s_min, e_min, is_virtual))
                
                return ranges
            
            def extract_days(text):
                """Extract days from text, handling various formats"""
                text_upper = text.upper()
                found_days = []
                
                # First check for day ranges like "M-TH", "MON-FRI", "MONDAY-THURSDAY"
                range_pattern = r'\b(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|MON|TUE|WED|THU|FRI|M|T|W|TH|R|F)\s*[-–—]\s*(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|MON|TUE|WED|THU|FRI|M|T|W|TH|R|F)\b'
                range_match = re.search(range_pattern, text_upper)
                
                if range_match:
                    start_day = range_match.group(1)
                    end_day = range_match.group(2)
                    start_idx = day_name_to_idx.get(start_day)
                    end_idx = day_name_to_idx.get(end_day)
                    if start_idx is not None and end_idx is not None:
                        return day_map_list[start_idx:end_idx + 1]
                
                # Check for slash-separated days like "Mon/Wed" or "M/W"
                slash_pattern = r'\b(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|MON|TUE|WED|THU|FRI|M|T|W|TH|R|F)(?:\s*/\s*(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|MON|TUE|WED|THU|FRI|M|T|W|TH|R|F))+\b'
                slash_match = re.search(slash_pattern, text_upper)
                if slash_match:
                    slash_text = slash_match.group(0)
                    for day_name in re.split(r'\s*/\s*', slash_text):
                        day_name = day_name.strip()
                        if day_name in day_name_to_idx:
                            d = day_map_list[day_name_to_idx[day_name]]
                            if d not in found_days:
                                found_days.append(d)
                    if found_days:
                        return found_days
                
                # Check for individual day names (full or abbreviated)
                # Order matters - check longer names first
                for day_name in ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 
                                 'MON', 'TUE', 'WED', 'THU', 'FRI', 'TH']:
                    if day_name in text_upper:
                        d = day_map_list[day_name_to_idx[day_name]]
                        if d not in found_days:
                            found_days.append(d)
                
                # Only check single letters if no full names found
                if not found_days:
                    # Be careful with single letters - use word boundaries
                    for letter, idx in [('M', 0), ('T', 1), ('W', 2), ('R', 3), ('F', 4)]:
                        if re.search(rf'\b{letter}\b', text_upper):
                            d = day_map_list[idx]
                            if d not in found_days:
                                found_days.append(d)
                
                return found_days
            
            # Split by semicolons first (separates different day groups)
            # Then check for day labels with colons (like "Monday:")
            oh_segments = []
            
            # Check if input uses "Day:" format (like from syllabus)
            if re.search(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday)\s*:', oh_text, re.IGNORECASE):
                # Split by day labels
                day_label_pattern = r'((?:Monday|Tuesday|Wednesday|Thursday|Friday)\s*:)'
                parts = re.split(day_label_pattern, oh_text, flags=re.IGNORECASE)
                
                current_day = None
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    if re.match(r'(Monday|Tuesday|Wednesday|Thursday|Friday)\s*:', part, re.IGNORECASE):
                        current_day = part.rstrip(':').strip()
                    elif current_day:
                        # This part contains times for current_day
                        # Split by semicolons for different time slots
                        for time_slot in re.split(r';', part):
                            time_slot = time_slot.strip()
                            if time_slot:
                                oh_segments.append(f"{current_day} {time_slot}")
            else:
                # Original format - split by comma or semicolon
                for segment in re.split(r'[;,]', oh_text):
                    segment = segment.strip()
                    if segment:
                        oh_segments.append(segment)
            
            # Process each segment
            for segment in oh_segments:
                if not segment:
                    continue
                
                found_days = extract_days(segment)
                time_ranges = extract_time_ranges(segment)
                
                for s_min, e_min, is_virtual in time_ranges:
                    if found_days and s_min > 0:
                        events.append({
                            "type": "oh",
                            "name": "Virtual Office Hours" if is_virtual else "Office Hours",
                            "days": found_days,
                            "start": s_min,
                            "end": e_min,
                            "loc": ""
                        })

            # Generate HTML
            if events:
                all_times = [e['start'] for e in events] + [e['end'] for e in events]
                start_hr = max(0, (min(all_times) // 60) - 1)
                end_hr = min(23, (max(all_times) // 60) + 1)
            else:
                start_hr, end_hr = 9, 17

            # Check if any events occur on Friday
            has_friday = any('F' in ev['days'] for ev in events)
            num_day_cols = 5 if has_friday else 4
            day_headers = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'] if has_friday else ['Mon', 'Tue', 'Wed', 'Thu']

            total_slots = (end_hr - start_hr) * 4
            html_events = ""
            colors_cool = ["#e8f4f8", "#e3f2fd", "#e0f2f1", "#f3e5f5", "#fff3e0", "#f1f8e9"]
            color_map = {}
            col_map = {"M": 2, "T": 3, "W": 4, "Th": 5, "F": 6} if has_friday else {"M": 2, "T": 3, "W": 4, "Th": 5}
            
            for ev in events:
                start_off = ev['start'] - (start_hr * 60)
                end_off = ev['end'] - (start_hr * 60)
                row_s = int(start_off / 15) + 2
                row_span = max(1, int((end_off - start_off) / 15))
                
                if ev['type'] == 'oh':
                    bg, border = "#fff8e1", "#d84315"
                else:
                    if ev['name'] not in color_map:
                        color_map[ev['name']] = colors_cool[len(color_map) % len(colors_cool)]
                    bg, border = color_map[ev['name']], "#546e7a"
                
                for d in ev['days']:
                    if d in col_map:
                        loc_h = f"<br>{ev['loc']}" if ev['loc'] else ""
                        html_events += (
                            f'<div class="event" style="grid-column:{col_map[d]}; '
                            f'grid-row:{row_s}/span {row_span}; background:{bg}; '
                            f'border-left:4px solid {border}; color:#000;">'
                            f'<strong>{ev["name"]}</strong>{loc_h}</div>'
                        )
            
            # Generate time labels (start from second hour to avoid overlap with header)
            html_times = ""
            for h in range(start_hr, end_hr + 1):
                r = (h - start_hr) * 4 + 2
                hour_label = f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"
                # Skip first time label to avoid header overlap
                if h > start_hr:
                    html_times += f'<div class="time-label" style="grid-row:{r};">{hour_label}</div>'
                html_times += f'<div class="grid-line" style="grid-row:{r};"></div>'

            # Online classes section
            online_list = [f"{k}{v}" for k, v in online_data.items()]
            online_html = ""
            if online_list:
                online_html = (
                    f"<div style='margin-top:30px; border-top:2px solid #eee; "
                    f"padding-top:10px; width:100%; max-width:850px; text-align:center;'>"
                    f"<strong>Online Classes:</strong><br>{', '.join(online_list)}</div>"
                )
            
            # Build day headers HTML
            day_headers_html = "\n        ".join([f'<div class="header">{d}</div>' for d in day_headers])
            
            # Final HTML
            final_html = f"""<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        font-family: 'Segoe UI', sans-serif;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    h1 {{
        text-align: center;
        font-weight: 300;
        font-size: 28px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #37474f;
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 2px solid #90a4ae;
    }}
    .calendar {{
        display: grid;
        grid-template-columns: 60px repeat({num_day_cols}, 1fr);
        grid-template-rows: 35px repeat({total_slots}, 1fr);
        width: 100%;
        max-width: 850px;
        border: none;
    }}
    .header {{
        font-weight: 600;
        text-align: center;
        border-bottom: 1px solid #ccc;
        font-size: 15px;
        padding-top: 5px;
        color: #455a64;
    }}
    .time-label {{
        font-size: 10px;
        color: #444;
        text-align: right;
        padding-right: 12px;
        transform: translateY(-50%);
    }}
    .grid-line {{
        grid-column: 2 / span {num_day_cols};
        border-top: 1px solid #eee;
        height: 0;
    }}
    .event {{
        margin: 1px;
        padding: 4px;
        font-size: 11px;
        border-radius: 0px;
        line-height: 1.2;
        print-color-adjust: exact;
        -webkit-print-color-adjust: exact;
        overflow: hidden;
    }}
    @media print {{
        @page {{ margin: 0.5in; }}
        .calendar {{ height: auto; }}
    }}
</style>
</head>
<body>
    <h1>{title_text}</h1>
    <div class="calendar">
        <div class="header" style="grid-column:1"></div>
        {day_headers_html}
        {html_times}
        {html_events}
    </div>
    {online_html}
</body>
</html>"""
            
            st.success("Door sign generated successfully!")
            
            # Preview
            with st.expander("Preview", expanded=True):
                st.components.v1.html(final_html, height=800, scrolling=True)
            
            st.download_button(
                "Download HTML",
                data=final_html,
                file_name="door_sign.html",
                mime="text/html",
                type="primary"
            )

# ==========================================
# TOOL 3: FACULTY ASSIGNMENT SHEET HELPER
# ==========================================
elif tool_choice == "Assignment Sheet Helper":
    st.header("Faculty Assignment Sheet Helper")
    
    with st.expander("How to Use This Tool", expanded=True):
        st.markdown("""
        <div class="instruction-box">
        <strong>This tool converts your Self-Service schedule into FAS table format.</strong>
        
        <strong>Steps:</strong>
        <ol>
            <li>Copy your schedule from Self-Service</li>
            <li>Paste it into the text area below</li>
            <li>Click Generate to create the table</li>
            <li>Review and edit the data if needed</li>
            <li>Copy the tab-separated values at the bottom</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    messy_text = st.text_area("Paste Schedule from Self-Service:", height=300)
    
    if st.button("Generate FAS Table Rows", type="primary"):
        if not messy_text:
            st.warning("Please paste some text.")
            st.stop()
        
        with st.spinner("Parsing schedule..."):
            course_pattern = r'([A-Z]{3,4}-\d{4}-[A-Z0-9]+)'
            starts = [m.start() for m in re.finditer(course_pattern, messy_text)]
            starts.append(len(messy_text))
            
            blocks = [messy_text[starts[i]:starts[i + 1]] for i in range(len(starts) - 1)]
            rows = []
            
            for block in blocks:
                name_match = re.search(course_pattern, block)
                if not name_match:
                    continue
                
                f_code = name_match.group(1)
                c_num = f_code.split('-')[1]
                s_code = f_code.split('-')[2]
                
                cr, cont, eq = HOUR_MAP.get(c_num, (3, 3, 3))
                
                # Extract dates
                date_finds = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', block)
                b_date = date_finds[0] if date_finds else ""
                e_date = date_finds[-1] if date_finds else ""
                
                # Extract time
                t_match = re.search(
                    r'(\d{1,2}:\d{2}(?:\s*[AP]M)?\s*-\s*\d{1,2}:\d{2}\s*[AP]M)',
                    block,
                    re.I
                )
                time_s = t_match.group(1).upper() if t_match else ""
                
                # Extract days
                days_f = set()
                if t_match:
                    up_block = block.upper()
                    if "M/W" in up_block or "MW" in up_block:
                        days_f.update(["Mon", "Wed"])
                    if "T/TH" in up_block or "TTH" in up_block or "T/R" in up_block:
                        days_f.update(["Tue", "Thu"])
                    if re.search(r'\bM\b', up_block):
                        days_f.add("Mon")
                    if re.search(r'\bT\b', up_block):
                        days_f.add("Tue")
                    if re.search(r'\bW\b', up_block):
                        days_f.add("Wed")
                    if re.search(r'\bR\b', up_block) or "TH" in up_block:
                        days_f.add("Thu")
                    if re.search(r'\bF\b', up_block):
                        days_f.add("Fri")
                
                # Extract room
                physical = ""
                room_search = re.search(r'SOU-([A-Z]),\s*(\d+)', block)
                if room_search:
                    physical = f"S{room_search.group(1)}-{room_search.group(2)}"
                
                room_d = physical if physical else ("Remote" if "REMOTE" in block.upper() else "")
                
                rows.append({
                    "Course Code /Section": f_code.replace("-", " "),
                    "Cr Hrs": cr,
                    "Cont Hrs": cont,
                    "Eq Hrs": eq,
                    "Begin Date": b_date,
                    "End Date": e_date,
                    "Mon": time_s if "Mon" in days_f else "",
                    "Tue": time_s if "Tue" in days_f else "",
                    "Wed": time_s if "Wed" in days_f else "",
                    "Thu": time_s if "Thu" in days_f else "",
                    "Fri": time_s if "Fri" in days_f else "",
                    "Room": room_d,
                    "Online": "Yes" if "ONLINE" in block.upper() and not time_s else ""
                })
            
            if rows:
                df = pd.DataFrame(rows)
                
                st.success(f"Generated {len(rows)} rows")
                
                edited_df = st.data_editor(
                    df,
                    num_rows="dynamic",
                    use_container_width=True
                )
                
                st.markdown("---")
                st.markdown("### Tab-Separated Values (Copy and paste into spreadsheet)")
                
                tsv_output = edited_df.to_csv(sep='\t', index=False, header=False)
                st.code(tsv_output, language="text")
                
                st.download_button(
                    "Download as TSV",
                    data=tsv_output,
                    file_name="faculty_assignment_sheet.tsv",
                    mime="text/tab-separated-values"
                )
            else:
                st.warning("No course data found in the pasted text.")

# ==========================================
# TOOL 4: DATE SHIFTER & CALCULATOR
# ==========================================
elif tool_choice == "Date Shifter & Calculator":
    st.header("Date Shift Calculator")
    
    with st.expander("How to Use This Tool", expanded=True):
        st.markdown("""
        <div class="instruction-box">
        <strong>This tool shifts all dates in a calendar file forward or backward.</strong>
        
        <strong>Use Cases:</strong>
        <ul>
            <li>Reusing a previous semester's calendar for a new semester</li>
            <li>Adjusting due dates when the semester start date changes</li>
            <li>Accounting for Canvas's date handling quirks</li>
        </ul>
        
        <strong>Steps:</strong>
        <ol>
            <li>Enter the old reference date (e.g., first day of old semester)</li>
            <li>Enter the new reference date (e.g., first day of new semester)</li>
            <li>Check the Canvas adjustment box if needed (+1 day)</li>
            <li>Upload your old .ics calendar file</li>
            <li>Download the shifted version</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    calc_col1, calc_col2, calc_col3 = st.columns(3)
    
    with calc_col1:
        old_ref = st.date_input("Old Reference Date", value=datetime(2025, 8, 25))
    with calc_col2:
        new_ref = st.date_input("New Reference Date", value=datetime(2026, 1, 12))
    with calc_col3:
        canvas_adj = st.checkbox("Add +1 day for Canvas?", value=True)
    
    final_shift = (new_ref - old_ref).days + (1 if canvas_adj else 0)
    
    st.metric("Total Days to Shift", f"{final_shift} days")
    
    st.markdown("---")
    
    shift_file = st.file_uploader("Upload OLD .ics file", type="ics")
    
    if shift_file:
        with st.spinner("Parsing calendar..."):
            calendar = parse_calendar_file(shift_file.read().decode("utf-8"))
        
        if not calendar:
            st.stop()
        
        # Show preview of changes
        st.markdown("### Preview of Changes")
        
        sample_events = list(calendar.events)[:5]  # Show first 5 events
        preview_data = []
        
        for e in sample_events:
            old_date = e.begin.format('YYYY-MM-DD HH:mm')
            new_date = (e.begin + timedelta(days=final_shift)).format('YYYY-MM-DD HH:mm')
            preview_data.append({
                "Event": e.name[:50] + "..." if len(e.name) > 50 else e.name,
                "Old Date": old_date,
                "New Date": new_date
            })
        
        if preview_data:
            st.table(pd.DataFrame(preview_data))
        
        if st.button(f"Generate Shifted ICS (+{final_shift} days)", type="primary"):
            with st.spinner("Shifting dates..."):
                new_calendar = Calendar()
                
                for e in calendar.events:
                    e.begin += timedelta(days=final_shift)
                    e.end += timedelta(days=final_shift)
                    new_calendar.events.add(e)
                
                st.success(f"Shifted {len(calendar.events)} events by {final_shift} days!")
                
                st.download_button(
                    "Download Shifted ICS",
                    str(new_calendar),
                    "shifted_calendar.ics",
                    mime="text/calendar"
                )

# --- FOOTER ---
st.markdown("---")
st.caption("Contact Sarah Karlis with any questions.")
