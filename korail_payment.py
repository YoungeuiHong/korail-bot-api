import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import threading
import os
from dotenv import load_dotenv

load_dotenv()

KORAIL_ID = os.getenv("KORAIL_ID")
KORAIL_PW = os.getenv("KORAIL_PW")
CARD_NUMBER = os.getenv("CARD_NUMBER")
EXP_MONTH = os.getenv("EXP_MONTH")
EXP_YEAR = os.getenv("EXP_YEAR")
CARD_PASSWORD = os.getenv("CARD_PASSWORD")
AUTH_NUMBER = os.getenv("AUTH_NUMBER")

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

def handle_alerts(driver):
    while True:
        try:
            alert = WebDriverWait(driver, 1).until(EC.alert_is_present())
            alert.accept()
            print("Alert accepted")
        except:
            time.sleep(0.5)

def login_to_korail(driver, korail_id, korail_pw):
    driver.get("https://www.letskorail.com/korail/com/login.do")
    input_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "txtMember")))
    input_element.send_keys(korail_id)
    input_element = driver.find_element(By.ID, "txtPwd")
    input_element.send_keys(korail_pw)
    btn_login_element = driver.find_element(By.CLASS_NAME, "btn_login")
    btn_login_link = btn_login_element.find_element(By.TAG_NAME, "a")
    btn_login_link.click()

def navigate_to_reservation_page(driver):
    driver.get("https://www.letskorail.com/ebizprd/EbizPrdTicketpr13500W_pr13510.do?1716367172357")

def click_payment_button(driver):
    button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@href='javascript:fn_pay1(0);']")))
    button.click()
    time.sleep(1)
    button2 = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//a[@id='btn_next' and contains(@class, 'btn_blue_ang')]")))
    button2.click()

def enter_card_details(driver, card_number, exp_month, exp_year, password, auth_number):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tabStl1"))).click()
    time.sleep(1)
    card_fields = [driver.find_element(By.NAME, f"txtCardNo{i}") for i in range(1, 5)]
    for field, number in zip(card_fields, [card_number[i:i+4] for i in range(0, 16, 4)]):
        field.send_keys(number)
    Select(driver.find_element(By.ID, "month")).select_by_value(exp_month)
    Select(driver.find_element(By.ID, "year")).select_by_value(exp_year)
    driver.find_element(By.NAME, "txtCCardPwd_1").send_keys(password)
    driver.find_element(By.NAME, "txtJuminNo2_1").send_keys(auth_number)

def agree_and_issue_ticket(driver):
    checkbox = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "chkAgree")))
    if not checkbox.is_selected():
        checkbox.click()
    issuing_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "fnIssuing")))
    issuing_button.click()
    time.sleep(2)

def finalize_payment(driver):
    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "subInfo")))
    time.sleep(2)
    iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'mainframeSaleInfo')))
    driver.switch_to.frame(iframe)
    time.sleep(2)
    pay_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "btn_next2")))
    pay_button.click()

async def pay_train():
    alert_thread = threading.Thread(target=handle_alerts, args=(driver,))
    alert_thread.daemon = True
    alert_thread.start()

    login_to_korail(driver, KORAIL_ID, KORAIL_PW)
    navigate_to_reservation_page(driver)
    click_payment_button(driver)
    enter_card_details(driver, CARD_NUMBER, EXP_MONTH, EXP_YEAR, CARD_PASSWORD, AUTH_NUMBER)
    agree_and_issue_ticket(driver)
    finalize_payment(driver)

    return True
