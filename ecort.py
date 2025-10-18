from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import easyocr
import pandas as pd

# ============================================================================
# SETUP
# ============================================================================

options = Options()
options.add_experimental_option("detach", True)
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), 
    options=options
)

driver.get(
    "https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/index&app_token=4a71ef6f1714e0abe10fb078271c1cbc080d09e894e34ac793d7a2674224ac61"
)

wait = WebDriverWait(driver, 15)

# ============================================================================
# STEP 1: SELECT STATE
# ============================================================================

def state_select():
    print("\n" + "="*80)
    print("STEP 1: SELECT STATE")
    print("="*80)

    state_dropdown = wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
    states = [option.text for option in state_dropdown.find_elements(By.TAG_NAME, "option")]

    print("\nAvailable states:")
    for i, state in enumerate(states, 1):
        print(f"  {i}. {state}")

    statename = input("\nEnter the state name from above: ").strip()
    Select(state_dropdown).select_by_visible_text(statename)
    print(f"✓ Selected: {statename}")
    time.sleep(1)

# ============================================================================
# STEP 2: SELECT DISTRICT
# ============================================================================

def district_select():
    print("\n" + "="*80)
    print("STEP 2: SELECT DISTRICT")
    print("="*80)

    dist = wait.until(EC.presence_of_element_located((By.NAME, "sees_dist_code")))
    districts = [option.text for option in dist.find_elements(By.TAG_NAME, "option")]

    print("\nAvailable districts:")
    for i, district in enumerate(districts, 1):
        print(f"  {i}. {district}")

    cityname = input("\nEnter the district name from above: ").strip()
    Select(dist).select_by_visible_text(cityname)
    print(f"✓ Selected: {cityname}")
    time.sleep(1)

# ============================================================================
# STEP 3: SELECT COURT COMPLEX
# ============================================================================

def cort_complex_select():
    print("\n" + "="*80)
    print("STEP 3: SELECT COURT COMPLEX")
    print("="*80)

    cort_complex = wait.until(EC.presence_of_element_located((By.ID, "court_complex_code")))
    complexes = [option.text for option in cort_complex.find_elements(By.TAG_NAME, "option")]

    print("\nAvailable court complexes:")
    for i, complex_name in enumerate(complexes, 1):
        print(f"  {i}. {complex_name}")

    cort_complex_name = input("\nEnter the court complex name from above: ").strip()
    Select(cort_complex).select_by_visible_text(cort_complex_name)
    print(f"✓ Selected: {cort_complex_name}")
    time.sleep(1)

# ============================================================================
# STEP 4: SELECT COURT ESTABLISHMENT (OPTIONAL)
# ============================================================================

def cort_establishment_select():
    print("\n" + "="*80)
    print("STEP 4: SELECT COURT ESTABLISHMENT (OPTIONAL)")
    print("="*80)

    try:
        cort_est = wait.until(EC.presence_of_element_located((By.ID, "court_est_code")))
        establishments = [option.text for option in cort_est.find_elements(By.TAG_NAME, "option")]
        
        if len(establishments) > 1:
            print("\nAvailable court establishments:")
            for i, est in enumerate(establishments, 1):
                print(f"  {i}. {est}")
            
            cort_est_name = input("\nEnter the court establishment name from above (or press Enter to skip): ").strip()
            
            if cort_est_name:
                Select(cort_est).select_by_visible_text(cort_est_name)
                print(f"✓ Selected: {cort_est_name}")
                time.sleep(1)
            else:
                print("⊘ Skipped")
        else:
            print("⊘ No court establishment options available, skipping...")
            
    except Exception as e:
        print(f"⊘ No court establishment found, skipping...")

# ============================================================================
# STEP 5: GET ALL COURTS
# ============================================================================

