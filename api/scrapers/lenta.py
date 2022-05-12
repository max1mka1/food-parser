
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
    sleep_time: int = 1
    base_url: str = None  # url-ссылка для парсинга
    user_agent: UserAgent = None
    headers: Dict[str, str] = None
    cookies: Dict[str, str] = None
    city_code: str = 85  # Челябинск (Москва=2398) TODO: спарсить все коды городов с сайта магазина

    def __init__(self, base_url: str):
        self.setup_headers(base_url=base_url)

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

    async def get_page_data(self, session: aiohttp.ClientSession, page_url: str):
        """
        Метод парсит товары с веб-страницы
        :return:
        """
        await asyncio.sleep(self.sleep_time)
        self.update_credentials()
        async with session.get(url=page_url, headers=self.headers, cookies=self.cookies) as response:
            assert response.status == 200
            response_text = await response.text()
            soup = BeautifulSoup(response_text, 'lxml')
            target_cards = soup.findAll('div', class_='sku-card-small-container')[0].get('data-model')
            'sku-card-small sku-card-small--ecom'
            soup.find_all("div", class_="sku-card-small-container")
            target_cards = json.loads(target_cards)
            print(target_cards)

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

    async def gather_data(self):
        """
        Метод формирует таски для парсинга товаров Ленты
        :return:
        """
        await asyncio.sleep(self.sleep_time)
        async with aiohttp.ClientSession() as session:
            self.update_credentials(city_code='2398')
            response = await session.get(url=self.base_url, headers=self.headers, cookies=self.cookies)
            assert response.status == 200

            tasks = []
            soup = BeautifulSoup(await response.text(), 'lxml')
            pages = [elem.text.strip() for elem in soup.find_all("li", class_="pagination__item")]
            assert np.all([page.isdigit() for page in pages]) == True, 'Не все спарсенные номера страниц числовые!'

            filtered_pages = list(filter(lambda x: self.has_attr(x=x, attribute='rel'), soup.find_all("ul", class_="pagination")[0].contents))
            max_page_num = soup.find_all("ul", class_="pagination")[0].contents
            max_page_num = list(filter(lambda x: self.has_attr(x=x, attribute='rel'), max_page_num))
            max_page_num = list(filter(lambda x: self.has_attr(x=x, attribute='rel'), max_page_num[-1].contents))
            max_page_num = max_page_num[0].get('rel')
            max_page_num = list(filter(lambda x: x.isdigit(), max_page_num))
            max_page_num = max(list(map(int, max_page_num)))

            for page in range(1, max_page_num + 1):
                await asyncio.sleep(self.sleep_time)
                task = asyncio.create_task(self.get_page_data(session=session,
                                                              page_url=f'{self.base_url}?page={page}'))
                tasks.append(task)

            await asyncio.gather(*tasks)


def main():
    base_url = "https://lenta.com/catalog/frukty-i-ovoshchi/"
    parser = LentaParser(base_url=base_url)
    asyncio.run(parser.gather_data())

    print(f"Затраченное на работу скрипта время: {time.time() - start_time}")


if __name__ == '__main__':
    main()
