import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.support.ui import Select
from seleniumwire.request import Request
from send_email import send_email
from dotenv import load_dotenv
from driver import get_driver
from db import WebScraperDB
from datetime import datetime, timedelta
import parsel
import os
import time
import json

load_dotenv()


DB_NAME = 'visa.db'
PROFILE_NAME = 'Test Profile'
LOGIN_URL = 'https://ais.usvisa-info.com/es-mx/niv/users/sign_in'
HOME_URL = 'https://ais.usvisa-info.com/es-mx/niv/groups/35287194'
APPOINTMENT_URL = 'https://ais.usvisa-info.com/es-mx/niv/schedule/49257902/appointment'
APPOINTMENT_JSON_URL = 'https://ais.usvisa-info.com/es-mx/niv/schedule/49257902/appointment/days/65.json?appointments[expedite]=false'

SMTP_EMAIL = os.environ.get('EMAIL')
SMTP_PASSWORD = os.environ.get('PASSWORD')

creds = {
    'email': os.environ.get('LOGIN_EMAIL'),
    'password': os.environ.get('LOGIN_PASSWORD')
}

def check_and_click_dialog(driver: uc.Chrome):
    try:
        ok_button = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located("//div[@aria-describedby='flash_messages' and contains(@style, 'display: block')]//button[text()='OK']")

        )
        ActionChains(driver).move_to_element(ok_button).click().perform()
    except:
        pass
    

def login(driver: uc.Chrome):
    driver.get(LOGIN_URL)
    check_and_click_dialog(driver)
    email = driver.find_element(By.ID, 'user_email')
    password = driver.find_element(By.ID, 'user_password')
    policy = driver.find_element(By.ID, "policy_confirmed")
    submit = driver.find_element(By.XPATH, "//form[@class='simple_form new_user']//input[@type='submit']")
    ActionChains(driver, 1000).move_to_element(email).send_keys_to_element(email, creds['email']).move_to_element(password).send_keys_to_element(password, creds['password']).move_to_element(policy).click().move_to_element(submit).click().perform()

def goto_calendar(driver: uc.Chrome):
    continue_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[text()='Continuar']"))
    )
    ActionChains(driver, 1000).move_to_element(continue_btn).click().perform()
    appointment_dropdown = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//ul/li/a/h5/.."))
    )
    appointment_dropdown.click()
    appointment_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Programe la cita')]"))
    )
    appointment_button.click()
    

def refresh_calendar(driver: uc.Chrome):
    driver.refresh()
    if driver.current_url != APPOINTMENT_URL:
        print("LOGGING IN AGAIN...")
        login(driver)
        print("GOING TO CALENDAR...")
        goto_calendar(driver)
    open_calendar(driver)


def open_calendar(driver: uc.Chrome):
    select_location('65')
    calendar = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "appointments_consulate_appointment_date"))
    )
    ActionChains(driver, 1000).move_to_element(calendar).click().perform()

def click_next_calendar(driver: uc.Chrome):
    next_month = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "a.ui-datepicker-next"))
        )
    ActionChains(driver).move_to_element(next_month).click().perform()

def select_location(driver: uc.Chrome, location_option: str):
    location_dropdown = Select(WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "appointments_consulate_appointment_facility_id"))
    ))
    location_dropdown.select_by_value(location_option)

def parse_calendar(html: str):
    selector = parsel.Selector(text=html)
    dates = []
    first_calendar_sel = selector.xpath("//div[@class='ui-datepicker-group ui-datepicker-group-first']")
    month = first_calendar_sel.xpath("./div/div[@class='ui-datepicker-title']/span[@class='ui-datepicker-month']/text()").get()
    year = first_calendar_sel.xpath("./div/div[@class='ui-datepicker-title']/span[@class='ui-datepicker-year']/text()").get()
    days = first_calendar_sel.xpath(".//td[@class=' undefined']/a/text()").getall()
    for day in days:
        dates.append(f"{month} {day}, {year}")
    second_calendar_sel = selector.xpath("//div[@class='ui-datepicker-group ui-datepicker-group-last']")
    month = second_calendar_sel.xpath("./div/div[@class='ui-datepicker-title']/span[@class='ui-datepicker-month']/text()").get()
    year = second_calendar_sel.xpath("./div/div[@class='ui-datepicker-title']/span[@class='ui-datepicker-year']/text()").get()
    days = second_calendar_sel.xpath(".//td[@class=' undefined']/a/text()").getall()
    for day in days:
        dates.append([f"{month} {day}, {year}"])
    return dates

def is_less_than_or_equal_to_one_month_from_today(input_date):
    today = datetime.today().date()
    one_month_later = today + timedelta(days=30)
    return input_date <= one_month_later

def main():
    driver = get_driver('Test Profile', headless=False)
    driver.maximize_window()
    login(driver)
    goto_calendar(driver)
    retry = 0
    while True:
        select_location(driver, '65')
        time.sleep(5)
        appointment_req = None
        for req in driver.requests:
            if req.url == APPOINTMENT_JSON_URL:
                appointment_req = req
                break
        if appointment_req is not None and appointment_req.response is not None and appointment_req.response.status_code == 200 and appointment_req.response.body is not None:
            dates = json.loads(appointment_req.response.body.decode('utf-8'))
            valid_dates = []
            for date in dates:
                temp_date = datetime.strptime(date['date'], "%Y-%m-%d").date()
                if is_less_than_or_equal_to_one_month_from_today(temp_date):
                    valid_dates.append(date['date'])
            if len(valid_dates) > 0:
                print("FOUND NEAREST AVAILABLE DATES")
                with WebScraperDB(DB_NAME) as conn:
                    conn.save_dates([[date] for date in valid_dates])
                with WebScraperDB(DB_NAME) as conn:
                    not_sent_dates = conn.get_all_not_sent()
                    if len(not_sent_dates) > 0:
                        to_mail_dates_str = '\n'.join(not_sent_dates)
                        send_email('Nearest Available Dates', to_mail_dates_str, SMTP_EMAIL, SMTP_PASSWORD)
                        conn.set_sent_all()
                        print("DATES SENT TO EMAIL: ", SMTP_EMAIL)

            else:
                print("NO NEAREST DATE FOUND")
        else:
            retry += 1
            if retry >= 3:
                print("SESSION EXPIRED...")
                print("RELOGGING...")
                login(driver)
                goto_calendar(driver)
                retry = 0
                continue
        select_location(driver, '66')
        time.sleep(5)
        del driver.requests
        

if __name__ == '__main__':
    main()