def get_all_courts():
    print("\n" + "="*80)
    print("STEP 5: GET AVAILABLE COURTS")
    print("="*80)

    print("\n⏳ Waiting for court dropdown to load...")
    time.sleep(2)

    cort = driver.find_element(By.ID, "CL_court_no")
    wait.until(lambda d: len(cort.find_elements(By.TAG_NAME, "option")) > 1)

    # Get only enabled options (skip disabled ones)
    all_options = cort.find_elements(By.TAG_NAME, "option")
    courts = []
    
    for option in all_options:
        is_disabled = option.get_attribute("disabled") is not None
        option_text = option.text.strip()
        
        # Skip disabled options and empty options
        if not is_disabled and option_text and option_text != "Select Court Name":
            courts.append(option_text)

    print(f"\n✓ Loaded {len(courts)} enabled court options")
    print("\nAvailable courts:")
    for i, court in enumerate(courts, 1):
        print(f"  {i}. {court}")

    return courts



# ============================================================================
# FUNCTION: SCAN AND SOLVE CAPTCHA
# ============================================================================

def scan_captcha():
    print("\n📸 Capturing captcha...")
    captcha_element = wait.until(
        EC.presence_of_element_located((By.XPATH, "//img[contains(@src,'captcha') or contains(@id,'captcha')]"))
    )

    captcha_element.screenshot('captcha.png')
    print("✓ Captcha image saved as 'captcha.png'")

    driver.save_screenshot('full_page_before_submit.png')
    print("✓ Full page screenshot saved")

    print("🔍 Processing captcha image...")
    img = Image.open('captcha.png').convert('L')
    img = img.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    img.save('captcha_processed.png')

    print("🤖 Solving captcha with EasyOCR...")
    reader = easyocr.Reader(['en'])
    result = reader.readtext('captcha_processed.png')

    captcha_text = ''.join([text[1] for text in result if text[2] > 0.3]).strip()
    captcha_text = ''.join(c for c in captcha_text if c.isalnum())

    print(f"✓ Captcha solved: '{captcha_text}'")
    return captcha_text

# ============================================================================
# FUNCTION: ENTER CAPTCHA AND SUBMIT
# ============================================================================

def enter_captcha_and_submit(captcha_text):
    print("\n📝 Entering captcha...")
    captcha_input = driver.find_element(By.ID, "cause_list_captcha_code")
    captcha_input.clear()
    captcha_input.send_keys(captcha_text)
    print(f"✓ Captcha entered: {captcha_text}")

    print("📤 Clicking submit button...")
    submit_btn = driver.find_element(By.XPATH, "//button[text()='Civil']")
    driver.execute_script("arguments[0].click();", submit_btn)
    print("✓ Submit button clicked")
    time.sleep(2)

# ============================================================================
# FUNCTION: VALIDATE CAPTCHA WITH RETRY
# ============================================================================

def validate_captcha(capchafunc):
    print("\n" + "="*80)
    print("VALIDATING CAPTCHA")
    print("="*80)

    check_captcha_retry = True
    retry_count = 0
    max_retries = 5

    while check_captcha_retry:
        time.sleep(2)
        
        try:
            modal_elements = driver.find_elements(By.CLASS_NAME, "modal-content")
            
            if modal_elements:
                print("\n⚠️  Modal detected on page...")
                
                try:
                    error_alerts = driver.find_elements(By.CLASS_NAME, "alert-danger-cust")
                    success_alerts = driver.find_elements(By.CLASS_NAME, "alert-success-cust")
                    
                    if error_alerts:
                        error_msg = error_alerts[0]
                        error_text = error_msg.text.strip()
                        error_display = error_msg.value_of_css_property("display")
                        
                        if error_display != "none" and error_text:
                            retry_count += 1
                            print(f"\n❌ Captcha was incorrect! (Attempt {retry_count}/{max_retries})")
                            print(f"Error: {error_text}")
                            
                            if retry_count >= max_retries:
                                print(f"\n❌ Maximum captcha attempts ({max_retries}) reached.")
                                driver.save_screenshot("max_retries_reached.png")
                                return False
                            
                            print("🔄 Retrying with new captcha...")
                            time.sleep(1)
                            
                            try:
                                close_btn = driver.find_element(By.XPATH, "//button[@class='btn-close']")
                                driver.execute_script("arguments[0].click();", close_btn)
                                print("✓ Modal closed")
                                time.sleep(2)
                            except:
                                try:
                                    driver.execute_script("document.querySelector('.modal-content').closest('.modal').style.display='none';")
                                    time.sleep(2)
                                except:
                                    driver.refresh()
                                    time.sleep(3)
                            
                            captcha_text = scan_captcha()
                            capchafunc(captcha_text)
                        
                        elif success_alerts and success_alerts[0].value_of_css_property("display") != "none":
                            success_text = success_alerts[0].text.strip()
                            print(f"✓ Success message received: {success_text}")
                            check_captcha_retry = False
                        else:
                            print("✓ No error or success message - proceeding...")
                            check_captcha_retry = False
                    else:
                        print("✓ No error alert found - proceeding...")
                        check_captcha_retry = False
                        
                except Exception as e:
                    print(f"Error reading modal content: {e}")
                    check_captcha_retry = False
            else:
                print("✓ No modal found - captcha accepted!")
                check_captcha_retry = False
                
        except Exception as e:
            print(f"Error checking for modal: {e}")
            check_captcha_retry = False

    return True


