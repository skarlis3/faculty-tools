import streamlit as st
from datetime import datetime
import pandas as pd

# --- PAGE SETUP ---
st.set_page_config(page_title="Sign-In Generator", page_icon="📝", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2em; color: #333; margin-bottom: 0px; }
    .ferpa-warning { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; border: 1px solid #ffeeba; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>📝 Daily Sign-In Sheet Generator</div>", unsafe_allow_html=True)
st.markdown("<div class='ferpa-warning'><strong>🔒 SECURE MODE:</strong> This app is running locally. Student names are processed on your machine and are not sent to the internet.</div>", unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    class_name = st.text_input("Class Name:", value="ENGL 1190")
    class_date = st.date_input("Date:", value=datetime.now())
with col_b:
    sheet_mode = st.radio("Sheet Type:", ["First Week (With Notes)", "Standard (Sign-In Only)"])
    
raw_names = st.text_area("Paste Student List (Messy copy/paste is fine):", height=200, 
                         placeholder="Smith, John\nDoe, Jane\n...or...\nJohn Smith\nJane Doe")

if st.button("Generate Sign-In Sheet", type="primary"):
    # --- PARSING LOGIC ---
    students = []
    lines = raw_names.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Simple parser for "Last, First" or "First Last"
        if "," in line:
            name_parts = line.split(",")
            last = name_parts[0].strip()
            first = name_parts[1].strip().split()[0] 
            students.append({"last": last, "first": first, "display": f"{last}, {first}"})
        else:
            parts = line.split()
            if len(parts) >= 2:
                last = parts[-1]
                first = parts[0]
                students.append({"last": last, "first": first, "display": f"{last}, {first}"})
            elif len(parts) == 1:
                students.append({"last": parts[0], "first": "", "display": parts[0]})
            
    # Sort by Last Name
    students.sort(key=lambda x: x['last'])
    
    # --- HTML GENERATION ---
    table_html = """
    <style>
        @media print {
            @page { margin: 0.5in; }
            body { font-family: sans-serif; }
            .no-print { display: none; }
            button { display: none; }
        }
        body { font-family: 'Segoe UI', sans-serif; color: #000; }
        h1 { text-align: center; margin-bottom: 5px; font-size: 24px; }
        .meta { text-align: center; margin-bottom: 20px; color: #444; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #eee; text-align: left; padding: 10px; border: 1px solid #000; }
        td { padding: 8px; border: 1px solid #000; height: 35px; vertical-align: middle; }
        .col-name { width: 30%; font-weight: bold; }
        .col-sign { width: 35%; }
        .col-note { width: 35%; }
    </style>
    """
    
    date_str = class_date.strftime("%A, %B %d, %Y")
    table_html += f"<h1>{class_name} — Sign In</h1>"
    table_html += f"<div class='meta'>{date_str}</div>"
    
    table_html += "<table><thead><tr>"
    table_html += "<th class='col-name'>Student Name</th>"
    table_html += "<th class='col-sign'>Signature</th>"
    if "First Week" in sheet_mode:
        table_html += "<th class='col-note'>Notes (Nickname/Pronouns)</th>"
    table_html += "</tr></thead><tbody>"
    
    for s in students:
        table_html += f"<tr><td>{s['display']}</td><td></td>"
        if "First Week" in sheet_mode:
            table_html += "<td></td>"
        table_html += "</tr>"
        
    for _ in range(3): # Blank rows
        table_html += "<tr><td></td><td></td>"
        if "First Week" in sheet_mode:
            table_html += "<td></td>"
        table_html += "</tr>"
        
    table_html += "</tbody></table>"
    
    st.download_button("Download Printable HTML", table_html, f"signin_{class_name}.html", "text/html")
