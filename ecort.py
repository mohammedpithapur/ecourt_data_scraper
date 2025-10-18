import re
import time
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import easyocr
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors


# ============================================================================
# SETUP
# ============================================================================

def setup_driver():
    """Initialize and configure Chrome WebDriver"""
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
    return driver


# ============================================================================
# STEP 1-4: SELECTION FUNCTIONS
# ============================================================================

def state_select(driver, wait):
    """Select state from dropdown"""
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
    print(f"[OK] Selected: {statename}")
    time.sleep(1)
    return statename


def district_select(driver, wait):
    """Select district from dropdown"""
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
    print(f"[OK] Selected: {cityname}")
    time.sleep(1)
    return cityname


def cort_complex_select(driver, wait):
    """Select court complex from dropdown"""
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
    print(f"[OK] Selected: {cort_complex_name}")
    time.sleep(1)
    return cort_complex_name


def cort_establishment_select(driver, wait):
    """Select court establishment (optional)"""
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
                print(f"[OK] Selected: {cort_est_name}")
                time.sleep(1)
            else:
                print("[SKIP] Skipped")
        else:
            print("[SKIP] No court establishment options available")
            
    except Exception as e:
        print(f"[SKIP] No court establishment found: {str(e)}")


# ============================================================================
# STEP 5: GET ALL COURTS
# ============================================================================

def get_all_courts(driver, wait):
    """Retrieve all available courts"""
    print("\n" + "="*80)
    print("STEP 5: GET AVAILABLE COURTS")
    print("="*80)
    
    print("\n[WAIT] Waiting for court dropdown to load...")
    time.sleep(2)
    
    cort = driver.find_element(By.ID, "CL_court_no")
    wait.until(lambda d: len(cort.find_elements(By.TAG_NAME, "option")) > 1)
    
    all_options = cort.find_elements(By.TAG_NAME, "option")
    courts = []
    
    for option in all_options:
        is_disabled = option.get_attribute("disabled") is not None
        option_text = option.text.strip()
        
        if not is_disabled and option_text and option_text != "Select Court Name":
            courts.append(option_text)
    
    print(f"\n[OK] Loaded {len(courts)} enabled court options")
    print("\nAvailable courts:")
    for i, court in enumerate(courts, 1):
        print(f"  {i}. {court}")
    
    return courts


# ============================================================================
# CAPTCHA FUNCTIONS
# ============================================================================

def scan_captcha(driver, wait):
    """Capture and process captcha image"""
    print("\n[PROCESS] Capturing captcha...")
    captcha_element = wait.until(
        EC.presence_of_element_located((By.XPATH, "//img[contains(@src,'captcha') or contains(@id,'captcha')]"))
    )
    
    captcha_element.screenshot('captcha.png')
    print("[OK] Captcha image saved as 'captcha.png'")
    
    driver.save_screenshot('full_page_before_submit.png')
    print("[OK] Full page screenshot saved")
    
    print("[PROCESS] Processing captcha image...")
    img = Image.open('captcha.png').convert('L')
    img = img.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    img.save('captcha_processed.png')
    
    print("[PROCESS] Solving captcha with EasyOCR...")
    reader = easyocr.Reader(['en'])
    result = reader.readtext('captcha_processed.png')
    
    captcha_text = ''.join([text[1] for text in result if text[2] > 0.3]).strip()
    captcha_text = ''.join(c for c in captcha_text if c.isalnum())
    
    print(f"[OK] Captcha solved: '{captcha_text}'")
    return captcha_text


def enter_captcha_and_submit(driver, captcha_text):
    """Enter captcha and submit form"""
    print("\n[INPUT] Entering captcha...")
    captcha_input = driver.find_element(By.ID, "cause_list_captcha_code")
    captcha_input.clear()
    captcha_input.send_keys(captcha_text)
    print(f"[OK] Captcha entered: {captcha_text}")
    
    print("[ACTION] Clicking submit button...")
    submit_btn = driver.find_element(By.XPATH, "//button[text()='Civil']")
    driver.execute_script("arguments[0].click();", submit_btn)
    print("[OK] Submit button clicked")
    time.sleep(2)


