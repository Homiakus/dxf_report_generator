import os
import tempfile
import shutil
import streamlit as st
import ezdxf
import pandas as pd

from core import (
    calculate_total_length,
    calculate_precise_area,
    render_dxf_to_image,
    parse_filename_metadata
)
from reports import create_pdf_report, create_excel_report

st.set_page_config(page_title="DXF Report Generator", layout="wide")

st.title("DXF Cost Estimator & Report Generator")

with st.sidebar.form("cost_form"):
    st.header("Cost Settings")
    cost_per_meter = st.number_input("Cutting Cost (per meter)", min_value=0.0, value=10.0, step=1.0)
    cost_per_square_meter = st.number_input("Material Cost (per m²)", min_value=0.0, value=50.0, step=1.0)
    # The submit button triggers the reactive calculation and report regeneration
    recalculate_btn = st.form_submit_button("Update Costs")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Filename Metadata Parsing**
Upload files named like:
`name_material_thickness_quantity.dxf`
e.g. `bracket_steel_3mm_5.dxf`
Fallback: `name_quantity.dxf` or just `name.dxf`
""")

uploaded_files = st.file_uploader("Upload DXF Files", accept_multiple_files=True, type=['dxf'])

if uploaded_files:
    if st.button("Process Files & Generate Reports"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Clean up existing temp directory if it exists to prevent disk leak
        if 'temp_dir' in st.session_state and st.session_state['temp_dir']:
            if os.path.exists(st.session_state['temp_dir']):
                shutil.rmtree(st.session_state['temp_dir'], ignore_errors=True)

        # Initialize session state for persistent data
        st.session_state['data'] = []
        st.session_state['images'] = []
        st.session_state['temp_dir'] = tempfile.mkdtemp()

        total_files = len(uploaded_files)
        for i, uploaded_file in enumerate(uploaded_files):
            filename = uploaded_file.name
            status_text.text(f"Processing {filename}...")

            # Save uploaded file to temp dir
            dxf_path = os.path.join(st.session_state['temp_dir'], filename)
            with open(dxf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                # Read DXF
                doc = ezdxf.readfile(dxf_path)
                msp = doc.modelspace()

                if len(msp) == 0:
                    st.warning(f"No objects in {filename}, skipping.")
                    continue

                # Calculations
                total_length = calculate_total_length(doc)
                area = calculate_precise_area(doc)
                metadata = parse_filename_metadata(filename)

                data_item = {
                    'File': filename,
                    'Name': metadata['name'],
                    'Material': metadata['material'],
                    'Thickness': metadata['thickness'],
                    'Quantity': metadata['quantity'],
                    'Length': total_length,
                    'Area': area
                }
                st.session_state['data'].append(data_item)

                # Image rendering
                image_filename = f"{metadata['name']}.png"
                image_path = os.path.join(st.session_state['temp_dir'], image_filename)
                success = render_dxf_to_image(doc, image_path)

                if success and os.path.exists(image_path):
                    st.session_state['images'].append({
                        'filename': filename,
                        'image_path': image_path,
                        'total_length': total_length,
                        'quantity': metadata['quantity'],
                        'area': area
                    })
            except Exception as e:
                st.error(f"Error processing {filename}: {e}")

            progress_bar.progress((i + 1) / total_files)

        status_text.text("Generating reports...")
        st.session_state['reports_generated'] = True
        st.session_state['pdf_path'] = os.path.join(st.session_state['temp_dir'], "report.pdf")
        st.session_state['excel_path'] = os.path.join(st.session_state['temp_dir'], "report.xlsx")

        if st.session_state['images']:
            create_pdf_report(st.session_state['images'], st.session_state['data'], st.session_state['pdf_path'], cost_per_meter, cost_per_square_meter)
        create_excel_report(st.session_state['data'], st.session_state['excel_path'], cost_per_meter, cost_per_square_meter)

        status_text.text("Done!")

# Display UI if reports are generated
if st.session_state.get('reports_generated'):

    # If the user updated the cost multipliers, regenerate the reports to keep them in sync
    if recalculate_btn:
        pdf_path = st.session_state.get('pdf_path')
        excel_path = st.session_state.get('excel_path')
        if st.session_state.get('images'):
            create_pdf_report(st.session_state['images'], st.session_state['data'], pdf_path, cost_per_meter, cost_per_square_meter)
        create_excel_report(st.session_state['data'], excel_path, cost_per_meter, cost_per_square_meter)
        st.success("Costs updated and reports regenerated successfully!")

    # Calculate Costs for Preview
    preview_data = []
    grand_total = 0.0
    for item in st.session_state['data']:
        cutting_cost = (item['Length'] / 1000) * cost_per_meter * item['Quantity']
        material_cost = item['Area'] * cost_per_square_meter * item['Quantity']
        total = cutting_cost + material_cost
        grand_total += total

        preview_item = item.copy()
        preview_item['Cutting Cost'] = round(cutting_cost, 2)
        preview_item['Material Cost'] = round(material_cost, 2)
        preview_item['Total'] = round(total, 2)
        preview_data.append(preview_item)

    # Display Preview
    st.subheader("Preview Data")
    df_preview = pd.DataFrame(preview_data)
    st.dataframe(df_preview, use_container_width=True)
    st.write(f"**Grand Total Cost:** {grand_total:.2f}")

    # Download buttons
    col1, col2 = st.columns(2)

    pdf_path = st.session_state.get('pdf_path', '')
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            col1.download_button(
                label="Download PDF Report",
                data=f,
                file_name="dxf_report.pdf",
                mime="application/pdf"
            )

    excel_path = st.session_state.get('excel_path', '')
    if os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            col2.download_button(
                label="Download Excel Report",
                data=f,
                file_name="dxf_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Show Images
    st.subheader("Generated Previews")
    images = st.session_state.get('images', [])
    cols = st.columns(min(3, len(images))) if images else []
    for i, img_info in enumerate(images):
        with cols[i % len(cols)]:
            st.image(img_info['image_path'], caption=img_info['filename'])

    if st.button("Clear Results"):
        # Explicitly clean up temp dir on clear
        temp_dir = st.session_state.get('temp_dir')
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

        for key in ['reports_generated', 'data', 'images', 'temp_dir', 'pdf_path', 'excel_path']:
            st.session_state.pop(key, None)
        st.rerun()
