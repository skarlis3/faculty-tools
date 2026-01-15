import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import base64

st.set_page_config(page_title="PDF Merger & Editor", page_icon="📄", layout="wide")

# Initialize session state
if 'pdf_files' not in st.session_state:
    st.session_state.pdf_files = []
if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = 0
if 'editing_file_idx' not in st.session_state:
    st.session_state.editing_file_idx = None

def extract_pages_from_pdf(pdf_bytes):
    """Extract individual pages from a PDF"""
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = []
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        pages.append({
            'page_num': i + 1,
            'bytes': output.read()
        })
    return pages

def add_page_numbers(input_pdf_bytes, position='bottom-center', start_num=1):
    """Add page numbers to PDF"""
    reader = PdfReader(BytesIO(input_pdf_bytes))
    writer = PdfWriter()
    
    for page_num, page in enumerate(reader.pages):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        positions = {
            'bottom-center': (page_width / 2, 30),
            'bottom-right': (page_width - 50, 30),
            'bottom-left': (50, 30),
            'top-center': (page_width / 2, page_height - 30),
            'top-right': (page_width - 50, page_height - 30),
            'top-left': (50, page_height - 30),
        }
        
        x, y = positions.get(position, (page_width / 2, 30))
        
        can.setFont("Helvetica", 10)
        can.drawCentredString(x, y, str(page_num + start_num))
        can.save()
        
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
    
    can.setFont("Helvetica-Bold", 20)
    can.drawString(50, 750, "Table of Contents")
    
    can.setFont("Helvetica", 12)
    y_position = 700
    
    for entry in toc_entries:
        if y_position < 50:
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
    
    if add_toc:
        current_page += 1
    
    all_pages = []
    for pdf_info in pdf_list:
        toc_entries.append({
            'title': pdf_info['toc_title'],
            'page': current_page
        })
        
        # Add pages in order they appear in the pages list
        for page_info in pdf_info['pages']:
            reader = PdfReader(BytesIO(page_info['bytes']))
            all_pages.append(reader.pages[0])
            current_page += 1
    
    if add_toc:
        toc_pdf_bytes = create_toc_page(toc_entries)
        toc_reader = PdfReader(BytesIO(toc_pdf_bytes))
        for page in toc_reader.pages:
            writer.add_page(page)
    
    for page in all_pages:
        writer.add_page(page)
    
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    merged_bytes = output.read()
    
    if page_num_position != 'none':
        merged_bytes = add_page_numbers(merged_bytes, page_num_position, start_num)
    
    return merged_bytes

# UI
st.title("📄 PDF Merger & Editor")
st.markdown("Upload, reorder pages, and merge PDF files with page numbers and table of contents")

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
    st.markdown("✓ Reorder pages within PDFs")
    st.markdown("✓ Add page numbers")
    st.markdown("✓ Generate TOC")
    st.markdown("✓ Delete pages")

# File uploader
uploaded_files = st.file_uploader(
    "Upload PDF files",
    type=['pdf'],
    accept_multiple_files=True,
    help="Upload one or more PDF files to merge",
    key=f"file_uploader_{st.session_state.file_uploader_key}"
)

# Add uploaded files to session state
if uploaded_files:
    for uploaded_file in uploaded_files:
        if not any(f['name'] == uploaded_file.name for f in st.session_state.pdf_files):
            pdf_bytes = uploaded_file.read()
            pages = extract_pages_from_pdf(pdf_bytes)
            st.session_state.pdf_files.append({
                'name': uploaded_file.name,
                'bytes': pdf_bytes,
                'toc_title': uploaded_file.name.replace('.pdf', ''),
                'pages': pages
            })

# Page editing view
if st.session_state.editing_file_idx is not None:
    idx = st.session_state.editing_file_idx
    if idx < len(st.session_state.pdf_files):
        pdf_file = st.session_state.pdf_files[idx]
        
        st.markdown(f"### 📑 Editing Pages: {pdf_file['name']}")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.info(f"Total pages: {len(pdf_file['pages'])}")
        with col2:
            if st.button("✅ Done Editing"):
                st.session_state.editing_file_idx = None
                st.rerun()
        
        st.markdown("---")
        
        # Display pages
        for page_idx, page_info in enumerate(pdf_file['pages']):
            col1, col2, col3, col4 = st.columns([0.5, 3, 1, 1])
            
            with col1:
                st.markdown(f"**{page_idx + 1}**")
            
            with col2:
                st.text(f"Page {page_info['page_num']} from original")
            
            with col3:
                col_up, col_down = st.columns(2)
                with col_up:
                    if st.button("⬆️", key=f"page_up_{page_idx}", disabled=(page_idx == 0)):
                        pdf_file['pages'][page_idx], pdf_file['pages'][page_idx - 1] = \
                            pdf_file['pages'][page_idx - 1], pdf_file['pages'][page_idx]
                        st.rerun()
                with col_down:
                    if st.button("⬇️", key=f"page_down_{page_idx}", 
                               disabled=(page_idx == len(pdf_file['pages']) - 1)):
                        pdf_file['pages'][page_idx], pdf_file['pages'][page_idx + 1] = \
                            pdf_file['pages'][page_idx + 1], pdf_file['pages'][page_idx]
                        st.rerun()
            
            with col4:
                if st.button("🗑️", key=f"page_remove_{page_idx}"):
                    pdf_file['pages'].pop(page_idx)
                    if len(pdf_file['pages']) == 0:
                        st.session_state.pdf_files.pop(idx)
                        st.session_state.editing_file_idx = None
                    st.rerun()

# Main file list view
elif st.session_state.pdf_files:
    st.markdown("### 📚 Files to Merge")
    
    for idx, pdf_file in enumerate(st.session_state.pdf_files):
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 1.5, 1])
        
        with col1:
            st.markdown(f"**#{idx + 1}**")
        
        with col2:
            st.text(f"{pdf_file['name']} ({len(pdf_file['pages'])} pages)")
        
        with col3:
            new_title = st.text_input(
                "TOC Title",
                value=pdf_file['toc_title'],
                key=f"toc_{idx}",
                label_visibility="collapsed"
            )
            st.session_state.pdf_files[idx]['toc_title'] = new_title
        
        with col4:
            col_up, col_down, col_edit = st.columns(3)
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
            with col_edit:
                if st.button("✏️", key=f"edit_{idx}", help="Edit pages"):
                    st.session_state.editing_file_idx = idx
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
            st.session_state.file_uploader_key += 1
            st.session_state.editing_file_idx = None
            st.rerun()

else:
    st.info("👆 Upload PDF files to get started")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Built with Streamlit • Upload PDFs • Reorder Pages • Merge • Add Page Numbers • Generate TOC"
    "</div>",
    unsafe_allow_html=True
)
