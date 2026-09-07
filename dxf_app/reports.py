import os
import pandas as pd
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

def create_pdf_report(images, data, pdf_path, cost_per_meter, cost_per_square_meter):
    """
    Creates a PDF report using standard fonts.
    """
    # Register Roboto-Regular to support Cyrillic characters
    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Roboto-Regular.ttf')
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Roboto', font_path))
            font_name = 'Roboto'
        except Exception as e:
            print(f"Failed to load font: {e}")
            font_name = 'Helvetica'
    else:
        # Fallback if somehow font isn't found
        font_name = 'Helvetica'

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.alignment = 1
    styleN.fontName = font_name
    styleH = styles['Heading1']
    styleH.fontName = font_name

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []

    # Title
    elements.append(Paragraph('DXF Report', styleH))
    elements.append(Spacer(1, 0.5 * cm))

    # Fixed image dimensions
    fixed_width = 6 * cm
    fixed_height = 6 * cm

    for image_info in images:
        image_path = image_info['image_path']
        if not os.path.exists(image_path):
            continue

        img_flowable = RLImage(image_path, width=fixed_width, height=fixed_height)
        elements.append(img_flowable)
        elements.append(Spacer(1, 0.2 * cm))

        filename = image_info['filename']
        total_length = image_info['total_length']
        quantity = image_info['quantity']
        area = image_info['area']

        caption_text = (
            f"{filename} - Length: {total_length:.2f} mm, "
            f"Area: {area:.4f} m^2, Quantity: {quantity}"
        )
        caption = Paragraph(caption_text, styleN)
        elements.append(caption)
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.grey))
        elements.append(Spacer(1, 0.5 * cm))

    # Add the final table
    elements.append(Paragraph('Cost Calculation Table', styleH))
    elements.append(Spacer(1, 0.5 * cm))

    table_data = [
        ['File', 'Quantity', 'Length (mm)', 'Area (m^2)',
         'Cutting Cost', 'Material Cost', 'Total']
    ]

    grand_total = 0.0
    for item in data:
        filename = item['File']
        quantity = item['Quantity']
        total_length = item['Length']
        area = item['Area']

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

    table_data.append(['', '', '', '', '', 'Grand Total', f"{grand_total:.2f}"])

    table = Table(table_data, colWidths=[4 * cm, 2 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

def create_excel_report(data, excel_path, cost_per_meter, cost_per_square_meter):
    """
    Creates an Excel report from the provided data.
    """
    rows = []
    grand_total = 0.0
    for item in data:
        filename = item['File']
        quantity = item['Quantity']
        total_length = item['Length']
        area = item['Area']

        cutting_cost = (total_length / 1000) * cost_per_meter * quantity
        material_cost = area * cost_per_square_meter * quantity
        total = cutting_cost + material_cost
        grand_total += total

        rows.append({
            'File': filename,
            'Quantity': quantity,
            'Length (mm)': total_length,
            'Area (m^2)': area,
            'Cutting Cost': cutting_cost,
            'Material Cost': material_cost,
            'Total': total
        })

    df = pd.DataFrame(rows)
    # Add grand total row
    total_row = pd.DataFrame([{
        'File': 'Grand Total',
        'Quantity': '',
        'Length (mm)': '',
        'Area (m^2)': '',
        'Cutting Cost': '',
        'Material Cost': '',
        'Total': grand_total
    }])
    df = pd.concat([df, total_row], ignore_index=True)

    df.to_excel(excel_path, index=False)