def enter_captcha_and_submit_cnr(driver, captcha_text="fhgjkj"):
    """Enter captcha and submit CNR form"""
    print("\n[INPUT] Entering captcha...")
    captcha_input = driver.find_element(By.ID, "fcaptcha_code")
    captcha_input.clear()
    captcha_input.send_keys(captcha_text)
    print(f"[OK] Captcha entered: {captcha_text}")
    
    print("[ACTION] Clicking submit button...")
    submit_btn = driver.find_element(By.XPATH, "//button[text()='Search']")
    driver.execute_script("arguments[0].click();", submit_btn)
    print("[OK] Submit button clicked")
    time.sleep(2)


def validate_captcha(driver, wait, captcha_func):
    """Validate captcha with retry logic"""
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
                print("\n[WARNING] Modal detected on page...")
                
                try:
                    error_alerts = driver.find_elements(By.CLASS_NAME, "alert-danger-cust")
                    success_alerts = driver.find_elements(By.CLASS_NAME, "alert-success-cust")
                    
                    if error_alerts:
                        error_msg = error_alerts[0]
                        error_text = error_msg.text.strip()
                        error_display = error_msg.value_of_css_property("display")
                        
                        if error_display != "none" and error_text:
                            retry_count += 1
                            print(f"\n[ERROR] Captcha was incorrect! (Attempt {retry_count}/{max_retries})")
                            print(f"[ERROR] {error_text}")
                            
                            if retry_count >= max_retries:
                                print(f"\n[ERROR] Maximum captcha attempts ({max_retries}) reached.")
                                driver.save_screenshot("max_retries_reached.png")
                                return False
                            
                            print("[RETRY] Retrying with new captcha...")
                            time.sleep(1)
                            
                            try:
                                close_btn = driver.find_element(By.XPATH, "//button[@class='btn-close']")
                                driver.execute_script("arguments[0].click();", close_btn)
                                print("[OK] Modal closed")
                                time.sleep(2)
                            except:
                                try:
                                    driver.execute_script("document.querySelector('.modal-content').closest('.modal').style.display='none';")
                                    time.sleep(2)
                                except:
                                    driver.refresh()
                                    time.sleep(3)
                            
                            captcha_text = scan_captcha(driver, wait)
                            captcha_func(captcha_text)
                        
                        elif success_alerts and success_alerts[0].value_of_css_property("display") != "none":
                            success_text = success_alerts[0].text.strip()
                            print(f"[OK] Success message received: {success_text}")
                            check_captcha_retry = False
                        else:
                            print("[OK] No error or success message - proceeding...")
                            check_captcha_retry = False
                    else:
                        print("[OK] No error alert found - proceeding...")
                        check_captcha_retry = False
                        
                except Exception as e:
                    print(f"[ERROR] Error reading modal content: {str(e)}")
                    check_captcha_retry = False
            else:
                print("[OK] No modal found - captcha accepted!")
                check_captcha_retry = False
                
        except Exception as e:
            print(f"[ERROR] Error checking for modal: {str(e)}")
            check_captcha_retry = False
    
    return True


# ============================================================================
# RESULTS EXTRACTION
# ============================================================================

def get_results_table(driver, wait):
    """Wait for and retrieve results table"""
    print("\n" + "="*80)
    print("WAITING FOR RESULTS")
    print("="*80)
    
    try:
        print("\n[WAIT] Waiting for results table to load...")
        table = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "dispTable"))
        )
        print("[OK] Results table loaded successfully!")
        
        driver.save_screenshot('results_table_loaded.png')
        print("[OK] Results page screenshot saved")
        
        return table
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        print("[WARNING] Results table not found - No record found")
        return None


def extract_and_display_table(driver, court_name=None):
    """Extract data from results table"""
    print("\n" + "="*80)
    print("EXTRACTING TABLE DATA")
    print("="*80)
    
    try:
        table = driver.find_element(By.ID, "dispTable")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        headers = []
        table_data = []
        
        print(f"\n[INFO] Found {len(rows)} rows in table")
        
        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                cells = row.find_elements(By.TAG_NAME, "th")
            
            row_data = [cell.text.strip() for cell in cells]
            
            if i == 0:
                headers = row_data
                if court_name:
                    headers = ["Court Name"] + headers
                print(f"\n[INFO] Headers: {headers}")
            else:
                if any(row_data):
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
            print("[WARNING] No case data found in table")
            return [], []
        
    except Exception as e:
        print(f"[ERROR] Error extracting table data: {str(e)}")
        driver.save_screenshot("extraction_error.png")
        return [], []


# ============================================================================
# CSV & PDF FUNCTIONS
# ============================================================================

