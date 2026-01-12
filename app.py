import streamlit as st
import pandas as pd
from ics import Calendar
from datetime import datetime, timedelta
import re
import random
import requests

# --- PAGE SETUP ---
st.set_page_config(page_title="Faculty Tools", page_icon="💻", layout="wide")

st.title("🎓 Faculty Tools")
st.markdown("Tools to automate your syllabus, door signs, and assignment sheets.")

# --- SIDEBAR NAVIGATION ---
tool_choice = st.sidebar.radio("Select Tool:", 
    ["📅 Syllabus Scheduler", "🚪 Door Sign Generator", "📋 Assignment Sheet Filler", "⏳ ICS Date Shifter"])

# ==========================================
# TOOL 1: SYLLABUS SCHEDULER (Omitted for brevity, keep your current code here)
# ==========================================
if tool_choice == "📅 Syllabus Scheduler":
    st.info("Syllabus Scheduler code remains unchanged.")

# ==========================================
# TOOL 2: DOOR SIGN GENERATOR (Omitted for brevity, keep your current code here)
# ==========================================
elif tool_choice == "🚪 Door Sign Generator":
    st.info("Door Sign Generator code remains unchanged.")

# ==========================================
# TOOL 3: ASSIGNMENT SHEET FILLER (REVAMPED)
# ==========================================
elif tool_choice == "📋 Assignment Sheet Filler":
    st.header("📋 Faculty Assignment Helper")
    st.markdown("Optimized for 'Stacked' schedule text. It will pull Begin/End dates directly from your paste.")
    
    with st.sidebar:
        default_type = st.selectbox("Default Contract Type", ["BASE", "EC", "XXC"])
    
    messy_text = st.text_area(
        "Paste Schedule Text:", 
        height=300,
        placeholder="ENGL-2740-H1602...\n1/12/2026 - 5/6/2026\nW 6:00 PM - 7:25 PM..."
    )

    if st.button("Generate Spreadsheet Rows", type="primary"):
        if not messy_text:
            st.warning("Please paste some text first.")
        else:
            # We split the text by double newlines because each class is a "block"
            blocks = re.split(r'\n\s*\n', messy_text)
            rows = []

            for block in blocks:
                if not block.strip(): continue
                
                # --- 1. Identify Class ---
                class_match = re.search(r'([A-Z]{3,4}-\d{4}-[A-Z0-9]+)', block)
                if not class_match: continue
                class_name = class_match.group(1).replace("-", " ")
                
                # --- 2. Extract Dates ---
                # Look for all instances of MM/DD/YYYY
                date_finds = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', block)
                begin_date = ""
                end_date = ""
                if date_finds:
                    # Sort the found dates just in case, or take first and last
                    begin_date = date_finds[0]
                    end_date = date_finds[-1]

                # --- 3. Extract Time ---
                t_match = re.search(r'(\d{1,2}:\d{2}(?:\s*[AP]M)?\s*-\s*\d{1,2}:\d{2}\s*[AP]M)', block, re.IGNORECASE)
                time_str = t_match.group(1).upper() if t_match else ""

                # --- 4. Extract Days ---
                days_found = set()
                # Look for the line that has the time, the days are usually right before it
                if t_match:
                    # Get the specific line containing the time
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

                # --- 5. Extract Room ---
                # Specifically looking for the "SOU-F, 310" format or "SF-310"
                room = ""
                room_match = re.search(r'SOU-([A-Z]),\s*(\d+)', block)
                if room_match:
                    room = f"S{room_match.group(1)}-{room_match.group(2)}"
                else:
                    # Fallback to standard room search
                    room_alt = re.search(r'\b([A-Z]{1,3}-\d{3,4})\b', block)
                    room = room_alt.group(1) if room_alt else ""
                
                # Remote Check
                is_remote = "Remote" in block or "Online" in block
                if is_remote and not room: room = "Remote"
                
                # --- 6. Build Row ---
                row = {
                    "Course Code /Section": class_name,
                    "Cr Hrs": "", "Cont Hrs": "", "Eq Hrs": "", 
                    "Contract Type(s)": default_type,
                    "Combined With": "",
                    "Begin Date": begin_date,
                    "End Date": end_date,
                    "Mon": time_str if "Mon" in days_found else "",
                    "Tue": time_str if "Tue" in days_found else "",
                    "Wed": time_str if "Wed" in days_found else "",
                    "Thu": time_str if "Thu" in days_found else "",
                    "Fri": time_str if "Fri" in days_found else "",
                    "Sat": time_str if "Sat" in days_found else "",
                    "Room": room,
                    "Online Section": "Yes" if is_remote else ""
                }
                rows.append(row)
            
            if rows:
                cols = [
                    "Course Code /Section", "Cr Hrs", "Cont Hrs", "Eq Hrs", "Contract Type(s)", 
                    "Combined With", "Begin Date", "End Date", 
                    "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", 
                    "Room", "Online Section"
                ]
                df = pd.DataFrame(rows, columns=cols)
                st.success(f"Successfully parsed {len(df)} class blocks.")
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                
                st.write("### Excel Ready Output")
                tsv = edited_df.to_csv(sep='\t', index=False, header=False)
                st.code(tsv, language="text")
                st.caption("Copy the code above and paste into Excel cell A1.")
            else:
                st.error("No class blocks found. Ensure the Course Code (e.g., ENGL-1190-S1602) is present.")

# ==========================================
# TOOL 4: ICS DATE SHIFTER (Keep your current code here)
# ==========================================
elif tool_choice == "⏳ ICS Date Shifter":
    st.info("ICS Date Shifter code remains unchanged.")
