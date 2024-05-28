from korail2 import *
import time
import sys
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv
import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from google.cloud import documentai_v1beta3 as documentai
from google.protobuf.json_format import MessageToDict

# env 파일 로드
load_dotenv()

app = FastAPI()

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # Headless 모드 활성화

# Selenium 웹 드라이버 생성 (Chrome)
driver = webdriver.Chrome(chrome_options)

# 환경변수 셋팅
KORAIL_ID = os.getenv("KORAIL_ID")
KORAIL_PW = os.getenv("KORAIL_PW")
CARD_NUMBER = os.getenv("CARD_NUMBER")
EXP_MONTH = os.getenv("EXP_MONTH")
EXP_YEAR = os.getenv("EXP_YEAR")
CARD_PASSWORD = os.getenv("CARD_PASSWORD")
AUTH_NUMBER = os.getenv("AUTH_NUMBER")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
PROCESSOR_ID = os.getenv("GOOGLE_CLOUD_PROCESSOR_ID")
PUSHOVER_APP_TOKEN = 'APP_TOKEN'
PUSHOVER_USER_TOKEN = 'USER_TOKEN'

###################################################################################################################
# 예매 API
###################################################################################################################
# DEP = '서울'
# ARV = '부산'
# DEP_DATE = '20240515'
# DEP_TIME = '162800'
PSGRS = [AdultPassenger(1)]
TRAIN_TYPE = TrainType.KTX

class Train(BaseModel):
    departure: str
    destination: str
    date: str
    time: str

@app.post("/reservation")
async def reserve_train(train: Train):
    k = Korail(KORAIL_ID, KORAIL_PW)
    if not k.login():
        print("login fail")
        exit(-1)
    while True:
        notFound = True
        while notFound:
            try:
                sys.stdout.write("Finding Seat %s ➜ %s              \r" % (train.departure, train.destination))
                sys.stdout.flush()
                trains = k.search_train_allday(train.departure, train.destination, train.date, train.time, passengers=PSGRS, train_type=TRAIN_TYPE)
                print(trains)
                print("Found!!")
                notFound = False
            except NoResultsError:
                sys.stdout.write("No Seats                               \r")
                sys.stdout.flush()
                time.sleep(2)
            except Exception as e:
                print(e)
                time.sleep(2)

        k.login()
        seat = None
        ok = False
        try:
            seat = k.reserve(trains[0], passengers=PSGRS)
            ok = True
        except KorailError as e:
            print(e)
            break

        if ok:
            print(seat)
            return seat;

###################################################################################################################
# 결제 API
###################################################################################################################

def handle_alerts(driver):
    while True:
        try:
            alert = WebDriverWait(driver, 1).until(EC.alert_is_present())
            alert.accept()
            print("Alert accepted")
        except:
            # No alert found, sleep for a short while before trying again
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

@app.post("/pay")
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

###################################################################################################################
# 카드 정보 OCR API
###################################################################################################################
def process_document(content: bytes):
    client = documentai.DocumentProcessorServiceClient()

    # 요청 생성
    name = f'projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}'

    document = documentai.types.RawDocument(content=content, mime_type='image/jpeg')

    request = documentai.types.ProcessRequest(name=name, raw_document=document)
    result = client.process_document(request=request)

    # 결과 파싱
    document = result.document
    document_dict = MessageToDict(document._pb)


    # 필요한 정보 추출
    card_info = {
        "card_number": None,
        "expiry_date": None,
        "cvc": None,
    }

    for entity in document_dict.get('entities', []):
        if entity['type'] == 'CARD_NUMBER':
            card_info['card_number'] = entity['mentionText']
        elif entity['type'] == 'EXPIRATION_DATE':
            card_info['expiry_date'] = entity['mentionText']
        elif entity['type'] == 'CVC':
            card_info['cvc'] = entity['mentionText']

    return card_info

@app.post("/extract_card_info")
async def extract_card_info(file: UploadFile = File(...)):
    content = await file.read()

    try:
        card_info = process_document(content)
        return card_info
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

