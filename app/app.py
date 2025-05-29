import os
import logging
from functools import wraps
from flask import Flask, request, Response, render_template, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.firefox import GeckoDriverManager # Consider if automatic driver management is desired
import pandas as pd
import time
import random
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for flash messages

# Logging configuration
LOG_FILE = 'logs/app.log'
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- App Configuration ---
# Uploads and Sessions
UPLOAD_FOLDER = 'uploads' # Already defined, ensure it's here
SESSIONS_FOLDER = 'sessions'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(SESSIONS_FOLDER):
    os.makedirs(SESSIONS_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Ensure Flask config knows it

# Selenium & Sending Logic Configuration
MIN_WAIT_SECONDS = 45
MAX_WAIT_SECONDS = 120
MESSAGES_BEFORE_PAUSE = 20
PAUSE_DURATION_SECONDS = 300
WHATSAPP_WEB_URL = "https://web.whatsapp.com"
WEBDRIVER_WAIT_TIMEOUT = 20 # For elements to appear

# Basic Auth Configuration
BASIC_AUTH_USERNAME = 'admin'
BASIC_AUTH_PASSWORD = 'changeme' # Basic password, to be changed by user

# Uploads configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid."""
    return username == BASIC_AUTH_USERNAME and password == BASIC_AUTH_PASSWORD

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@requires_auth
def home():
    # Retrieve stored data from session if available
    excel_preview = session.pop('excel_preview', None)
    uploaded_filename = session.pop('uploaded_filename', None)
    logging.info('Application home page loaded.')
    return render_template('index.html', 
                           message='Upload an Excel file to begin.', 
                           excel_preview=excel_preview,
                           uploaded_filename=uploaded_filename)

def parse_excel_file(file_path):
    """Parses the Excel file to extract contacts and messages."""
    try:
        df = pd.read_excel(file_path)
        # Assuming columns are named 'PhoneNumber' and 'Message'
        # Adjust column names if they are different in the expected Excel format
        if 'PhoneNumber' not in df.columns or 'Message' not in df.columns:
            logging.error(f"Excel file at {file_path} is missing 'PhoneNumber' or 'Message' column.")
            return None, None, "File is missing required columns: 'PhoneNumber' and 'Message'."
        
        # Keep only necessary columns and drop rows with missing phone numbers
        df = df[['PhoneNumber', 'Message']].dropna(subset=['PhoneNumber'])
        df['PhoneNumber'] = df['PhoneNumber'].astype(str) # Ensure phone numbers are strings
        
        contacts_preview = df.head(10).to_dict('records') # Get first 10 for preview
        all_contacts = df.to_dict('records') # Get all contacts for later processing
        
        logging.info(f"Successfully parsed {len(all_contacts)} contacts from {file_path}.")
        return contacts_preview, all_contacts, None # Return preview, all contacts, and no error
    except Exception as e:
        logging.error(f"Error parsing Excel file {file_path}: {e}")
        return None, None, f"Error parsing Excel file: {e}"

@app.route('/upload', methods=['POST'])
@requires_auth
def upload_file():
    auth = request.authorization
    if 'file' not in request.files:
        flash('No file part', 'error')
        logging.warning(f"File upload attempt by {auth.username if auth else 'unknown'} with no file part.")
        return redirect(url_for('home'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        logging.warning(f"File upload attempt by {auth.username if auth else 'unknown'} with no file selected.")
        return redirect(url_for('home'))
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        try:
            file.save(file_path)
            logging.info(f'File "{original_filename}" uploaded successfully by user {auth.username if auth else "unknown"}. Path: {file_path}')
            
            # Parse the Excel file
            preview_data, all_data, error_message = parse_excel_file(file_path)
            
            if error_message:
                flash(error_message, 'error')
                logging.error(f"Error processing file {original_filename}: {error_message}")
            else:
                flash(f'File "{original_filename}" processed. Preview below.', 'success')
                session['excel_preview'] = preview_data
                session['uploaded_filename'] = original_filename 
                # Store all data for later use in the sending process
                session['all_contacts'] = all_data 
                                    
        except Exception as e:
            flash(f'Error saving or processing file: {e}', 'error')
            logging.error(f'Error saving/processing file "{original_filename}" by user {auth.username if auth else "unknown"}. Exception: {e}')
        return redirect(url_for('home'))
    else:
        flash('Invalid file type. Only .xls and .xlsx are allowed.', 'error')
        logging.warning(f"Invalid file type attempt by {auth.username if auth else 'unknown'}. Filename: {file.filename if file else 'N/A'}")
        return redirect(url_for('home'))

@app.route('/logs_view')
@requires_auth
def view_logs():
    try:
        with open(LOG_FILE, 'r') as f:
            log_content = f.read()
    except FileNotFoundError:
        log_content = "Log file not found."
    except Exception as e:
        log_content = f"Error reading log file: {e}"
    return render_template('logs.html', log_content=log_content)

# Placeholder for Selenium WebDriver initialization
def init_driver(session_id="default"):
    """Initializes and returns a Selenium WebDriver instance."""
    logging.info(f"Attempting to initialize WebDriver for session: {session_id}")
    options = FirefoxOptions()
    options.add_argument("-headless") # Run headless for server environment
    options.add_argument(f"--user-data-dir={os.path.join(SESSIONS_FOLDER, session_id)}") # Session persistence

    service = FirefoxService() # Assumes geckodriver is in PATH

    try:
        driver = webdriver.Firefox(service=service, options=options)
        logging.info(f"WebDriver initialized successfully for session: {session_id}")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver for session {session_id}: {e}")
        if "executable needs to be in PATH" in str(e).lower():
            logging.error("GeckoDriver not found in PATH. Please ensure it is installed and accessible.")
        return None

def send_single_whatsapp_message(driver, number, message):
    """Sends a single WhatsApp message using the provided driver."""
    try:
        number = ''.join(filter(str.isdigit, str(number)))
        encoded_message = quote(message)
        full_url = f"{WHATSAPP_WEB_URL}/send?phone={number}&text={encoded_message}"
        logging.info(f"Navigating to: {full_url}")
        driver.get(full_url)

        input_box_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
        chat_screen_wait_timeout = 60 
        
        try:
            WebDriverWait(driver, chat_screen_wait_timeout).until(
                EC.presence_of_element_located((By.XPATH, input_box_xpath))
            )
            logging.info(f"Message input box found for {number}.")
        except Exception as e:
            qr_code_element_xpath = "//canvas[@aria-label='Scan me!']"
            try:
                driver.find_element(By.XPATH, qr_code_element_xpath)
                logging.warning(f"QR Code screen detected when trying to send to {number}. Manual scan required.")
                return "QR_SCAN_NEEDED"
            except:
                logging.error(f"Message input box not found for {number} after {chat_screen_wait_timeout}s and QR code not detected. Error: {e}")
                return False

        message_input_area = WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, input_box_xpath))
        )
        
        message_input_area.clear()
        time.sleep(random.uniform(0.5, 1.5))
        
        for line in message.split('\n'):
            message_input_area.send_keys(line)
            message_input_area.send_keys(Keys.SHIFT, Keys.ENTER)
        
        message_input_area.send_keys(Keys.ENTER)
        logging.info(f"Message sent to {number}.")
        
        time.sleep(random.uniform(2, 4))
        return True
    except Exception as e:
        logging.error(f"Error sending message to {number}: {e}")
        return False