def save_to_csv(table_data, headers):
    """Save table data to CSV file"""
    if table_data and headers:
        save_csv = input("\nSave results to CSV? (y/n): ").strip().lower()
        
        if save_csv == 'y':
            df = pd.DataFrame(table_data, columns=headers)
            filename = f"cause_list_{int(time.time())}.csv"
            df.to_csv(filename, index=False)
            print(f"[OK] Results saved to: {filename}")


def generate_pdf_report(table_data, headers, filename, court_complex_name, state_name, district_name):
    """Generate professional PDF report with case data"""
    pdf_file = f"{filename}_{int(datetime.now().timestamp())}.pdf"
    doc = SimpleDocTemplate(
        pdf_file, 
        pagesize=landscape(A4), 
        topMargin=0.4*inch, 
        bottomMargin=0.4*inch, 
        leftMargin=0.25*inch, 
        rightMargin=0.25*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
        alignment=1
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4,
        alignment=1
    )
    
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
    
    # Prepare table data with wrapped text
    table_data_with_headers = [headers] + table_data
    
    # Process table data
    processed_data = []
    for row_idx, row in enumerate(table_data_with_headers):
        processed_row = []
        for cell_idx, cell in enumerate(row):
            cell_text = str(cell).replace('\n', ' ').replace('\r', '').strip()
            
            if row_idx == 0:
                para = Paragraph(f"<b>{cell_text}</b>", cell_style)
            else:
                para = Paragraph(cell_text, cell_style)
            
            processed_row.append(para)
        processed_data.append(processed_row)
    
    # Calculate column widths
    page_width = landscape(A4)[0] - 0.5*inch
    num_cols = len(headers)
    base_width = page_width / num_cols
    col_widths = [base_width * 0.9] * num_cols
    
    if num_cols > 3:
        col_widths[3] = base_width * 1.2
        if num_cols > 4:
            col_widths[4] = base_width * 1.0
    
    # Create table
    table = Table(processed_data, colWidths=col_widths, repeatRows=1)
    
    # Style table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ROWHEIGHTS', (0, 1), (-1, -1), 0.4*inch),
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Footer
    elements.append(Spacer(1, 0.2*inch))
    footer_text = f"""
    <b>Total Records:</b> {len(table_data)}<br/>
    <b>Report Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}<br/>
    <i>Auto-generated report from eCourts Cause List Extractor. For official purposes, verify with court registry.</i>
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
    print(f"[OK] PDF report generated: {pdf_file}")
    return pdf_file


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_hearing_date(date_str):
    """Check hearing date status (Today, Tomorrow, or date)"""
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    hearing_date = datetime.strptime(date_str, "%d %B %Y").date()
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    
    if hearing_date == today:
        return "Today"
    elif hearing_date == tomorrow:
        return "Tomorrow"
    else:
        return date_str


def get_cnr_number(driver, wait):
    """Get CNR number from user input"""
    print("\n" + "="*80)
    print("ENTER CNR NUMBER")
    print("="*80)
    
    cnr_input = wait.until(EC.presence_of_element_located((By.ID, "cino")))
    cnr_number = input("\nEnter the CNR number (or press Enter to skip): ").strip()
    
    if cnr_number:
        cnr_input.clear()
        cnr_input.send_keys(cnr_number)
        print(f"[OK] Entered CNR number: {cnr_number}")
        time.sleep(1)
        enter_captcha_and_submit_cnr(driver)
    else:
        print("[SKIP] Skipped entering CNR number")


# ============================================================================
# MAIN WORKFLOW FUNCTIONS
# ============================================================================

def process_single_court(driver, wait):
    """Process single court and extract data"""
    print("\n" + "="*80)
    print("TASK 1: ENTER SPECIFIC COURT NAME")
    print("="*80)
    
    state_name = state_select(driver, wait)
    district_name = district_select(driver, wait)
    court_complex_name = cort_complex_select(driver, wait)
    cort_establishment_select(driver, wait)
    
    courts = get_all_courts(driver, wait)
    court_name = input("\nEnter the court name from above: ").strip()
    
    cort = driver.find_element(By.ID, "CL_court_no")
    Select(cort).select_by_visible_text(court_name)
    print(f"[OK] Selected: {court_name}")
    time.sleep(2)
    
    captcha_text = scan_captcha(driver, wait)
    enter_captcha_and_submit(driver, captcha_text)
    
    if validate_captcha(driver, wait, lambda ct: enter_captcha_and_submit(driver, ct)):
        table = get_results_table(driver, wait)
        if table:
            table_data, headers = extract_and_display_table(driver, court_name)
            
            if table_data and headers:
                print("\n[PROCESS] Generating PDF report...")
                try:
                    pdf_file = generate_pdf_report(
                        table_data, headers, "cause_list_report",
                        court_complex_name, state_name, district_name
                    )
                    print(f"[OK] PDF saved as: {pdf_file}")
                except Exception as e:
                    print(f"[ERROR] Error generating PDF: {str(e)}")
            
            save_to_csv(table_data, headers)


def process_all_courts(driver, wait):
    """Process all courts and extract combined data"""
    print("\n" + "="*80)
    print("TASK 2: PRINT ALL CASE DETAILS IN COURT COMPLEX")
    print("="*80)
    
    state_name = state_select(driver, wait)
    district_name = district_select(driver, wait)
    court_complex_name = cort_complex_select(driver, wait)
    cort_establishment_select(driver, wait)
    
    courts = get_all_courts(driver, wait)
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
            
            captcha_text = scan_captcha(driver, wait)
            enter_captcha_and_submit(driver, captcha_text)
            
            if validate_captcha(driver, wait, lambda ct: enter_captcha_and_submit(driver, ct)):
                table = get_results_table(driver, wait)
                if table:
                    table_data, headers = extract_and_display_table(driver, court_name)
                    if table_data:
                        all_data.extend(table_data)
                        all_headers = headers
    
    if all_data and all_headers:
        print("\n\n" + "="*80)
        print("ALL COURTS - COMBINED RESULTS")
        print("="*80)
        print(f"\nTotal cases found: {len(all_data)}")
        print(f"Columns: {all_headers}")
        
        print("\n[PROCESS] Generating PDF report...")
        try:
            pdf_file = generate_pdf_report(
                all_data, all_headers, "all_courts_report",
                court_complex_name, state_name, district_name
            )
            print(f"\n[OK] PDF saved as: {pdf_file}")
        except Exception as e:
            print(f"[ERROR] Error generating PDF: {str(e)}")
        
        save_to_csv(all_data, all_headers)
    
    print("\nAll courts processed.")


def process_cnr_search(driver, wait):
    """Process CNR search"""
    get_cnr_number(driver, wait)
    time.sleep(3)
    
    try:
        table = driver.find_element(By.CSS_SELECTOR, "table.case_status_table")
        data = []
        
        for row in table.find_elements(By.TAG_NAME, "tr"):
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = []
            for cell in cells:
                text = cell.text.strip()
                if text:
                    row_data.append(text)
            data.append(row_data)
        
        if len(data) > 1:
            date = check_hearing_date(data[1][1])
            print(f"\nHearing Date Status: {date}\n")
    except Exception as e:
        print(f"[ERROR] Error retrieving CNR data: {str(e)}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    driver = setup_driver()
    
    print("\n" + "="*80)
    print("eCOURTS CAUSE LIST EXTRACTOR")
    print("="*80)
    print("Task 1 = Enter specific court name")
    print("Task 2 = Print all case details in that court complex")
    print("Task 3 = Enter CNR number to get case details")
    
    task = int(input("\nEnter task number (1, 2, or 3): ").strip())
    
    try:
        if task == 1:
            driver.get(
                "https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/index&app_token=4a71ef6f1714e0abe10fb078271c1cbc080d09e894e34ac793d7a2674224ac61"
            )
            wait = WebDriverWait(driver, 15)
            process_single_court(driver, wait)
            
        elif task == 2:
            driver.get(
                "https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/index&app_token=4a71ef6f1714e0abe10fb078271c1cbc080d09e894e34ac793d7a2674224ac61"
            )
            wait = WebDriverWait(driver, 15)
            process_all_courts(driver, wait)
            
        elif task == 3:
            driver.get(
                "https://services.ecourts.gov.in/ecourtindia_v6/?p=home/index&app_token=e7a718a341cb6057560c8885aaaa8b9bd21b66e8dc9495d2e5f6f109ee796054"
            )
            wait = WebDriverWait(driver, 15)
            process_cnr_search(driver, wait)
        
        else:
            print("[ERROR] Invalid task number. Please enter 1, 2, or 3.")
            
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        driver.save_screenshot("error_screenshot.png")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n" + "="*80)
        print("[OK] PROCESS COMPLETE")
        print("="*80)
        input("Press Enter to close browser...")
        driver.quit()