import time
from flask import Flask, render_template, request
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from selenium.webdriver.support.ui import Select

# Automatically install the correct version of ChromeDriver
chromedriver_autoinstaller.install()

# Set up Flask
app = Flask(__name__)

# Function to send WhatsApp notification
def send_whatsapp_notification(course_name, phone_number):
    # Your Twilio credentials
    account_sid = "TWILIO_ACCOUNT_SID"  # Replace with your Twilio Account SID
    auth_token = "TWILIO_AUTH_TOKEN"    # Replace with your Twilio Auth Token
    from_whatsapp_number = "whatsapp:+14155238886"  # Twilio sandbox WhatsApp number (or your own)
    to_whatsapp_number = f"whatsapp:+91{phone_number}"  # Receiver's WhatsApp number

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"The course {course_name} has been successfully selected. Please check your browser.",
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )

    print(f"WhatsApp message sent to {to_whatsapp_number}: {message.body}")

# Function to login to the website
def login(driver):
    driver.get("https://arms.sse.saveetha.com")
    time.sleep(2)  # Wait for page to load

    username = driver.find_element(By.ID, "txtusername")
    password = driver.find_element(By.ID, "txtpassword")
    login_button = driver.find_element(By.ID, "btnlogin")

    username.send_keys("192210400")  # Replace with your username
    password.send_keys("Mrcreddy@2005")  # Replace with your password
    login_button.click()

    time.sleep(1)  # Wait for login process to complete

# Function to go to the enrollment page
def go_to_enrollment_page(driver):
    driver.get("https://arms.sse.saveetha.com/StudentPortal/Enrollment.aspx")
    time.sleep(1)  # Wait for the enrollment page to load

# Function to select a slot for course enrollment
def select_slot(driver, slot_letter):
    slot_number = ord(slot_letter.upper()) - 64  # Convert letter to number (A=1, B=2, ..., Z=26)

    slot_dropdown = Select(driver.find_element(By.ID, "cphbody_ddlslot"))
    slot_dropdown.select_by_value(str(slot_number))  # Select by value (1 for Slot A, etc.)

    time.sleep(1)  # Wait for any potential loading after selection

# Function to check for the course in the table
def check_for_course(driver, course_name):
    time.sleep(1)  # Wait for courses to load after selecting the slot

    course_found = False
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

                    print(f"Course {course_name} selected. Vacancies available: {vacancies}")
                    course_found = True
                    return True  # Exit after finding and selecting the course

                else:
                    print(f"Course '{course_name}' is found but has no vacancies.")
                    course_found = True
                    return False  # Course found but full

    if not course_found:
        print(f"Course '{course_name}' not found.")
        return False

# Main function to check for the course and handle actions
def main(course_name, slot, phone_number):
    # Initialize WebDriver
    options = Options()
    options.add_argument("--headless=new")  # Updated headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080") # Fixes potential memory issues

    driver = webdriver.Chrome(options=options)
    
    login(driver)
    go_to_enrollment_page(driver)

    refresh_count = 0  # Initialize refresh counter

    while True:  # Keep checking until manually stopped
        select_slot(driver, slot)  # Select the slot passed by user

        if driver.current_url == "https://arms.sse.saveetha.com/StudentPortal/Enrollment.aspx":
            found = check_for_course(driver, course_name)
            if found:
                print(f"Course {course_name} found! Notifications will be sent.")
                send_whatsapp_notification(course_name, phone_number)  # Send WhatsApp notification
                break  # Exit loop if course is found

        refresh_count += 1  # Increment refresh count
        print(f"Course not found or full. Reloading... (Attempt #{refresh_count})")
        driver.refresh()  # Refresh and check again

        time.sleep(2)  # Wait before checking again

    driver.quit()

# Define routes and views for Flask app
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/enroll', methods=['POST'])
def enroll():
    course_name = request.form['course_name']
    slot = request.form['slot']
    phone_number = request.form['phone_number']
    
    main(course_name, slot, phone_number)
    return f"Enrollment for course {course_name} is successful! Check your WhatsApp."

if __name__ == '__main__':
    app.run(debug=True)
