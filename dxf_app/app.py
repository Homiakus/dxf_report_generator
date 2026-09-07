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
    parse_filename_metadata,
    analyze_dxf_artifacts
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

                warnings = analyze_dxf_artifacts(doc)

                data_item = {
                    'File': filename,
                    'Name': metadata['name'],
                    'Material': metadata['material'],
                    'Thickness': metadata['thickness'],
                    'Quantity': metadata['quantity'],
                    'Length': total_length,
                    'Area': area,
                    'Warnings': "\n".join(warnings) if warnings else "OK"
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

    tab_dashboard, tab_editor, tab_images, tab_artifacts = st.tabs(["📊 Дашборд", "✏️ Данные", "🖼️ Предпросмотр", "⚠️ Артефакты DXF"])

    with tab_editor:
        st.subheader("Редактирование данных")
        st.write("Вы можете изменить количество деталей или названия материалов прямо в таблице. Итоговые суммы пересчитаются автоматически.")

        df = pd.DataFrame(st.session_state['data'])

        # We only want users to edit specific columns
        edited_df = st.data_editor(
            df,
            column_config={
                "File": st.column_config.TextColumn("Файл", disabled=True),
                "Length": st.column_config.NumberColumn("Длина реза (мм)", disabled=True, format="%.2f"),
                "Area": st.column_config.NumberColumn("Площадь (м²)", disabled=True, format="%.4f"),
                "Warnings": st.column_config.TextColumn("Статус", disabled=True),
                "Quantity": st.column_config.NumberColumn("Количество", min_value=1, step=1)
            },
            hide_index=True,
            use_container_width=True,
            key="data_editor"
        )

        # Sync back edited data to session state
        st.session_state['data'] = edited_df.to_dict('records')

    # Calculate Costs dynamically based on the (potentially edited) session state
    preview_data = []
    grand_total = 0.0
    total_area_all = 0.0
    total_length_all = 0.0

    for item in st.session_state['data']:
        cutting_cost = (item['Length'] / 1000) * cost_per_meter * item['Quantity']
        material_cost = item['Area'] * cost_per_square_meter * item['Quantity']
        total = cutting_cost + material_cost

        grand_total += total
        total_area_all += item['Area'] * item['Quantity']
        total_length_all += item['Length'] * item['Quantity']

        preview_item = item.copy()
        preview_item['Cutting Cost'] = round(cutting_cost, 2)
        preview_item['Material Cost'] = round(material_cost, 2)
        preview_item['Total'] = round(total, 2)
        preview_data.append(preview_item)

    # If the user updated the cost multipliers or table data, regenerate reports
    if recalculate_btn:
        pdf_path = st.session_state.get('pdf_path')
        excel_path = st.session_state.get('excel_path')
        if st.session_state.get('images'):
            create_pdf_report(st.session_state['images'], st.session_state['data'], pdf_path, cost_per_meter, cost_per_square_meter)
        create_excel_report(st.session_state['data'], excel_path, cost_per_meter, cost_per_square_meter)
        st.success("Отчеты успешно обновлены!")

    with tab_dashboard:
        st.subheader("Сводка по проекту")

        col1, col2, col3 = st.columns(3)
        col1.metric("Общая стоимость", f"{grand_total:,.2f} ₽")
        col2.metric("Общая площадь материала", f"{total_area_all:,.2f} м²")
        col3.metric("Общая длина реза", f"{total_length_all / 1000:,.2f} м")

        st.markdown("---")

        if preview_data:
            chart_df = pd.DataFrame(preview_data)
            chart_df = chart_df[['File', 'Cutting Cost', 'Material Cost']]
            chart_df = chart_df.set_index('File')

            st.write("**Структура стоимости по деталям**")
            st.bar_chart(chart_df)

        st.markdown("### Скачать отчеты")
        col_dl1, col_dl2 = st.columns(2)

        pdf_path = st.session_state.get('pdf_path', '')
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                col_dl1.download_button(
                    label="📥 Скачать PDF Отчет",
                    data=f,
                    file_name="dxf_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        excel_path = st.session_state.get('excel_path', '')
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                col_dl2.download_button(
                    label="📥 Скачать Excel Отчет",
                    data=f,
                    file_name="dxf_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    with tab_images:
        st.subheader("Предпросмотр контуров")
        images = st.session_state.get('images', [])
        cols = st.columns(min(3, max(1, len(images)))) if images else []
        for i, img_info in enumerate(images):
            with cols[i % len(cols)]:
                st.image(img_info['image_path'], caption=img_info['filename'])

    with tab_artifacts:
        st.subheader("Анализ качества DXF (Артефакты)")
        st.write("Проверка на микро-сегменты и незамкнутые контуры.")

        artifact_found = False
        for item in st.session_state['data']:
            if item.get('Warnings', 'OK') != 'OK':
                artifact_found = True
                st.error(f"**{item['File']}**:\n{item['Warnings']}")

        if not artifact_found:
            st.success("Все загруженные DXF файлы не содержат критических артефактов (микро-сегментов и разрывов контура).")

    st.markdown("---")
    if st.button("Очистить результаты", type="primary"):
        # Explicitly clean up temp dir on clear
        temp_dir = st.session_state.get('temp_dir')
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

        for key in ['reports_generated', 'data', 'images', 'temp_dir', 'pdf_path', 'excel_path']:
            st.session_state.pop(key, None)
        st.rerun()