def enter_captcha_and_submit_CNR(captcha_text):
    print("\n📝 Entering captcha...")
    captcha_input = driver.find_element(By.ID, "fcaptcha_code")
    captcha_input.clear()
    captcha_input.send_keys(captcha_text)
    print(f"✓ Captcha entered: {captcha_text}")

    print("📤 Clicking submit button...")
    submit_btn = driver.find_element(By.XPATH, "//button[text()='Search']")
    driver.execute_script("arguments[0].click();", submit_btn)
    print("✓ Submit button clicked")
    time.sleep(2)
def get_CNR_number():
    print("\n" + "="*80)
    print("ENTER CNR NUMBER")
    print("="*80)

    cnr_input = driver.find_element(By.ID, "cino")
    cnr_number = input("\nEnter the CNR number (or press Enter to skip): ").strip()

    if cnr_number:
        cnr_input.clear()
        cnr_input.send_keys(cnr_number)
        print(f"✓ Entered CNR number: {cnr_number}")
        time.sleep(1)
        captcha_text=scan_captcha()
        enter_captcha_and_submit_CNR(captcha_text)
        
        validate_captcha(enter_captcha_and_submit_CNR)

    else:
        print("⊘ Skipped entering CNR number")

# ============================================================================
# FUNCTION: GET RESULTS TABLE
# ============================================================================

def get_results_table():
    print("\n" + "="*80)
    print("WAITING FOR RESULTS")
    print("="*80)

    try:
        print("\n⏳ Waiting for results table to load...")
        table = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "dispTable"))
        )
        print("✅ Results table loaded successfully!")
        
        driver.save_screenshot('results_table_loaded.png')
        print("✓ Results page screenshot saved")
        
        return table
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️  Results table not found - No record found")
        return None

# ============================================================================
# FUNCTION: EXTRACT AND DISPLAY TABLE DATA
# ============================================================================

def extract_and_display_table(court_name=None):
    print("\n" + "="*80)
    print("EXTRACTING TABLE DATA")
    print("="*80)

    try:
        table = driver.find_element(By.ID, "dispTable")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        headers = []
        table_data = []
        
        print(f"\n📊 Found {len(rows)} rows in table")
        
        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                cells = row.find_elements(By.TAG_NAME, "th")
            
            row_data = [cell.text.strip() for cell in cells]
            
            if i == 0:
                headers = row_data
                # Add "Court Name" as first column header if court_name is provided
                if court_name:
                    headers = ["Court Name"] + headers
                print(f"\n📋 Headers: {headers}")
            else:
                if any(row_data):
                    # Add court name as first column if provided
                    if court_name:
                        row_data = [court_name] + row_data
                    table_data.append(row_data)
        
        if table_data:
            print("\n" + "="*80)
            print("RESULTS - CAUSE LIST")
            print("="*80 + "\n")
            
            for i, row in enumerate(table_data, 1):
                print(f"Case {i}:")
                print("-" * 80)
                for j, header in enumerate(headers):
                    value = row[j] if j < len(row) else "N/A"
                    print(f"  {header:.<30} {value}")
                print()
            
            return table_data, headers
        else:
            print("⚠️  No case data found in table")
            return [], []
        
    except Exception as e:
        print(f"❌ Error extracting table data: {e}")
        driver.save_screenshot("extraction_error.png")
        return [], []

