import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import tempfile
import os

st.set_page_config(page_title="PDF Merger & Editor", page_icon="📄", layout="wide")

# Initialize session state
if 'pdf_files' not in st.session_state:
    st.session_state.pdf_files = []

def add_page_numbers(input_pdf_bytes, position='bottom-center', start_num=1):
    """Add page numbers to PDF"""
    reader = PdfReader(BytesIO(input_pdf_bytes))
    writer = PdfWriter()
    
    for page_num, page in enumerate(reader.pages):
        # Create a new PDF with the page number
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        # Get page dimensions
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        # Set position
        positions = {
            'bottom-center': (page_width / 2, 30),
            'bottom-right': (page_width - 50, 30),
            'bottom-left': (50, 30),
            'top-center': (page_width / 2, page_height - 30),
            'top-right': (page_width - 50, page_height - 30),
            'top-left': (50, page_height - 30),
        }
        
        x, y = positions.get(position, (page_width / 2, 30))
        
        # Draw page number
        can.setFont("Helvetica", 10)
        can.drawCentredString(x, y, str(page_num + start_num))
        can.save()
        
        # Merge the page number with the original page
        packet.seek(0)
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)
    
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()

def create_toc_page(toc_entries):
    """Create a table of contents page"""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Title
    can.setFont("Helvetica-Bold", 20)
    can.drawString(50, 750, "Table of Contents")
    
    # TOC entries
    can.setFont("Helvetica", 12)
    y_position = 700
    
    for idx, entry in enumerate(toc_entries):
        if y_position < 50:  # New page if needed
            can.showPage()
            y_position = 750
        can.drawString(70, y_position, f"{entry['title']}")
        can.drawRightString(550, y_position, f"Page {entry['page']}")
        y_position -= 25
    
    can.save()
    packet.seek(0)
    return packet.read()

def merge_pdfs(pdf_list, add_toc=True, page_num_position='bottom-center', start_num=1):
    """Merge multiple PDFs with optional TOC and page numbers"""
    writer = PdfWriter()
    toc_entries = []
    current_page = 1
    
    # Add TOC placeholder page count
    if add_toc:
        current_page += 1
    
    # Collect all pages and build TOC
    all_pages = []
    for pdf_info in pdf_list:
        reader = PdfReader(BytesIO(pdf_info['bytes']))
        num_pages = len(reader.pages)
        
        toc_entries.append({
            'title': pdf_info['toc_title'],
            'page': current_page
        })
        
        for page in reader.pages:
            all_pages.append(page)
        
        current_page += num_pages
    
    # Create TOC if requested
    if add_toc:
        toc_pdf_bytes = create_toc_page(toc_entries)
        toc_reader = PdfReader(BytesIO(toc_pdf_bytes))
        for page in toc_reader.pages:
            writer.add_page(page)
    
    # Add all pages
    for page in all_pages:
        writer.add_page(page)
    
    # Write to bytes
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    merged_bytes = output.read()
    
    # Add page numbers
    if page_num_position != 'none':
        merged_bytes = add_page_numbers(merged_bytes, page_num_position, start_num)
    
    return merged_bytes

# UI
st.title("📄 PDF Merger & Editor")
st.markdown("Upload, reorder, and merge PDF files with page numbers and table of contents")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    add_toc = st.checkbox("Add Table of Contents", value=True)
    
    page_num_position = st.selectbox(
        "Page Number Position",
        options=['none', 'bottom-center', 'bottom-right', 'bottom-left', 
                'top-center', 'top-right', 'top-left'],
        index=1
    )
    
    start_page_num = st.number_input("Start Page Number", min_value=1, value=1, step=1)
    
    st.markdown("---")
    st.markdown("### Features")
    st.markdown("✓ Merge multiple PDFs")
    st.markdown("✓ Add page numbers")
    st.markdown("✓ Generate TOC")
    st.markdown("✓ Reorder files")

# File uploader
uploaded_files = st.file_uploader(
    "Upload PDF files",
    type=['pdf'],
    accept_multiple_files=True,
    help="Upload one or more PDF files to merge"
)

# Add uploaded files to session state
if uploaded_files:
    for uploaded_file in uploaded_files:
        # Check if file already exists
        if not any(f['name'] == uploaded_file.name for f in st.session_state.pdf_files):
            st.session_state.pdf_files.append({
                'name': uploaded_file.name,
                'bytes': uploaded_file.read(),
                'toc_title': uploaded_file.name.replace('.pdf', '')
            })

# Display and manage files
if st.session_state.pdf_files:
    st.markdown("### 📚 Files to Merge")
    
    for idx, pdf_file in enumerate(st.session_state.pdf_files):
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 1, 1])
        
        with col1:
            st.markdown(f"**#{idx + 1}**")
        
        with col2:
            st.text(pdf_file['name'])
        
        with col3:
            new_title = st.text_input(
                "TOC Title",
                value=pdf_file['toc_title'],
                key=f"toc_{idx}",
                label_visibility="collapsed"
            )
            st.session_state.pdf_files[idx]['toc_title'] = new_title
        
        with col4:
            col_up, col_down = st.columns(2)
            with col_up:
                if st.button("⬆️", key=f"up_{idx}", disabled=(idx == 0)):
                    st.session_state.pdf_files[idx], st.session_state.pdf_files[idx - 1] = \
                        st.session_state.pdf_files[idx - 1], st.session_state.pdf_files[idx]
                    st.rerun()
            with col_down:
                if st.button("⬇️", key=f"down_{idx}", 
                           disabled=(idx == len(st.session_state.pdf_files) - 1)):
                    st.session_state.pdf_files[idx], st.session_state.pdf_files[idx + 1] = \
                        st.session_state.pdf_files[idx + 1], st.session_state.pdf_files[idx]
                    st.rerun()
        
        with col5:
            if st.button("🗑️", key=f"remove_{idx}"):
                st.session_state.pdf_files.pop(idx)
                st.rerun()
    
    st.markdown("---")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Merge & Download PDF", type="primary", use_container_width=True):
            with st.spinner("Processing PDF..."):
                try:
                    merged_pdf = merge_pdfs(
                        st.session_state.pdf_files,
                        add_toc=add_toc,
                        page_num_position=page_num_position,
                        start_num=start_page_num
                    )
                    
                    st.download_button(
                        label="⬇️ Download Merged PDF",
                        data=merged_pdf,
                        file_name="merged_document.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ PDF merged successfully!")
                except Exception as e:
                    st.error(f"❌ Error merging PDFs: {str(e)}")
    
    with col2:
        if st.button("🗑️ Clear All Files", use_container_width=True):
            st.session_state.pdf_files = []
            st.rerun()

else:
    st.info("👆 Upload PDF files to get started")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Built with Streamlit • Upload PDFs • Merge • Add Page Numbers • Generate TOC"
    "</div>",
    unsafe_allow_html=True
)