@app.route('/send_messages', methods=['POST'])
@requires_auth
def send_messages_route():
    contacts = session.get('all_contacts')
    uploaded_filename = session.get('uploaded_filename', 'the uploaded file')

    if not contacts:
        flash('No contacts loaded. Please upload an Excel file first.', 'error')
        return redirect(url_for('home'))

    driver = init_driver()
    if not driver:
        flash('Failed to initialize WebDriver. Check logs. Ensure geckodriver is in PATH and Firefox is installed.', 'error')
        return redirect(url_for('home'))
    
    driver.get(WHATSAPP_WEB_URL)
    time.sleep(5)
    qr_code_element_xpath = "//canvas[@aria-label='Scan me!']"
    try:
        if driver.find_element(By.XPATH, qr_code_element_xpath).is_displayed():
            flash("WhatsApp QR Code scan is required. Please scan the QR code in the browser, then try sending again.", "warning")
            logging.warning("QR Code screen detected on initial load. User needs to scan.")
            # Not quitting driver here to allow user to scan.
            return redirect(url_for('home')) 
    except:
        logging.info("QR code not immediately detected on initial load, proceeding assuming logged in.")

    flash(f'Starting to send messages for {uploaded_filename}. Monitor logs for detailed status.', 'info')
    logging.info(f"Starting message sending process for {len(contacts)} contacts from {uploaded_filename}.")
    
    messages_sent_count = 0
    messages_failed_count = 0

    for i, contact in enumerate(contacts):
        phone_number = contact.get('PhoneNumber')
        message_text = contact.get('Message')

        if not phone_number or not message_text:
            logging.warning(f"Skipping contact due to missing phone number or message: {contact}")
            messages_failed_count += 1
            continue

        logging.info(f"Processing contact {i+1}/{len(contacts)}: {phone_number}")
        
        wait_time = random.uniform(MIN_WAIT_SECONDS, MAX_WAIT_SECONDS)
        if messages_sent_count > 0:
             logging.info(f"Waiting for {wait_time:.2f} seconds before next message...")
             time.sleep(wait_time)

        if messages_sent_count > 0 and messages_sent_count % MESSAGES_BEFORE_PAUSE == 0:
            logging.info(f"Sent {MESSAGES_BEFORE_PAUSE} messages. Pausing for {PAUSE_DURATION_SECONDS} seconds...")
            flash(f"Paused for {PAUSE_DURATION_SECONDS} seconds after {messages_sent_count} messages.", "info")
            time.sleep(PAUSE_DURATION_SECONDS)

        send_status = send_single_whatsapp_message(driver, phone_number, message_text)

        if send_status == "QR_SCAN_NEEDED":
            flash("WhatsApp QR Code scan is required. Please scan the QR code, then try sending again.", "warning")
            logging.warning("QR Code scan detected during sending process. Aborting further sends.")
            return redirect(url_for('home'))
        elif send_status:
            messages_sent_count += 1
            logging.info(f"Message to {phone_number} sent successfully.")
        else:
            messages_failed_count += 1
            logging.warning(f"Failed to send message to {phone_number}.")
        
        session['last_send_status'] = f"Processed: {i+1}/{len(contacts)}. Sent: {messages_sent_count}, Failed: {messages_failed_count}."

    logging.info("Finished sending messages.")
    flash(f"Finished sending messages for {uploaded_filename}. Sent: {messages_sent_count}, Failed: {messages_failed_count}.", "success" if messages_failed_count == 0 else "warning")
    
    if driver:
        driver.quit()
        logging.info("WebDriver session closed.")
    
    session.pop('all_contacts', None)
    # session.pop('excel_preview', None) # Optional: clear preview or keep it
    # session.pop('uploaded_filename', None) # Optional: clear filename or keep it
    session['last_send_status'] = f"Completed. Final Status for {uploaded_filename} - Sent: {messages_sent_count}, Failed: {messages_failed_count}."


    return redirect(url_for('home'))

# Example of a route that might use Selenium (for future development)
# This is just a placeholder to show where it might go.
# @app.route('/start_whatsapp') # Commenting out as it's replaced by /send_messages
# @requires_auth
# def start_whatsapp_session():
#     driver = init_driver() 
#     if driver:
#         try:
#             driver.get("https://web.whatsapp.com")
#             flash("WebDriver started. Please scan QR code if necessary. Check logs for status.", "info")
#             logging.info("WebDriver navigated to web.whatsapp.com. Manual QR scan might be needed.")
#         except Exception as e:
#             flash(f"Error during WebDriver operation: {e}", "error")
#             logging.error(f"Error during WebDriver operation: {e}")
#             if driver:
#                 driver.quit()
#     else:
#         flash("Failed to initialize WebDriver. Check logs.", "error")
#     return redirect(url_for('home'))

if __name__ == '__main__':
    logging.info('Application starting...')
    app.run(debug=True, host='0.0.0.0', port=5000)