# ============================================================================
# FUNCTION: SAVE TO CSV
# ============================================================================

def save_to_csv(table_data, headers):
    if table_data and headers:
        save_csv = input("\nSave results to CSV? (y/n): ").strip().lower()
        
        if save_csv == 'y':
            df = pd.DataFrame(table_data, columns=headers)
            filename = f"cause_list_{int(time.time())}.csv"
            df.to_csv(filename, index=False)
            print(f"✓ Results saved to: {filename}")

# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def process_single_court():
    print("\n" + "="*80)
    print("TASK 1: ENTER SPECIFIC COURT NAME")
    print("="*80)
    
    state_select()
    district_select()
    cort_complex_select()
    cort_establishment_select()
    
    courts = get_all_courts()
    court_name = input("\nEnter the court name from above: ").strip()
    
    cort = driver.find_element(By.ID, "CL_court_no")
    Select(cort).select_by_visible_text(court_name)
    print(f"✓ Selected: {court_name}")
    time.sleep(2)
    
    captcha_text = scan_captcha()
    enter_captcha_and_submit(captcha_text)
    
    if validate_captcha(enter_captcha_and_submit):
        table = get_results_table()
        if table:
            table_data, headers = extract_and_display_table()
            save_to_csv(table_data, headers)

def process_all_courts():
    print("\n" + "="*80)
    print("TASK 2: PRINT ALL CASE DETAILS IN COURT COMPLEX")
    print("="*80)
    
    state_select()
    district_select()
    cort_complex_select()
    cort_establishment_select()
    
    courts = get_all_courts()
    courts = courts[1:] if len(courts) > 1 else courts  # Skip first option (usually "Select")
    
    all_data = []
    all_headers = None
    
    for idx, court_name in enumerate(courts, 1):
        if court_name.strip():
            print(f"\n\n{'='*80}")
            print(f"Processing court {idx}/{len(courts)}: {court_name}")
            print(f"{'='*80}")
            
            cort = driver.find_element(By.ID, "CL_court_no")
            Select(cort).select_by_visible_text(court_name)
            time.sleep(2)
            
            captcha_text = scan_captcha()
            enter_captcha_and_submit(captcha_text)
            
            if validate_captcha():
                table = get_results_table()
                if table:
                    # Pass court_name to add it as a column
                    table_data, headers = extract_and_display_table(court_name)
                    if table_data:
                        all_data.extend(table_data)
                        all_headers = headers
    
    if all_data and all_headers:
        print("\n\n" + "="*80)
        print("ALL COURTS - COMBINED RESULTS")
        print("="*80)
        print(f"\nTotal cases found: {len(all_data)}")
        print(f"Columns: {all_headers}")
        save_to_csv(all_data, all_headers)
    
    print("\nAll courts processed.")

# ============================================================================
# PDF GENERATION FUNCTIONS
# ============================================================================
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from datetime import datetime

