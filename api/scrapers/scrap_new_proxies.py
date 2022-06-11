import os
import re
import requests_html
import pickle
import requests
import time
import itertools

import numpy as np
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup


px_list = set()
try:
    with open('proxis.pickle', 'rb') as f:
        px_list = pickle.load(f)
except:
    pass

executable_path = os.path.join(os.getcwd(), 'chromedriver', 'chromedriver')

options = Options()
# options.add_argument("start-minimized")
# options.add_argument("--disable-extensions")
options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(executable_path), options=options)  # Service(ChromeDriverManager().install()

city_code = '85'
cookies = {'mg_geo_id': f'{city_code}'}


def split_on_func(list_to_split, delimeter):

    splitted = [[]]
    for item in list_to_split:
        if delimeter(item):
            splitted.append([item])
        else:
            splitted[-1].append(item)

    return [elem for elem in splitted if elem != '' and elem != []]


def proxies_to_df(proxies_list: list) -> pd.DataFrame:
    columns = 'ip, port, code, country, anonymity, google, https, last_checked'.split(', ')
    # data = dict([[name, []] for name in names])
    L = []
    for proxy_list in proxies_list:
        assert len(proxy_list) in (7, 8), f'Length should be 7 or 8, not {len(proxy_string)}'
        if len(proxy_list) == 7:
            proxy_list.insert(5, 'unknown')
        L.append(proxy_list)

    df = pd.DataFrame(L, columns=columns)

    return df

def scrap_proxies():
    session = requests_html.HTMLSession()
    r = session.get('https://free-proxy-list.net/')
    r.html.render()
    for i in range(1, 21):
        proxies_text = r.html.xpath('/html/body/section[1]/div/div[2]/div/table/tbody')[0].text
        px_list = proxies_text.split('\n')
        ip_valid = lambda x: True if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", x) else False
        px_list = split_on_func(list_to_split=px_list, delimeter=ip_valid)

    print(f'---New proxy scraped, left: {len(px_list)}')
    with open('proxis.pickle', 'wb') as f:
        pickle.dump(px_list, f)

    return px_list


def check_proxy(px):
    try:
        requests.get("https://www.google.com/", proxies = {"https": "https://" + px}, timeout = 3)
    except Exception as x:
        print('--'+px + ' is dead: '+ x.__class__.__name__)
        return False
    return True

def get_proxy(scrap = False):
    global px_list
    if scrap or len(px_list) < 6:
            px_list = scrap_proxy()
    while True:
        if len(px_list) < 6:
            px_list = scrap_proxy()
        px = px_list.pop()
        if check_proxy(px):
            break
    print('-'+px+' is alive. ({} left)'.format(str(len(px_list))))
    with open('proxis.pickle', 'wb') as f:
            pickle.dump(px_list, f)
    return px


while True:
    px_list = scrap_proxies()
    df = proxies_to_df(px_list)
    print(df.head())
    PROXY = get_proxy(scrap=True)
    options.add_argument('--proxy-server=%s' % PROXY)
    driver = webdriver.Chrome(chrome_options=options, executable_path=os.path.abspath("chromedriver"))
    try:
        driver.get('https://google.com')
        driver.add_cookie(cookies)
        driver.find_element(By.NAME, 'q').send_keys('Yasser Khalil')
    except:
        print('Captcha!')




# try:
#     # driver.get("https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html")
#     driver.get("https://www.vindecoderz.com/EN/check-lookup/ZDMMADBMXHB001652")
#
#     time.sleep(10)
# except Exception as ex:
#     print(ex)
# finally:
#     driver.close()
#     driver.quit()


# import undetected_chromedriver
# try:
#     driver = undetected_chromedriver.Chrome()
#     # driver.get("https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html")
#     driver.get("https://www.vindecoderz.com/EN/check-lookup/ZDMMADBMXHB001652")
#     time.sleep(15)
# except Exception as ex:
#     print(ex)
# finally:
#     driver.close()
#     driver.quit()