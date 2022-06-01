
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import firefox
from selenium.webdriver import chrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import os
import json
import sys
import string


os.environ["GH_TOKEN"] = "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"


def pretty_price(inp_price) -> str:
    stripped = inp_price.strip()
    price = ''.join([c if c in string.digits else '' for c in stripped])
    return price + stripped[-1]


def pretty_old(old_price) -> str:
    del_price = str(old_price.contents[1])
    old = re.search("<del>(.+)</del>", del_price)
    if old is None:
        return ""
    old = old.group(1)
    return pretty_price(old)


def parse_product_data(product: str):
    result = dict()
    soup = BeautifulSoup(product, features="lxml")
    low_price = soup.find(attrs={"class": "lower-price"})
    if low_price is not None:
        result["current-price"] = \
            pretty_price(low_price.contents[0])  # pyright:ignore
    old_price = soup.find(attrs={"class": "price-old-block"})
    if old_price is not None:
        result["old-price"] = pretty_old(old_price)
    img = soup.find(name="img")
    if img is not None:
        result["image"] = img.attrs["src"][2:]  # pyright:ignore
    goods_name = soup.find(attrs={"class": "goods-name"})
    if goods_name is not None:
        result["goods-name"] = goods_name.contents[0]  # pyright:ignore
    brand_name = soup.find(attrs={"class": "brand-name"})
    if brand_name is not None:
        result["brand-name"] = brand_name.contents[0]  # pyright:ignore
    return result


def getSoup(url, driver, delay=15):
    print("Start fetching data...")
    driver.get(url)
    try:
        WebDriverWait(driver, delay).until(
            EC.element_to_be_clickable((By.ID, 'filters')))
    except TimeoutException as ex:
        print("Timeout exception")

    soup = BeautifulSoup(driver.page_source, features="lxml")

    driver.close()
    return soup


def parseSoup(soup: BeautifulSoup, element_class="product-card j-card-item j-good-for-listing-event"):
    print("Start parsing...")
    products = soup.find_all(attrs={"class": element_class})
    data = []
    toolbar_width = len(products)

    # start progress bar
    sys.stdout.write("[%s]" % (" " * toolbar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (toolbar_width+1))
    for product in products:
        to_add = parse_product_data(str(product))
        to_add["id"] = product["id"]
        data.append(to_add)

        sys.stdout.write("-")
        sys.stdout.flush()

    sys.stdout.write("]\n")  # this ends the progress bar

    return data


def dumpData(filename: str, data):
    with open(filename, "w", encoding="utf-8") as fp:
        fp.write(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=4))


def create_driver():
    print("Create driver...")
    # Options
    browsers = ["firefox", "chrome"]
    a = ""
    while a not in browsers:
        inp = input("Select browser: \n 1. firefox\n 2. chrome\n ::")
        if not inp.isdigit():
            print("Input must be number.")
            continue
        n = int(inp)
        if n not in [i+1 for i in range(0, len(browsers))]:
            print("Out of range number")
            continue
        a = browsers[n-1]
    if a == "firefox":
        opts = firefox.options.Options()  # pyright:ignore
        opts.headless = True
        return webdriver.Firefox(service=firefox.service.Service(  # pyright:ignore
            GeckoDriverManager().install()), options=opts)
    elif a == "chrome":
        opts = chrome.options.Options()  # pyright:ignore
        opts.headless = True
        return webdriver.Chrome(service=chrome.service.Service(  # pyright:ignore
            ChromeDriverManager().install()), options=opts)
    raise Exception("No driver used")


def main():
    url = input("Enter wildberries catalog url: ")
    filepath = input("Enter filename: ")
    dump_directory = os.path.dirname(os.path.realpath(__file__)) + "/target/"
    if not os.path.exists(dump_directory):
        os.mkdir(dump_directory)
    filepath = f"{dump_directory}{filepath}"
    fullname = f"{filepath}-full.json"
    idsname = f"{filepath}-ids.json"

    driver = create_driver()
    soup = getSoup(url, driver)
    products = parseSoup(
        soup, "product-card j-card-item j-good-for-listing-event")
    print(f"Writing fulldata in {os.path.basename(fullname)}" +
          f" and only id's in {os.path.basename(idsname)}")
    dumpData(fullname, products)
    ids = [item["id"] for item in products]
    dumpData(idsname, ids)


if __name__ == "__main__":
    main()