def generate_pdf_report(table_data, headers, filename, court_complex_name, state_name, district_name):
    """
    Generate a professional PDF report with case data - FIXED VERSION
    """
    
    pdf_file = f"{filename}_{int(datetime.now().timestamp())}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=landscape(A4), topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.25*inch, rightMargin=0.25*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
        alignment=1
    )
    
    # Header info style
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4,
        alignment=1
    )
    
    # Cell text style - smaller font for wrapped text
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,
        wordWrap='CJK'
    )
    
    # Add title
    title = Paragraph("eCOURTS CAUSE LIST REPORT", title_style)
    elements.append(title)
    
    # Add header info
    header_info = f"""
    <b>Court Complex:</b> {court_complex_name}<br/>
    <b>District:</b> {district_name}<br/>
    <b>State:</b> {state_name}<br/>
    <b>Generated on:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
    """
    elements.append(Paragraph(header_info, header_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Prepare table data with wrapped text in Paragraph objects
    table_data_with_headers = [headers] + table_data
    
    # Process table data - convert to Paragraph objects for proper wrapping
    processed_data = []
    for row_idx, row in enumerate(table_data_with_headers):
        processed_row = []
        for cell_idx, cell in enumerate(row):
            # Convert to string and clean
            cell_text = str(cell).replace('\n', ' ').replace('\r', '').strip()
            
            # Create Paragraph object for wrapping
            if row_idx == 0:  # Header row
                para = Paragraph(f"<b>{cell_text}</b>", cell_style)
            else:
                para = Paragraph(cell_text, cell_style)
            
            processed_row.append(para)
        processed_data.append(processed_row)
    
    # Calculate dynamic column widths based on content
    page_width = landscape(A4)[0] - 0.5*inch
    num_cols = len(headers)
    
    # Distribute width with some columns getting more space if they typically have longer content
    base_width = page_width / num_cols
    col_widths = [base_width * 0.9] * num_cols  # Slightly reduce to ensure fit
    
    # Give more space to columns that typically have longer content
    if num_cols > 3:
        col_widths[3] = base_width * 1.2  # Party Name usually longer
        if num_cols > 4:
            col_widths[4] = base_width * 1.0  # Advocate
    
    # Create table with calculated column widths
    table = Table(processed_data, colWidths=col_widths, repeatRows=1)
    
    # Style the table with better row heights and padding
    table_style = TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Data rows styling
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),  # Top alignment for wrapped text
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        
        # Padding for better spacing and to prevent overlap
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        
        # Minimum row height for data rows
        ('ROWHEIGHTS', (0, 1), (-1, -1), 0.4*inch),
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Footer section
    elements.append(Spacer(1, 0.2*inch))
    
    footer_text = f"""
    <b>Total Records:</b> {len(table_data)}<br/>
    <b>Report Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}<br/>
    <i>This is an auto-generated report from eCourts Cause List Extractor. For official purposes, please verify with the court registry.</i>
    """
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666'),
        alignment=0
    )
    
    elements.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(elements)
    print(f"✓ PDF report generated: {pdf_file}")
    return pdf_file
# ============================================================================
# MAIN EXECUTION
# ============================================================================

print("\n" + "="*80)
print("eCOURTS CAUSE LIST EXTRACTOR")
print("="*80)
print("Task 1 = Enter specific court name")
print("Task 2 = Print all case details in that court complex")
print("Task 3 = Enter CNR number to get case details")

task = int(input("\nEnter task number (1 or 2): ").strip())

# Store court details for PDF generation
court_complex_name = ""
state_name = ""
district_name = ""

