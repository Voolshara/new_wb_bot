import pickle

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
import selenium.common.exceptions as Sel_Exceptions

import multiprocessing as mp


options = webdriver.ChromeOptions()
options.add_argument("no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=800,600")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
flag_for_close = True


def set_phone(phone):
    driver = webdriver.Chrome(options=options)
    driver.get("https://seller.wildberries.ru/login/ru?redirect_url=/")
    q = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "SimpleInput--vVIag"))
                )
    login_input = driver.find_element(By.CLASS_NAME, 'SimpleInput--vVIag')
    login_input.clear()
    login_input.send_keys(phone)
    login_input.send_keys(Keys.ENTER)
    try:
        WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "text--yon+U color-Violet--EA6MO"))
                )        
        return False, driver.find_element(By.CLASS_NAME, 'text--yon+U color-Violet--EA6MO').text
    except:
        return True, driver


def set_sms(sms, driver, phone):
    login_input = driver.find_element(By.CLASS_NAME, 'Accept-code__form-input--OAwQc')
    login_input.clear()
    login_input.send_keys(sms)
    try:
        err_status_element = driver.find_element(By.CLASS_NAME, 'Accept-code__input-error--M98Yq')
        WebDriverWait(err_status_element, 7).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "color-Violet--EA6MO"))
                            )
        if flag_for_close:
            driver.close()
        return False, err_status_element.find_element(By.CLASS_NAME, 'color-Violet--EA6MO').text
    except:
        try: # we need this
            WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ProfileView"))
            )
            pickle.dump(driver.get_cookies(),
                        open(f"src/cookies/cookie{phone}", "wb"))
            if flag_for_close:
                driver.close()
            return True, None
            
        except:
            err_status_element = driver.find_element(By.CLASS_NAME, 'Accept-code__input-error--M98Yq')
            try:
                WebDriverWait(err_status_element, 70).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "color-Violet--EA6MO"))
                                )
                if flag_for_close:
                    driver.close()
                return False, err_status_element.find_element(By.CLASS_NAME, 'color-Violet--EA6MO').text
            except:
                return False, "WB не отвечает \n попробуйте чуть позже"

