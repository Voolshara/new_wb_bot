from asyncio import exceptions
from cProfile import run
from calendar import c
from re import T
from threading import current_thread
from time import sleep
from typer import Typer 
import pickle
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import Keys
import selenium.common.exceptions as Sel_Exceptions
from src.db.database import DB_new, DB_get


runner = Typer()
# database
DBN = DB_new()
DBG = DB_get()

options = webdriver.ChromeOptions()                                        
options.add_argument("no-sandbox")                                         
# options.add_argument('--headless')                                         
options.add_argument("--disable-gpu")                                      
options.add_argument("--window-size=800,600")                              
options.add_argument('--ignore-certificate-errors')                        
options.add_argument('--ignore-ssl-errors')                                
options.add_argument('--ignore-certificate-errors-spki-list')              
options.add_argument("--disable-dev-shm-usage")                            
options.add_experimental_option('excludeSwitches', ['enable-logging'])   


def setup_place(url):
    info_wb = DBG.get_cookie_from_url(url)
    print(info_wb)
    if info_wb is None:
        return None


def current_place(driver):
    place_elements = driver.find_elements(By.CLASS_NAME, 'card__settings__row__box')
    current_place = place_elements[1].find_element(By.TAG_NAME, "span").text
    if "-" in current_place:
        return range(int(current_place.split("-")[0]), int(current_place.split("-")[1]) + 1), "RNG"
    else:
        return int(current_place), "NUM" 


def test():
    place = 1
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()),
        options=options)
    driver.get("https://seller.wildberries.ru")
    for cookie in pickle.load(open( f"src/cookies/cookie+79781248490", "rb")):
        driver.add_cookie(cookie)
    driver.get("https://seller.wildberries.ru/cmp/campaigns/list/active/edit/carousel-auction/1848074")
    status_of_load = True
    try: 
        WebDriverWait(driver, 17).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'card__settings__row__box'))
                                )
    except:
        status_of_load = False
    
    if not status_of_load:
        return None
    run_stavki = True
    is_get_bottom_border = False
    while run_stavki:
        now_place, type_of_place = current_place(driver)
        if type_of_place == "NUM":
            if now_place > place:
                try:
                    driver.find_element(By.CLASS_NAME, 'icon--plus-new-outline').click()
                except:
                    pass
                if is_get_bottom_border:
                    run_stavki = False
            else:
                try:
                    driver.find_element(By.CLASS_NAME, 'icon--minus').click()
                except:
                    pass
                is_get_bottom_border = True
        else:
            if place in now_place or place < max(now_place):
                try:
                    driver.find_element(By.CLASS_NAME, 'icon--minus').click()
                except:
                    pass
                is_get_bottom_border = True
            else:
                try:
                    driver.find_element(By.CLASS_NAME, 'icon--plus-new-outline').click()
                except:
                    pass
                if is_get_bottom_border:
                    run_stavki = False
        sleep(0.15)
    run_stavki = True
    is_get_bottom_border = False
    while run_stavki:
        now_place, type_of_place = current_place(driver)
        if type_of_place == "NUM":
            if now_place > place:
                try:
                    driver.find_element(By.CLASS_NAME, 'icon--plus-new-outline').click()
                except:
                    pass
                if is_get_bottom_border:
                    run_stavki = False
            else:
                try:
                    driver.find_element(By.CLASS_NAME, 'icon--minus').click()
                except:
                    pass
                is_get_bottom_border = True
        else:
            if place in now_place or place < max(now_place):
                try:
                    driver.find_element(By.CLASS_NAME, 'icon--minus').click()
                except:
                    pass
                is_get_bottom_border = True
            else:
                try:
                    driver.find_element(By.CLASS_NAME, 'icon--plus-new-outline').click()
                except:
                    pass
                if is_get_bottom_border:
                    run_stavki = False
        sleep(0.15)
    now_place, type_of_place = current_place(driver)
    driver.find_elements(By.CLASS_NAME, "btn--outline")[2].click()
    cost = driver.find_elements(By.TAG_NAME, "input")[0].get_attribute("value")
    driver.close()
    return now_place



@runner.command()
def runner():
    test()
    # setup_place("https://seller.wildberries.ru/cmp/campaigns/list/active/edit/carousel-auction/1848074")