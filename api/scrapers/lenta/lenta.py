
import re
import csv
import json
import numpy as np
from typing import Dict, List
import time
import datetime
import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from fp.fp import FreeProxy, FreeProxyException
import logging
from aiohttp.client_exceptions import ClientProxyConnectionError


logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

start_time = time.time()
current_time = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M')


class LentaParser:
    """
    Парсер товаров магазина Лента
    """
    sleep_time: int = 4
    city_code: str = 85  # Челябинск (Москва=2398) TODO: спарсить все коды городов с сайта магазина
    base_url: str = None  # url-ссылка для парсинга
    categories: List[str] = []
    categories_urls: List[str] = []

    user_agent: UserAgent = None
    headers: Dict[str, str] = None
    cookies: Dict[str, str] = None
    session: aiohttp.ClientSession = None
    proxy: str = None
    statuses = {x for x in range(100, 600)}
    statuses.remove(200)
    statuses.remove(429)

    def __init__(self, base_url: str, city_code: str):
        self.setup_headers(base_url=base_url)
        self.city_code = city_code

    def setup_headers(self, base_url: str):
        """
        :return:
        """
        self.base_url = base_url
        self.user_agent = UserAgent()
        self.update_credentials()
        retries = 12
        counter = 0
        while counter < retries:
            try:
                # self.proxy = FreeProxy(https=False, timeout=0.3, country_id=['UA', 'RU', 'BY']).get()
                # self.proxy = 'http://114.231.45.241:8089'
                # self.proxy = 'http://103.169.148.13:8080'
                # self.proxy = None
                print(self.proxy)
                break
            except:
                pass
            finally:
                counter += 1
                print(f'Retry: {counter}, proxy: {self.proxy}')


    # async def get_proxy(self):
    #     try:
    #         # proxy = await FreeProxy(https=True, country_id=['RU']).get()
    #         # proxy = await FreeProxy(https=True, google=False, elite=True,
    #         #                   country_id=['RU'], anonym=True, timeout=0.3,
    #         #                   rand=True).get()
    #         proxy = await FreeProxy().get()
    #         self.proxy = proxy
    #         return proxy
    #     except FreeProxyException:
    #         # There are no working proxies at this time.
    #         self.proxy = None
    #     finally:
    #         print(f'!!! {self.proxy}')

    def update_credentials(self):
        """
        Метод обновляет хедеры браузера
        :return:
        """
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user-agent": self.user_agent.random
        }
        self.cookies = {'mg_geo_id': f'{self.city_code}'}

    @staticmethod
    def has_attr(x, attribute: str):
        """
        Вспомогательный метод для проверки свойства rel
        :param x:
        :return:
        """
        try:
            x.get(attribute)
            return True
        except AttributeError:
            return False

    async def parse_categories(self) -> None:
        """
        Метод парсит названия категорий и запускает по каждой процесс парсинга
        :return:
        """
        self.update_credentials()
        await asyncio.sleep(self.sleep_time)
        async with aiohttp.ClientSession() as session:
            self.session = session
            categories_page_url = f'{self.base_url}/catalog/'
            response = await session.get(url=categories_page_url, headers=self.headers,
                                         cookies=self.cookies)
            soup = BeautifulSoup(await response.text(), 'lxml')
            group_cards = soup.find_all("a", class_="group-card")
            categories = [card.get('href').split('/')[-2] for card in group_cards]  # ['/catalog/myaso-ptica-kolbasa/', ...]
            print(f'categories: {categories}')
            self.categories = ['myaso-ptica-kolbasa', 'frukty-i-ovoshchi', 'konditerskie-izdeliya', 'chajj-kofe-kakao', 'bakaleya', 'zamorozhennaya-produkciya', 'moloko-syr-yajjco', 'ryba-i-moreprodukty', 'zdorovoe-pitanie', 'produkciya-sobstvennogo-proizvodstva', 'bezalkogolnye-napitki', 'alkogolnye-napitki', 'hleb-i-hlebobulochnye-izdeliya', 'krasota-i-zdorove', 'bytovaya-himiya', 'sport-i-aktivnyjj-otdyh', 'tovary-dlya-zhivotnyh', 'avtotovary', 'bytovaya-tehnika-i-elektronika', 'dacha-sad', 'tovary-dlya-detejj', 'vse-dlya-doma', 'posuda', 'odezhda-i-obuv', 'kancelyariya-i-pechatnaya-produkciya', 'tekstil-dlya-doma', 'cvety']
            self.categories_urls = []
            for category in self.categories:
                # category_page_url = f'{categories_page_url}/{category}/'
                # self.categories.append(category_page_url)
                self.categories_urls.append(f'{categories_page_url}/{category}/')

            await self.categories_parsing()

    async def categories_parsing(self) -> None:
        for category_url in self.categories_urls:
            await asyncio.sleep(self.sleep_time)
            await self.gather_data(category_page_url=category_url)
    
    async def gather_data(self, category_page_url: str) -> None:
        """
        Метод формирует таски для парсинга товаров Ленты
        :return:
        """
        self.update_credentials()
        await asyncio.sleep(self.sleep_time)
        try:
            async with self.session.get(url=category_page_url, headers=self.headers,
                                        cookies=self.cookies, proxy=self.proxy) as response:  # , proxy=proxy
                # self.update_credentials(city_code=self.city_code)
                # response = await session.get(url=self.base_url, headers=self.headers, cookies=self.cookies)
                assert response.status == 200

                tasks = []
                soup = BeautifulSoup(await response.text(), 'lxml')
                pages = [elem.text.strip() for elem in soup.find_all("li", class_="pagination__item")]
                assert np.all([page.isdigit() for page in pages]) == True, 'Не все спаршенные номера страниц числовые!'

                filtered_pages = list(filter(lambda x: self.has_attr(x=x, attribute='rel'), soup.find_all("ul", class_="pagination")[0].contents))
                max_page_num = soup.find_all("ul", class_="pagination")[0].contents
                max_page_num = list(filter(lambda x: self.has_attr(x=x, attribute='rel'), max_page_num))
                max_page_num = list(filter(lambda x: self.has_attr(x=x, attribute='rel'), max_page_num[-1].contents))
                max_page_num = max_page_num[0].get('rel')
                max_page_num = list(filter(lambda x: x.isdigit(), max_page_num))
                max_page_num = max(list(map(int, max_page_num)))
                for page in range(1, max_page_num + 1):
                    # await asyncio.sleep(self.sleep_time)
                    task = asyncio.create_task(self.get_page_data(page_url=f'{category_page_url}/?page={page}'))
                    tasks.append(task)

                await asyncio.gather(*tasks)
        except ClientProxyConnectionError:
            # TODO: добавить смену прокси
            pass



    async def get_page_data(self, page_url: str) -> None:
        """
        Метод парсит товары с веб-страницы
        :return:
        """
        # self.update_credentials()
        await asyncio.sleep(self.sleep_time)
        async with self.session.get(url=page_url, headers=self.headers,
                                    cookies=self.cookies, proxy=self.proxy) as response:
            try:
                assert response.status == 200
                response_text = await response.text()
                soup = BeautifulSoup(response_text, 'lxml')
                target_cards = soup.findAll('div', class_='sku-card-small-container')[0].get('data-model')
                # 'sku-card-small sku-card-small--ecom'
                soup.find_all("div", class_="sku-card-small-container")
                target_cards = json.loads(target_cards)
                print(target_cards)
            except:
                print('!!!')
                pass

def main():
    city_code: int = 85
    base_url = "https://lenta.com"
    parser = LentaParser(base_url=base_url, city_code=city_code)
    # proxy = asyncio.run(parser.get_proxy())

    print(f'proxy = {parser.proxy}')

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(parser.parse_categories())
    loop.run_until_complete(future)

    print(f"Затраченное на работу скрипта время: {time.time() - start_time}")


if __name__ == '__main__':
    main()
