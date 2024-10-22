import os
import threading
import math
import ezdxf
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import matplotlib as ezdxf_matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser


def calculate_total_length(doc):
    """
    Calculate the total length of lines in a DXF document.
    Supports LINE, LWPOLYLINE, POLYLINE, CIRCLE, ARC, SPLINE.
    """
    total_length = 0.0
    msp = doc.modelspace()
    for entity in msp:
        try:
            length = 0.0
            if entity.dxftype() == 'LINE':
                length = calculate_line_length(entity)
            elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                length = calculate_polyline_length(entity)
            elif entity.dxftype() == 'CIRCLE':
                length = calculate_circle_length(entity)
            elif entity.dxftype() == 'ARC':
                length = calculate_arc_length(entity)
            elif entity.dxftype() == 'SPLINE':
                length = calculate_spline_length(entity)
            total_length += length
        except Exception as e:
            print(f"Error processing {entity.dxftype()}: {e}")
            continue
    return total_length


def calculate_line_length(entity):
    start = entity.dxf.start
    end = entity.dxf.end
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    return length


def calculate_polyline_length(entity):
    length = 0.0
    points = list(entity.get_points())
    for i in range(len(points) - 1):
        start = points[i]
        end = points[i + 1]
        length += math.hypot(end[0] - start[0], end[1] - start[1])
    if entity.closed:
        start = points[-1]
        end = points[0]
        length += math.hypot(end[0] - start[0], end[1] - start[1])
    return length


def calculate_circle_length(entity):
    radius = entity.dxf.radius
    return 2 * math.pi * radius


def calculate_arc_length(entity):
    radius = entity.dxf.radius
    start_angle = math.radians(entity.dxf.start_angle)
    end_angle = math.radians(entity.dxf.end_angle)
    angle = end_angle - start_angle
    if angle < 0:
        angle += 2 * math.pi
    return radius * angle


def calculate_spline_length(entity):
    length = 0.0
    spline_points = entity.approximate(segments=100)
    for i in range(len(spline_points) - 1):
        start = spline_points[i]
        end = spline_points[i + 1]
        length += math.hypot(end[0] - start[0], end[1] - start[1])
    return length


def calculate_bounding_box_area(doc):
    """
    Calculate the area of the minimal bounding rectangle for all entities in the DXF document.
    """
    msp = doc.modelspace()
    min_x, min_y, max_x, max_y = None, None, None, None
    for entity in msp:
        try:
            vertices = get_entity_vertices(entity)
            for x, y in vertices:
                min_x = x if min_x is None else min(min_x, x)
                min_y = y if min_y is None else min(min_y, y)
                max_x = x if max_x is None else max(max_x, x)
                max_y = y if max_y is None else max(max_y, y)
        except Exception as e:
            print(f"Error processing {entity.dxftype()}: {e}")
            continue
    if None not in (min_x, min_y, max_x, max_y):
        width = max_x - min_x
        height = max_y - min_y
        area = width * height / 1_000_000  # Convert from mm² to m²
        return area
    else:
        return 0.0


def get_entity_vertices(entity):
    vertices = []
    if entity.dxftype() == 'LINE':
        vertices.extend([entity.dxf.start[:2], entity.dxf.end[:2]])
    elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
        vertices.extend([point[:2] for point in entity.get_points()])
    elif entity.dxftype() == 'CIRCLE':
        center = entity.dxf.center
        radius = entity.dxf.radius
        vertices.extend([
            (center[0] - radius, center[1]),
            (center[0] + radius, center[1]),
            (center[0], center[1] - radius),
            (center[0], center[1] + radius),
        ])
    elif entity.dxftype() == 'ARC':
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)
        vertices.extend([
            (
                center[0] + radius * math.cos(start_angle),
                center[1] + radius * math.sin(start_angle)
            ),
            (
                center[0] + radius * math.cos(end_angle),
                center[1] + radius * math.sin(end_angle)
            )
        ])
    elif entity.dxftype() == 'SPLINE':
        spline_points = entity.approximate(segments=100)
        vertices.extend([(p[0], p[1]) for p in spline_points])
    return vertices


def render_dxf_to_image(doc, image_path):
    """
    Render the DXF document to an image and save it to the specified path.
    Uses ezdxf_matplotlib.qsave for reliable rendering.
    Returns True if successful, False otherwise.
    """
    try:
        fig_width, fig_height = 6, 6  # Inches
        dpi = 300  # Resolution

        # Render the DXF document
        ezdxf_matplotlib.qsave(
            doc.modelspace(),
            image_path,
            size_inches=(fig_width, fig_height),
            dpi=dpi,
            bg='#FFFFFF',
            fg='#000000',
        )
        return True
    except Exception as e:
        print(f"Error rendering DXF to image: {e}")
        return False


