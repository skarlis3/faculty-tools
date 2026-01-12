# ==========================================
# TOOL 3: ASSIGNMENT SHEET FILLER (BLOCK-AWARE)
# ==========================================
elif tool_choice == "📋 Assignment Sheet Filler":
    st.header("📋 Faculty Assignment Helper")
    st.markdown("This version scans vertically to catch Remote/Online labels and Room numbers.")
    
    with st.sidebar:
        default_type = st.selectbox("Default Contract Type", ["BASE", "EC", "XXC"])
    
    messy_text = st.text_area(
        "Paste Schedule Text:", 
        height=300,
        placeholder="ENGL-2740-H1602...\n(Wait for the green success message below)"
    )

    if st.button("Generate Spreadsheet Rows", type="primary"):
        if not messy_text:
            st.warning("Please paste some text first.")
        else:
            # NEW STRATEGY: Find every Course Code and treat everything until the next one as a block
            # This regex finds "ENGL-2740-H1602" or similar
            course_pattern = r'([A-Z]{3,4}-\d{4}-[A-Z0-9]+)'
            
            # Find all start positions of course codes
            starts = [m.start() for m in re.finditer(course_pattern, messy_text)]
            starts.append(len(messy_text)) # Add the end of the text
            
            blocks = []
            for i in range(len(starts)-1):
                blocks.append(messy_text[starts[i]:starts[i+1]])

            rows = []
            for block in blocks:
                # 1. Class Name
                name_match = re.search(course_pattern, block)
                if not name_match: continue
                class_name = name_match.group(1).replace("-", " ")

                # 2. Dates
                date_finds = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', block)
                begin_date = date_finds[0] if date_finds else ""
                end_date = date_finds[-1] if date_finds else ""

                # 3. Time & Days
                t_match = re.search(r'(\d{1,2}:\d{2}(?:\s*[AP]M)?\s*-\s*\d{1,2}:\d{2}\s*[AP]M)', block, re.IGNORECASE)
                time_str = t_match.group(1).upper() if t_match else ""
                
                days_found = set()
                if t_match:
                    # Look at the specific line the time was found on for the days
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

                # 4. Room & Remote Logic
                is_remote = "REMOTE" in block.upper() or "ONLINE" in block.upper() or "ZOOM" in block.upper()
                
                room = ""
                room_match = re.search(r'SOU-([A-Z]),\s*(\d+)', block)
                if room_match:
                    room = f"S{room_match.group(1)}-{room_match.group(2)}"
                else:
                    room_alt = re.search(r'\b([A-Z]{1,3}-\d{3,4})\b', block)
                    room = room_alt.group(1) if room_alt else ""
                
                # Priority: If Remote is mentioned in the block, use that for Room
                if is_remote:
                    room = "Remote"

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
                cols = ["Course Code /Section", "Cr Hrs", "Cont Hrs", "Eq Hrs", "Contract Type(s)", "Combined With", "Begin Date", "End Date", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Room", "Online Section"]
                df = pd.DataFrame(rows, columns=cols)
                st.success(f"Parsed {len(df)} classes.")
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                
                st.write("### Excel Output (Copy this)")
                tsv = edited_df.to_csv(sep='\t', index=False, header=False)
                st.code(tsv, language="text")
            else:
                st.error("No classes found. Ensure Course Codes (ENGL-####-####) are in the text.")
