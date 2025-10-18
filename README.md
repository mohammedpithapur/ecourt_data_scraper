# eCourts Cause List Extractor

A Python automation tool that extracts judicial case information from India's eCourts system. This tool helps lawyers, legal professionals, and litigants retrieve cause lists, case details, and generate professional reports.

## What This Tool Does

**eCourts Cause List Extractor** automates the process of accessing India's eCourts portal and extracting case information. It provides three main functionalities:

1. **Single Court Search** - Extract and download case details for a specific court
2. **All Courts Search** - Retrieve cases from all courts in a selected court complex
3. **CNR Search** - Look up specific case information using Case Number Reference (CNR)

The tool automatically:
- Navigates the eCourts portal
- Solves CAPTCHA challenges using OCR technology
- Extracts case data from tables
- Generates professional PDF reports
- Exports data to CSV files for analysis

## Features

- ✅ **Automated CAPTCHA Solving** - Uses EasyOCR to bypass security verification
- ✅ **PDF Report Generation** - Creates formatted, professional cause list documents
- ✅ **CSV Export** - Save case data for Excel/spreadsheet analysis
- ✅ **Bulk Processing** - Extract data from multiple courts at once
- ✅ **Smart Retry Logic** - Automatically retries failed CAPTCHA attempts
- ✅ **Screenshot Logging** - Saves screenshots for debugging and verification
- ✅ **User-Friendly Interface** - Clear command-line prompts and feedback

## System Requirements

- **Python**: 3.7 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: Minimum 2GB (4GB recommended)
- **Internet Connection**: Required for accessing eCourts portal
- **Tesseract OCR**: Required for CAPTCHA processing

## Installation

### Step 1: Install Python Dependencies

First, install all required Python packages using pip:

```bash
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR (Required for CAPTCHA)

Tesseract is an OCR engine needed for CAPTCHA solving. Install it based on your operating system:

#### **Windows:**
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (recommended: keep default installation path `C:\Program Files\Tesseract-OCR`)
3. Add Tesseract to your Python script or system PATH

#### **macOS:**
```bash
brew install tesseract
```

#### **Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

#### **Linux (Fedora/CentOS):**
```bash
sudo yum install tesseract
```

### Step 3: Verify Installation

Test if everything is set up correctly:

```bash
python -c "import pytesseract; import easyocr; print('All dependencies installed successfully!')"
```



## Usage

### Quick Start

1. Navigate to the project directory:
```bash
cd path/to/ecort_project
```

2. Run the script:
```bash
python ecort.py
```

3. You'll see the main menu:
```
eCOURTS CAUSE LIST EXTRACTOR
================================================================================
Task 1 = Enter specific court name
Task 2 = Print all case details in that court complex
Task 3 = Enter CNR number to get case details

Enter task number (1, 2, or 3):
```

### Task 1: Single Court Search

Extract cases from a specific court:

1. Enter `1` when prompted
2. Select your state from the dropdown
3. Select the district
4. Select the court complex
5. (Optional) Select court establishment
6. Choose the specific court
7. Solve the CAPTCHA (auto-solved, shows result)
8. View results and optionally save as PDF/CSV

**Output**: 
- PDF report with formatted case data
- CSV file with raw case information
- Screenshots for verification

### Task 2: All Courts in Complex

Extract cases from all courts in a court complex:

1. Enter `2` when prompted
2. Follow the same selection process as Task 1
3. The tool processes all courts sequentially
4. Combines all results into a single report

**Output**:
- Combined PDF report with all cases
- Single CSV file with all data
- Progress updates during processing

### Task 3: CNR Search

Look up a specific case using CNR number:

1. Enter `3` when prompted
2. Enter the 16-digit CNR number
3. Tool displays hearing date status (Today/Tomorrow/Date)
4. Shows case details from the database

**Output**:
- Case status information
- Hearing date details
- Case metadata

## File Structure

```
ecort/
├── ecort.py                 # Main script
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── cause_list_report_*.pdf # Generated PDF reports
├── cause_list_*.csv        # Exported case data
└── screenshots/
    ├── captcha.png         # Captured CAPTCHA images
    ├── captcha_processed.png # Processed CAPTCHA
    └── results_table_loaded.png
```

## Generated Output Files

### PDF Reports
- **Filename**: `cause_list_report_[timestamp].pdf` or `all_courts_report_[timestamp].pdf`
- **Format**: Landscape A4 with professional styling
- **Contents**: Court info, case details, metadata, and record count

### CSV Files
- **Filename**: `cause_list_[timestamp].csv`
- **Format**: Standard CSV (comma-separated values)
- **Usage**: Import into Excel, Google Sheets, or database tools

## Troubleshooting

### Common Issues

**CAPTCHA Not Solving**
- Ensure Tesseract is installed and in your PATH
- Check internet connection quality
- Try running Task 1 or 2 again (automatic retry up to 5 times)

**ChromeDriver Issues**
- `webdriver-manager` auto-downloads the correct driver
- If issues persist, reinstall: `pip install --upgrade webdriver-manager`

**Tesseract Not Found (Windows)**
- Add Tesseract path to code before importing:
```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Connection Timeout**
- Check your internet connection
- The eCourts portal may be temporarily unavailable
- Try again after a few minutes

**No Results Found**
- Verify the court name is correct
- The court may have no active cases
- Check if court complex selection was valid

## Advanced Configuration

### Modify CAPTCHA Retry Attempts

Edit in `ecort.py` around line 183:
```python
max_retries = 5  # Change this number
```

### Change Output Page Size

Modify the PDF generation function (around line 413):
```python
pagesize=landscape(A4)  # Change to letter, A3, etc.
```

### Adjust Wait Times

Modify timeout values in `process_single_court()` and `process_all_courts()`:
```python
time.sleep(2)  # Change these values (in seconds)
```

## Legal Disclaimer

- This tool is for **educational and legitimate legal purposes only**
- Always comply with eCourts Terms of Service
- Do not use for automated mass downloading without permission
- Verify all extracted information with official court records
- The creators are not responsible for misuse of this tool

## Performance Tips

- Run during off-peak hours for faster processing
- Close unnecessary browser windows/tabs
- Ensure stable internet connection
- Use Task 2 for bulk data extraction (more efficient than multiple Task 1 runs)
- CSV export is faster than PDF; use CSV for large datasets

## Contributing & Support

For bugs, issues, or improvements:
1. Test the script in isolation first
2. Save error screenshots (auto-saved to project directory)
3. Note the exact task and steps that failed
4. Check the troubleshooting section above

## License

This project is provided as-is for educational purposes. Use responsibly and in compliance with applicable laws.

## Changelog

**v1.0** (Current)
- Initial release
- Support for Tasks 1, 2, and 3
- PDF and CSV export
- CAPTCHA auto-solving
- Multi-court batch processing

---

**Last Updated**: October 2024
**Python Version**: 3.7+
**Status**: Active & Maintained