def create_pdf(images, data, pdf_path, cost_per_meter, cost_per_square_meter):
    """
    Create a PDF document containing images of DXF files and a data table.
    """
    # Register Arial font
    pdfmetrics.registerFont(TTFont('Arial', r'C:\Windows\Fonts\arial.ttf'))

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'Arial'
    styleN.alignment = 1
    styleH = styles['Heading1']
    styleH.fontName = 'Arial'

    # Create the PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []

    # Fixed image dimensions
    fixed_width = 6 * cm
    fixed_height = 6 * cm

    for image_info in images:
        image_path = image_info['image_path']
        if not os.path.exists(image_path):
            print(f"Image {image_path} not found, skipping.")
            continue
        img_flowable = RLImage(image_path, width=fixed_width, height=fixed_height)
        elements.append(img_flowable)
        elements.append(Spacer(1, 0.2 * cm))
        filename = image_info['filename']
        total_length = image_info['total_length']
        quantity = image_info['quantity']
        area = image_info['area']
        caption_text = (
            f"{filename} - Длина линий: {total_length:.2f} мм, "
            f"Площадь: {area:.4f} м², Количество: {quantity}"
        )
        caption = Paragraph(caption_text, styleN)
        elements.append(caption)
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.grey))
        elements.append(Spacer(1, 0.5 * cm))

    # Add the final table
    elements.append(Paragraph('Таблица расчета стоимости', styleH))
    elements.append(Spacer(1, 0.5 * cm))
    table_data = [
        ['Файл', 'Количество', 'Длина линий (мм)', 'Площадь (м²)',
         'Стоимость реза', 'Стоимость материала', 'Итого']
    ]
    grand_total = 0.0
    for item in data:
        filename = item['Файл']
        quantity = item['Количество']
        total_length = item['Общая длина линий']
        area = item['Площадь']
        cutting_cost = (total_length / 1000) * cost_per_meter * quantity
        material_cost = area * cost_per_square_meter * quantity
        total = cutting_cost + material_cost
        grand_total += total
        table_data.append([
            filename,
            str(quantity),
            f"{total_length:.2f}",
            f"{area:.4f}",
            f"{cutting_cost:.2f}",
            f"{material_cost:.2f}",
            f"{total:.2f}"
        ])
    table_data.append(['', '', '', '', '', 'Общая стоимость', f"{grand_total:.2f}"])

    table = Table(table_data, colWidths=[4 * cm, 2 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)


def extract_quantity_from_filename(filename):
    """
    Extracts the quantity from the filename.
    Expected format: 'name_quantity.dxf'.
    Returns 1 if quantity is not found.
    """
    base_name = os.path.splitext(filename)[0]
    parts = base_name.rsplit('_', 1)
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    else:
        return 1


def process_files(directory, progress_label, cost_per_meter, cost_per_square_meter, open_report_button):
    """
    Processes DXF files in the specified directory and generates a PDF report.
    """
    data = []
    images = []
    temp_image_folder = os.path.join(directory, 'temp_images')
    os.makedirs(temp_image_folder, exist_ok=True)

    dxf_files = [f for f in os.listdir(directory) if f.lower().endswith('.dxf')]

    total_files = len(dxf_files)
    processed_files = 0

    for filename in dxf_files:
        dxf_path = os.path.join(directory, filename)
        progress_label.config(text=f"Обработка файла {filename}...")
        progress_label.update()
        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            if len(msp) == 0:
                print(f"No objects in {filename}, skipping.")
                continue
            total_length = calculate_total_length(doc)
            area = calculate_bounding_box_area(doc)
            quantity = extract_quantity_from_filename(filename)
            data.append({
                'Файл': filename,
                'Количество': quantity,
                'Общая длина линий': total_length,
                'Площадь': area
            })
            print(f"Total line length in {filename}: {total_length:.2f} mm")
            print(f"Area of {filename}: {area:.4f} m²")
            image_filename = os.path.splitext(filename)[0] + '.jpg'
            image_path = os.path.join(temp_image_folder, image_filename)
            success = render_dxf_to_image(doc, image_path)
            if success and os.path.exists(image_path):
                images.append({
                    'filename': filename,
                    'image_path': image_path,
                    'total_length': total_length,
                    'quantity': quantity,
                    'area': area
                })
                print(f"Image for {filename} created successfully.")
            else:
                print(f"Failed to create image for {filename}.")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
        processed_files += 1
        progress_label.config(text=f"Processed {processed_files} of {total_files} files.")
        progress_label.update()

    if images:
        pdf_path = os.path.join(directory, 'dxf_files.pdf')
        progress_label.config(text="Creating PDF report...")
        progress_label.update()
        create_pdf(images, data, pdf_path, cost_per_meter, cost_per_square_meter)
        progress_label.config(text=f"PDF report saved at: {pdf_path}")
        progress_label.update()
        print(f"PDF report saved at: {pdf_path}")
        open_report_button.config(state='normal')
        open_report_button.pdf_path = pdf_path
    else:
        progress_label.config(text="Failed to create PDF report; no images available.")
        progress_label.update()
        print("Failed to create PDF report; no images available.")

    # Clean up temporary images
    for image_info in images:
        try:
            os.remove(image_info['image_path'])
        except Exception as e:
            print(f"Error deleting temporary file {image_info['image_path']}: {e}")
    try:
        os.rmdir(temp_image_folder)
    except OSError:
        pass


def start_processing(directory, progress_label, generate_button,
                     cost_per_meter_entry, cost_per_square_meter_entry, open_report_button):
    """
    Starts processing files in a separate thread.
    """
    try:
        cost_per_meter = float(cost_per_meter_entry.get())
        cost_per_square_meter = float(cost_per_square_meter_entry.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Пожалуйста, введите корректные значения для стоимости.")
        return

    generate_button.config(state='disabled')
    threading.Thread(
        target=process_files,
        args=(directory, progress_label, cost_per_meter, cost_per_square_meter, open_report_button),
        daemon=True
    ).start()


def main():
    """
    Main function to run the GUI application.
    """
    root = tk.Tk()
    root.title("DXF Report Generator")
    root.geometry("800x600")
    root.configure(bg='#2e2e2e')

    selected_directory = tk.StringVar()

    def select_directory():
        directory = filedialog.askdirectory()
        if directory:
            selected_directory.set(directory)
            directory_label.config(text=f"Selected Directory: {directory}")
            generate_button.config(state='normal')
        else:
            directory_label.config(text="No directory selected.")
            generate_button.config(state='disabled')

    def generate_report():
        if selected_directory.get():
            progress_label.config(text="Starting file processing...")
            start_processing(
                selected_directory.get(),
                progress_label,
                generate_button,
                cost_per_meter_entry,
                cost_per_square_meter_entry,
                open_report_button
            )
        else:
            messagebox.showwarning("Warning", "Please select a directory first.")

    def open_report():
        pdf_path = open_report_button.pdf_path
        if os.path.exists(pdf_path):
            webbrowser.open_new(r'file://%s' % pdf_path)
        else:
            messagebox.showerror("Error", "Report file not found.")

    # Styles for the dark theme
    style_bg = '#2e2e2e'
    style_fg = '#ffffff'
    button_bg = '#5e5e5e'
    entry_bg = '#4e4e4e'

    root.configure(bg=style_bg)

    select_button = tk.Button(root, text="Выбрать папку", command=select_directory,
                              bg=button_bg, fg=style_fg)
    select_button.pack(pady=10)

    directory_label = tk.Label(root, text="No directory selected.", bg=style_bg, fg=style_fg)
    directory_label.pack(pady=5)

    # Cost input fields
    cost_frame = tk.Frame(root, bg=style_bg)
    cost_frame.pack(pady=10)

    cost_per_meter_label = tk.Label(cost_frame, text="Стоимость реза за метр:",
                                    bg=style_bg, fg=style_fg)
    cost_per_meter_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')
    cost_per_meter_entry = tk.Entry(cost_frame, bg=entry_bg, fg=style_fg)
    cost_per_meter_entry.grid(row=0, column=1, padx=5, pady=5)

    cost_per_square_meter_label = tk.Label(cost_frame, text="Стоимость материала за м²:",
                                           bg=style_bg, fg=style_fg)
    cost_per_square_meter_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
    cost_per_square_meter_entry = tk.Entry(cost_frame, bg=entry_bg, fg=style_fg)
    cost_per_square_meter_entry.grid(row=1, column=1, padx=5, pady=5)

    progress_label = tk.Label(root, text="", bg=style_bg, fg=style_fg)
    progress_label.pack(pady=10)

    generate_button = tk.Button(root, text="Сформировать отчет", command=generate_report,
                                state='disabled', bg=button_bg, fg=style_fg)
    generate_button.pack(pady=10)

    open_report_button = tk.Button(root, text="Открыть отчет", command=open_report,
                                   state='disabled', bg=button_bg, fg=style_fg)
    open_report_button.pack(pady=10)

    # Adaptive window size
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root.mainloop()


if __name__ == "__main__":
    main()
