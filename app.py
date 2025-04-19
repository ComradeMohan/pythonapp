import time
import os
from flask import Flask, render_template, request
from twilio.rest import Client
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# Flask app
app = Flask(__name__)

# Function to send WhatsApp notification
def send_whatsapp_notification(course_name, phone_number, vacancies):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_whatsapp_number = "whatsapp:+14155238886"
    to_whatsapp_number = f"whatsapp:+91{phone_number}"

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"The course {course_name} has been successfully selected. Vacancies available: {vacancies}. Please check your ARMS portal.",
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )
    print(f"WhatsApp message sent to {to_whatsapp_number}: {message.body}")

# Login to ARMS
def login(driver):
    driver.get("https://arms.sse.saveetha.com")
    time.sleep(2)

    driver.find_element(By.ID, "txtusername").send_keys("192210400")
    driver.find_element(By.ID, "txtpassword").send_keys("Mrcreddy@2005")
    driver.find_element(By.ID, "btnlogin").click()
    time.sleep(1)

def go_to_enrollment_page(driver):
    driver.get("https://arms.sse.saveetha.com/StudentPortal/Enrollment.aspx")
    time.sleep(1)

def select_slot(driver, slot_letter):
    slot_number = ord(slot_letter.upper()) - 64
    slot_dropdown = Select(driver.find_element(By.ID, "cphbody_ddlslot"))
    slot_dropdown.select_by_value(str(slot_number))
    time.sleep(1)

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
                    row.find_element(By.CSS_SELECTOR, "input[type='radio']").click()
                    print(f"Course {course_name} selected. Vacancies available: {vacancies}")
                    return True, vacancies
                else:
                    print(f"Course '{course_name}' is found but has no vacancies.")
                    return False, 0
    print(f"Course '{course_name}' not found.")
    return False, 0

# Main logic
def main(course_name, slot, phone_number):
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # Set the binary location for Render's Chromium
    options.binary_location = "/opt/render/project/.chromium-browser/bin/chromium"

    driver = uc.Chrome(options=options)

    login(driver)
    go_to_enrollment_page(driver)

    refresh_count = 0
    while True:
        select_slot(driver, slot)
        if driver.current_url == "https://arms.sse.saveetha.com/StudentPortal/Enrollment.aspx":
            found, vacancies = check_for_course(driver, course_name)
            if found:
                send_whatsapp_notification(course_name, phone_number, vacancies)
                break

        refresh_count += 1
        print(f"Course not found. Refreshing... Attempt #{refresh_count}")
        driver.refresh()
        time.sleep(2)

    driver.quit()

# Routes
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
