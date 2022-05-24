
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


start_time = time.time()
current_time = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M')


class LentaParser:
    """
    Парсер товаров магазина Лента
    """
    sleep_time: int = 2
    city_code: str = 85  # Челябинск (Москва=2398) TODO: спарсить все коды городов с сайта магазина
    base_url: str = None  # url-ссылка для парсинга

    user_agent: UserAgent = None
    headers: Dict[str, str] = None
    cookies: Dict[str, str] = None
    session: aiohttp.ClientSession = None

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
            response = await session.get(url=categories_page_url, headers=self.headers, cookies=self.cookies)
            soup = BeautifulSoup(await response.text(), 'lxml')
            group_cards = soup.find_all("a", class_="group-card")
            categories = [card.get('href').split('/')[-2] for card in group_cards]  # ['/catalog/myaso-ptica-kolbasa/', ...]
            print(categories)
            for category in categories:
                category_page_url = f'{categories_page_url}/{category}/'
                await self.gather_data(category_page_url=category_page_url)

    async def gather_data(self, category_page_url: str) -> None:
        """
        Метод формирует таски для парсинга товаров Ленты
        :return:
        """
        self.update_credentials()
        await asyncio.sleep(self.sleep_time)
        async with self.session.get(url=category_page_url, headers=self.headers, cookies=self.cookies) as response:
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
                await asyncio.sleep(self.sleep_time)
                task = asyncio.create_task(self.get_page_data(page_url=f'{category_page_url}/?page={page}'))
                tasks.append(task)

            await asyncio.gather(*tasks)

    async def get_page_data(self, page_url: str) -> None:
        """
        Метод парсит товары с веб-страницы
        :return:
        """
        self.update_credentials()
        await asyncio.sleep(self.sleep_time)
        async with self.session.get(url=page_url, headers=self.headers, cookies=self.cookies) as response:
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
    asyncio.run(parser.parse_categories())
    print(f"Затраченное на работу скрипта время: {time.time() - start_time}")


if __name__ == '__main__':
    main()
