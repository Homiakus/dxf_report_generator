# DXF Cost Estimator & Report Generator (Web Version)

This is a comprehensive tool for processing DXF files, extracting data (total cut length and area), calculating costs based on user inputs, and generating rich PDF and Excel reports. It features a modern, responsive web interface built with **Streamlit**.

## Key Features

- **Modern Web Interface:** Built with Streamlit for a smooth, intuitive drag-and-drop experience.
- **Advanced DXF Parsing:** Calculates both line/cut length and overall part area.
- **Rich Filename Metadata:** Automatically parses file names (e.g., `bracket_steel_3mm_5.dxf`) to extract the part name, material, thickness, and quantity.
- **Dynamic Cost Calculation:** Interactive sidebar for adjusting cutting and material costs and instantly previewing the grand total.
- **Comprehensive Reporting:** Export your results seamlessly to **PDF** (including generated part images) and **Excel** (.xlsx).

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/dxf-report-generator.git
   cd dxf-report-generator
   ```

2. **Create and Activate a Virtual Environment (Optional but Recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the Web Application**
   ```bash
   cd dxf_app
   streamlit run app.py
   ```
2. **Access the App:** Open the URL provided in your terminal (typically `http://localhost:8501`).
3. **Upload Files:** Drag and drop your `.dxf` files into the upload area.
4. **Configure Settings:** Set the cutting cost per meter and material cost per square meter via the sidebar.
5. **Process & Generate:** Click the "Process Files & Generate Reports" button.
6. **Download:** Review the calculation preview on the screen and download the generated PDF or Excel report.

## File Naming Convention

To fully utilize the automatic metadata extraction, name your files using the following pattern:
`name_material_thickness_quantity.dxf`

**Example:**
`bracket_steel_3mm_5.dxf` -> Name: `bracket`, Material: `steel`, Thickness: `3mm`, Quantity: `5`

If the file doesn't follow this strict convention, the tool will gracefully fallback to standard formats (like `name_quantity.dxf` or simply `name.dxf`).

## Technologies Used
- **Streamlit**: Web interface
- **ezdxf**: Reading and parsing DXF files
- **matplotlib**: Rendering DXF vector data into images
- **reportlab**: PDF report generation
- **pandas** & **openpyxl**: Excel report generation

## License
MIT License