try:
    if task == 1:
        # Get state, district, and complex before processing
        print("\nCollecting location details...")
        
        state_dropdown = wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        states = [option.text for option in state_dropdown.find_elements(By.TAG_NAME, "option")]
        print("\nAvailable states:")
        for i, state in enumerate(states, 1):
            print(f"  {i}. {state}")
        state_name = input("\nEnter the state name from above: ").strip()
        Select(state_dropdown).select_by_visible_text(state_name)
        time.sleep(1)
        
        dist = wait.until(EC.presence_of_element_located((By.NAME, "sees_dist_code")))
        districts = [option.text for option in dist.find_elements(By.TAG_NAME, "option")]
        print("\nAvailable districts:")
        for i, district in enumerate(districts, 1):
            print(f"  {i}. {district}")
        district_name = input("\nEnter the district name from above: ").strip()
        Select(dist).select_by_visible_text(district_name)
        time.sleep(1)
        
        cort_complex = wait.until(EC.presence_of_element_located((By.ID, "court_complex_code")))
        complexes = [option.text for option in cort_complex.find_elements(By.TAG_NAME, "option")]
        print("\nAvailable court complexes:")
        for i, complex_name in enumerate(complexes, 1):
            print(f"  {i}. {complex_name}")
        court_complex_name = input("\nEnter the court complex name from above: ").strip()
        Select(cort_complex).select_by_visible_text(court_complex_name)
        time.sleep(1)
        
        cort_establishment_select()
        
        courts = get_all_courts()
        court_name = input("\nEnter the court name from above: ").strip()
        
        cort = driver.find_element(By.ID, "CL_court_no")
        Select(cort).select_by_visible_text(court_name)
        print(f"✓ Selected: {court_name}")
        time.sleep(2)
        
        captcha_text = scan_captcha()
        enter_captcha_and_submit(captcha_text)
        
        if validate_captcha():
            table = get_results_table()
            if table:
                table_data, headers = extract_and_display_table()
                save_to_csv(table_data, headers)
                
                # Generate PDF after getting results
                if table_data and headers:
                    print("\nGenerating PDF report...")
                    try:
                        pdf_file = generate_pdf_report(table_data, headers, "cause_list_report", court_complex_name, state_name, district_name)
                        print(f"✓ PDF saved as: {pdf_file}")
                    except Exception as pdf_err:
                        print(f"Error generating PDF: {pdf_err}")
                        import traceback
                        traceback.print_exc()
        
    elif task == 2:
        # Get state, district, and complex before processing
        print("\nCollecting location details...")
        
        state_dropdown = wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        states = [option.text for option in state_dropdown.find_elements(By.TAG_NAME, "option")]
        print("\nAvailable states:")
        for i, state in enumerate(states, 1):
            print(f"  {i}. {state}")
        state_name = input("\nEnter the state name from above: ").strip()
        Select(state_dropdown).select_by_visible_text(state_name)
        time.sleep(1)
        
        dist = wait.until(EC.presence_of_element_located((By.NAME, "sees_dist_code")))
        districts = [option.text for option in dist.find_elements(By.TAG_NAME, "option")]
        print("\nAvailable districts:")
        for i, district in enumerate(districts, 1):
            print(f"  {i}. {district}")
        district_name = input("\nEnter the district name from above: ").strip()
        Select(dist).select_by_visible_text(district_name)
        time.sleep(1)
        
        cort_complex = wait.until(EC.presence_of_element_located((By.ID, "court_complex_code")))
        complexes = [option.text for option in cort_complex.find_elements(By.TAG_NAME, "option")]
        print("\nAvailable court complexes:")
        for i, complex_name in enumerate(complexes, 1):
            print(f"  {i}. {complex_name}")
        court_complex_name = input("\nEnter the court complex name from above: ").strip()
        Select(cort_complex).select_by_visible_text(court_complex_name)
        time.sleep(1)
        
        cort_establishment_select()
        
        courts = get_all_courts()
        courts = courts[1:] if len(courts) > 1 else courts
        
        all_data = []
        all_headers = None
        
        for idx, court_name in enumerate(courts, 1):
            if court_name.strip():
                print(f"\n\n{'='*80}")
                print(f"Processing court {idx}/{len(courts)}: {court_name}")
                print(f"{'='*80}")
                
                cort = driver.find_element(By.ID, "CL_court_no")
                Select(cort).select_by_visible_text(court_name)
                time.sleep(2)
                
                captcha_text = scan_captcha()
                enter_captcha_and_submit(captcha_text)
                
                if validate_captcha():
                    table = get_results_table()
                    if table:
                        table_data, headers = extract_and_display_table(court_name)
                        if table_data:
                            all_data.extend(table_data)
                            all_headers = headers
        
        if all_data and all_headers:
            print("\n\n" + "="*80)
            print("ALL COURTS - COMBINED RESULTS")
            print("="*80)
            print(f"\nTotal cases found: {len(all_data)}")
            print(f"Columns: {all_headers}")
            
            # Generate combined PDF
            print("\nGenerating PDF report...")
            pdf_file = generate_pdf_report(all_data, all_headers, "all_courts_report", court_complex_name, state_name, district_name)
            print(f"\n✓ PDF saved as: {pdf_file}")
            
            save_to_csv(all_data, all_headers)
        
        print("\nAll courts processed.")
    elif task == 3:
        get_CNR_number()
        
    else:
        print("Invalid task number. Please enter 1 or 2.")
except Exception as e:
    print(f"\n❌ Error: {e}")
    driver.save_screenshot("error_screenshot.png")
finally:
    print("\n" + "="*80)
    print("✅ PROCESS COMPLETE")
    print("="*80)
    input("Press Enter to close browser...")
    driver.quit()