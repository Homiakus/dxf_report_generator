
# README

## DXF Report Generator

DXF Report Generator is a Python application that processes DXF files in a selected directory, calculates the total length of lines, calculates the area of the parts, and generates a PDF report with images and a detailed cost table. The application includes a graphical user interface (GUI) with a dark theme, where users can input cost parameters and generate reports effortlessly.

## Features

- **Batch Processing**: Process multiple DXF files in a selected directory.
- **Length and Area Calculation**: Calculate the total length of lines and the area of each part.
- **Cost Estimation**: Calculate cutting and material costs based on user-defined parameters.
- **PDF Report Generation**: Generate a PDF report with images of the parts and a detailed cost table.
- **Graphical User Interface**: User-friendly GUI with a dark theme.
- **Customizable**: Adaptable to different pricing models and units.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [File Naming Convention](#file-naming-convention)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/dxf-report-generator.git
   cd dxf-report-generator
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Required Packages**

   ```bash
   pip install -r requirements.txt
   ```

   *If `requirements.txt` is not provided, install the dependencies manually:*

   ```bash
   pip install ezdxf matplotlib reportlab
   ```

4. **Ensure Availability of the Arial Font**

   - For Windows users, Arial is typically available at `C:\Windows\Fonts\arial.ttf`.
   - For other operating systems, ensure that the Arial font is available and adjust the path in the code if necessary.

## Usage

1. **Run the Application**

   ```bash
   python dxf_report_generator.py
   ```

2. **Using the GUI**

   - **Select Directory**: Click on the "Выбрать папку" button to select the directory containing your DXF files.
   - **Enter Costs**:
     - **Стоимость реза за метр**: Enter the cutting cost per meter.
     - **Стоимость материала за м²**: Enter the material cost per square meter.
   - **Generate Report**: Click on the "Сформировать отчет" button to start processing.
   - **Progress Monitoring**: The progress label will display the current status of the processing.
   - **Open Report**: Once processing is complete, the "Открыть отчет" button becomes active. Click it to open the generated PDF report.

3. **Report Output**

   - The PDF report (`dxf_files.pdf`) is saved in the selected directory.
   - The report includes images of each DXF file and a table with detailed calculations.

## File Naming Convention

For accurate quantity extraction, DXF files should be named using the following convention:

```
name_quantity.dxf
```

- **Example**: `partA_5.dxf` indicates that there are 5 units of `partA`.

If the quantity is not specified, the program assumes a default quantity of 1.

## Dependencies

- **Python 3.x**
- **ezdxf**: For reading and processing DXF files.
- **matplotlib**: For rendering DXF files into images.
- **ReportLab**: For generating the PDF report.
- **tkinter**: For the GUI (usually included with Python).



## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**

   Click on the "Fork" button at the top right corner of this page.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/yourusername/dxf-report-generator.git
   ```

3. **Create a New Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Your Changes**

5. **Commit Your Changes**

   ```bash
   git commit -am 'Add some feature'
   ```

6. **Push to the Branch**

   ```bash
   git push origin feature/your-feature-name
   ```

7. **Submit a Pull Request**

   Go to the original repository and click on "Pull Request".

## License

This project is licensed under the MIT License 

---




**Note**: Ensure that you adjust the path to the Arial font in the `create_pdf` function if it's located in a different directory on your system.

## How to Run the Script

1. **Place the Script**

   Save the script as `dxf_report_generator.py` in your project directory.

2. **Ensure Dependencies are Installed**

   ```bash
   pip install ezdxf matplotlib reportlab
   ```

3. **Run the Script**

   ```bash
   python dxf_report_generator.py
   ```

---

If you have any questions or need further assistance, feel free to open an issue or submit a pull request.
