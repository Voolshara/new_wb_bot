from re import T
from flask import Flask, request
from flask_cors import CORS
from random import randint

import pickle
from typer import Typer 

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
import selenium.common.exceptions as Sel_Exceptions
from src.db.database import DB_new



app = Flask(__name__)
CORS(app, resources={
    r"/new_user*": {"origins": "*"},
    }) # настройка CORS POLICY
app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin'

runner = Typer()
driver_dict = {} # all drivers

options = webdriver.ChromeOptions()                                        
options.add_argument("no-sandbox")                                         
options.add_argument('--headless')                                         
options.add_argument("--disable-gpu")                                      
options.add_argument("--window-size=800,600")                              
options.add_argument('--ignore-certificate-errors')                        
options.add_argument('--ignore-ssl-errors')                                
options.add_argument('--ignore-certificate-errors-spki-list')              
options.add_argument("--disable-dev-shm-usage")                            
options.add_experimental_option('excludeSwitches', ['enable-logging'])     
                                                                           

DBN = DB_new() # db
# Global Variables
# ------------------------------------------------------------------------------
# Routes


@app.route('/new_user', methods=['POST'])  # роут сборки шаблонов
def new_user():
    inp = request.json
    if inp["status"] == "phone":
        status, name_of_driver, mes = phone_handler(inp["mes"])
        return {
            "status": status,
            "name_of_driver": name_of_driver,
            "mes": mes
        }
    elif inp["status"] == "sms":
        status, message_from_WB = sms_handler(inp["driver_code"], inp["phone"], inp["sms"])
        return {
            "status": status,
            "mes": message_from_WB
        }
    elif inp["status"] == "repeat_sms":
        status = repeat_sms(inp["driver_code"])
        return {
            "status": status,
        }

@runner.command()
def runner():
    app.run(host="localhost", port="4600") # запуск сервераp


# Routes
# ------------------------------------------------------------------------------
# Handlers


def phone_handler(phone):
    global driver_dict
    driver = webdriver.Chrome(options=options)
    # driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=options)  
    driver.get("https://seller.wildberries.ru/login/ru?redirect_url=/")
    WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "SimpleInput--vVIag"))
                )
    login_input = driver.find_element(By.CLASS_NAME, 'SimpleInput--vVIag')
    login_input.clear()
    login_input.send_keys(phone)
    login_input.send_keys(Keys.ENTER)
    try:
        err_status_element = driver.find_element(By.CLASS_NAME, 'Login-phone__input-error--G4jI5')
        WebDriverWait(err_status_element, 7).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "color-Violet--EA6MO"))
                            )
        driver.close()
        return False, None, err_status_element.find_element(By.CLASS_NAME, 'color-Violet--EA6MO').text
    except:
        if "На номер" in driver.find_element(By.TAG_NAME, "body").text:
            name_of_driver = ""
            for _ in range(16):
                name_of_driver += chr(randint(97, 122))
            
            driver_dict[name_of_driver] = driver
            return True, name_of_driver, None
        else:
            try:
                err_status_element = driver.find_element(By.CLASS_NAME, 'Login-phone__input-error--G4jI5')
                WebDriverWait(err_status_element, 50).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, "color-Violet--EA6MO"))
                                    )
                driver.close()
                return False, None, err_status_element.find_element(By.CLASS_NAME, 'color-Violet--EA6MO').text
            except:
                if "На номер" in driver.text:
                    name_of_driver = ""
                    for _ in range(16):
                        name_of_driver += chr(randint(97, 122))
                    driver_dict[name_of_driver] = driver
                    return True, name_of_driver, None
                return False, None, "Ошибка WB\nПопробуйте сначала /authorization" 


def sms_handler(driver_code, phone, sms):
    global driver_dict
    driver = driver_dict[driver_code]
    login_input = driver.find_element(By.CLASS_NAME, 'Accept-code__form-input--OAwQc')
    login_input.clear()
    login_input.send_keys(sms)
    try:
        print(1)
        err_status_element = driver.find_element(By.CLASS_NAME, 'Accept-code__input-error--M98Yq')
        WebDriverWait(err_status_element, 7).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "color-Violet--EA6MO"))
                            )
        print(1.1)
        err_text = err_status_element.find_element(By.CLASS_NAME, 'color-Violet--EA6MO').text
        if err_text == "Неверный СМС код" or err_text == "Неверные данные доступа":
            print(1.2)
            return False, err_text
        driver.close()
        return False, err_text
        #  status, message_from_WB
    except:
        try: # we need this
            print(2)
            WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ProfileView"))
            )
            print(2.1)
            pickle.dump(driver.get_cookies(),
                        open(f"src/cookies/cookie{phone}", "wb"))
            print(2.2)
            driver.close()
            return True, None            
        except:
            try:
                print(3)
                err_status_element = driver.find_element(By.CLASS_NAME, 'Accept-code__input-error--M98Yq')
                WebDriverWait(err_status_element, 35).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "color-Violet--EA6MO"))
                                )
                print(3.1)
                err_text = err_status_element.find_element(By.CLASS_NAME, 'color-Violet--EA6MO').text
                if err_text == "Неверный СМС код" or err_text == "Неверные данные доступа":
                    return False, err_text
                driver.close()
                return False, err_text
            except:
                try: # repeat sms
                    print(4)
                    WebDriverWait(driver, 4).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, "Button--YsZv8 Button--main---tdBh size-big--DqMCh Button--full-width--DVZvW Button--hover--31M+L"))
                                    )
                    return False, "NEW"
                except: 
                    driver.close()
                    return False, "WB не отвечает \nпопробуйте чуть позже"


def repeat_sms(driver_code):
    global driver_dict
    driver = driver_dict[driver_code]
    button = driver.find_elements(By.TAG_NAME, 'button')[-1]
    if "disabled" in button.get_attribute("class"):
        return False
    button.click()
    return True


# Handlers
# ------------------------------------------------------------------------------
# Tests
def test_driver_connection():
    try: 
        driver = webdriver.Chrome(options=options)
        return True
    except:
        return False