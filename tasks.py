import time
import os
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from twilio.rest import Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_whatsapp_notification(course_name, phone_number, vacancies):
    """Send WhatsApp notification via Twilio"""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_whatsapp_number = "whatsapp:+14155238886"
    to_whatsapp_number = f"whatsapp:+91{phone_number}"

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"The course {course_name} has been successfully selected. Vacancies available: {vacancies}. Please check your ARMS portal.",
            from_=from_whatsapp_number,
            to=to_whatsapp_number
        )
        logger.info(f"WhatsApp message sent to {to_whatsapp_number}: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        return False

def check_course_availability(enrollment_id, course_name, slot, phone_number):
    """Background task to check course availability"""
    from models import db, Enrollment
    
    # Update status to running
    enrollment = Enrollment.query.get(enrollment_id)
    if not enrollment:
        logger.error(f"Enrollment {enrollment_id} not found")
        return
    
    enrollment.status = "running"
    db.session.commit()
    
    # Configure Selenium
    options = Options()
    options.add_argument("--headless")  # Standard headless mode is more compatible
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # For Railway, we need to use a specific Chrome binary path
    # This works with the Chrome buildpack
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        options.binary_location = "/app/.apt/usr/bin/google-chrome"
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Login to the website
        logger.info(f"Logging in to check for course {course_name} in slot {slot}")
        login(driver)
        
        max_attempts = 100  # Limit the number of attempts to avoid infinite loops
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            logger.info(f"Attempt {attempt} checking course {course_name}")
            
            # Navigate to enrollment page and select slot
            go_to_enrollment_page(driver)
            select_slot(driver, slot)
            
            # Check if course is available
            found, vacancies = check_for_course(driver, course_name)
            
            if found:
                logger.info(f"Course {course_name} found with {vacancies} vacancies")
                
                # Update database record
                enrollment.status = "completed"
                enrollment.completed_at = datetime.datetime.utcnow()
                enrollment.vacancies = vacancies
                db.session.commit()
                
                # Send notification
                send_whatsapp_notification(course_name, phone_number, vacancies)
                return True
            
            # Wait before trying again
            time.sleep(10)  # 10 second delay between checks
        
        # If we reach here, the course wasn't found after max attempts
        enrollment.status = "failed"
        enrollment.completed_at = datetime.datetime.utcnow()
        db.session.commit()
        logger.warning(f"Max attempts reached for course {course_name}")
        return False
        
    except Exception as e:
        logger.error(f"Error checking course availability: {str(e)}")
        if enrollment:
            enrollment.status = "failed"
            enrollment.completed_at = datetime.datetime.utcnow()
            db.session.commit()
        return False
    finally:
        if driver:
            driver.quit()

# Include your existing functions
def login(driver):
    driver.get("https://arms.sse.saveetha.com")
    time.sleep(2)  # Wait for page to load

    username = driver.find_element(By.ID, "txtusername")
    password = driver.find_element(By.ID, "txtpassword")
    login_button = driver.find_element(By.ID, "btnlogin")

    username.send_keys(os.environ.get("ARMS_USERNAME"))
    password.send_keys(os.environ.get("ARMS_PASSWORD"))
    login_button.click()

    time.sleep(1)  # Wait for login process to complete

def go_to_enrollment_page(driver):
    driver.get("https://arms.sse.saveetha.com/StudentPortal/Enrollment.aspx")
    time.sleep(1)  # Wait for the enrollment page to load

def select_slot(driver, slot_letter):
    slot_number = ord(slot_letter.upper()) - 64  # Convert letter to number (A=1, B=2, ..., Z=26)

    slot_dropdown = Select(driver.find_element(By.ID, "cphbody_ddlslot"))
    slot_dropdown.select_by_value(str(slot_number))  # Select by value (1 for Slot A, etc.)

    time.sleep(1)  # Wait for any potential loading after selection

def check_for_course(driver, course_name):
    time.sleep(1)
    rows = driver.find_elements(By.CSS_SELECTOR, "#tbltbodyslota tr")

    for row in rows:
        labels = row.find_elements(By.TAG_NAME, "label")
        badges = row.find_elements(By.CLASS_NAME, "badge")

        for label, badge in zip(labels, badges):
            if course_name in label.text:
                vacancies = int(badge.text)
                if vacancies > 0:
                    radio_button = row.find_element(By.CSS_SELECTOR, "input[type='radio']")
                    radio_button.click()
                    logger.info(f"Course {course_name} selected. Vacancies available: {vacancies}")
                    return True, vacancies
                else:
                    logger.info(f"Course '{course_name}' is found but has no vacancies.")
                    return False, 0

    logger.info(f"Course '{course_name}' not found.")
    return False, 0
