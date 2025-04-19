import time
import os
from flask import Flask, render_template, request, jsonify
from twilio.rest import Client
import undetected_chromedriver.v2 as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from threading import Thread

# Flask app
app = Flask(__name__)

# WhatsApp alert function using Twilio
def send_whatsapp_notification(course_name, phone_number, vacancies):
    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_whatsapp_number = "whatsapp:+14155238886"
        to_whatsapp_number = f"whatsapp:+91{phone_number}"

        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=f"The course '{course_name}' has been selected successfully! Vacancies available: {vacancies}. Check ARMS portal.",
            from_=from_whatsapp_number,
            to=to_whatsapp_number
        )
        print(f"[Twilio] Message sent to {to_whatsapp_number}")
    except Exception as e:
        print(f"[Twilio Error] {str(e)}")

# ARMS login function
def login(driver):
    driver.get("https://arms.sse.saveetha.com")
    time.sleep(2)
    driver.find_element(By.ID, "txtusername").send_keys("192210400")  # Replace with secure input
    driver.find_element(By.ID, "txtpassword").send_keys("Mrcreddy@2005")  # Replace with secure input
    driver.find_element(By.ID, "btnlogin").click()
    time.sleep(2)

def go_to_enrollment_page(driver):
    driver.get("https://arms.sse.saveetha.com/StudentPortal/Enrollment.aspx")
    time.sleep(2)

def select_slot(driver, slot_letter):
    slot_number = ord(slot_letter.upper()) - 64
    slot_dropdown = Select(driver.find_element(By.ID, "cphbody_ddlslot"))
    slot_dropdown.select_by_value(str(slot_number))
    time.sleep(2)

def check_for_course(driver, course_name):
    rows = driver.find_elements(By.CSS_SELECTOR, "#tbltbodyslota tr")

    for row in rows:
        labels = row.find_elements(By.TAG_NAME, "label")
        badges = row.find_elements(By.CLASS_NAME, "badge")

        for label, badge in zip(labels, badges):
            if course_name.lower() in label.text.lower():
                vacancies = int(badge.text)
                if vacancies > 0:
                    row.find_element(By.CSS_SELECTOR, "input[type='radio']").click()
                    print(f"[FOUND] {course_name} - Vacancies: {vacancies}")
                    return True, vacancies
                else:
                    print(f"[No Vacancies] {course_name}")
                    return False, 0
    print(f"[NOT FOUND] {course_name}")
    return False, 0

# Main automation
def main(course_name, slot, phone_number):
    try:
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        chromium_path = "/opt/render/project/.chromium-browser/bin/chromium"
        if os.path.exists(chromium_path):
            options.binary_location = chromium_path
            print(f"[✔] Chromium found at {chromium_path}")
        else:
            print(f"[❌] Chromium not found!")
            return

        driver = uc.Chrome(options=options, browser_executable_path=chromium_path)

        login(driver)
        go_to_enrollment_page(driver)

        refresh_count = 0
        while True:
            select_slot(driver, slot)
            if driver.current_url.endswith("Enrollment.aspx"):
                found, vacancies = check_for_course(driver, course_name)
                if found:
                    send_whatsapp_notification(course_name, phone_number, vacancies)
                    break
            refresh_count += 1
            print(f"[Retrying] Attempt #{refresh_count}")
            driver.refresh()
            time.sleep(3)

        driver.quit()
    except Exception as e:
        print(f"[ERROR] {str(e)}")

# Run in background thread
def run_enrollment_task(course_name, slot, phone_number):
    Thread(target=main, args=(course_name, slot, phone_number)).start()

# Routes
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/enroll', methods=['POST'])
def enroll():
    try:
        course_name = request.form['course_name']
        slot = request.form['slot']
        phone_number = request.form['phone_number']

        run_enrollment_task(course_name, slot, phone_number)
        return f"✔ Enrollment started for {course_name}. You will be notified via WhatsApp when it's selected."
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
