import requests
from bs4 import BeautifulSoup
from random import choice


def get_proxies():
    html = requests.get('https://free-proxy-list.net/').text
    soup = BeautifulSoup(html, 'lxml')
    trs = soup.find('tbody').find_all('tr')
    proxies = []

    for tr in trs:
        tds = tr.find_all('td')
        ip = tds[0].text.strip()
        port = tds[1].text.strip()
        schema = 'https' if 'yes' in tds[6].text.strip() else 'http'
        proxy = {'schema': schema, 'address': ip + ':' + port}
        proxies.append(proxy)

    return proxies

def get_proxy(proxies):
    return choice(proxies)

def get_html(url):
    # proxies = {'https': 'ipaddress:5000'}
    proxies = get_proxies() # {'schema': '', 'address': ''}
    print()
    p = get_proxy(proxies)
    proxy = {p['schema']:p['address']}
    r = requests.get(url, proxies=proxy, timeout=5)
    return r.json()['origin']




def main():
    url = 'http://httpbin.org/ip'
    print(get_html(url))

if __name__ == '__main__':
    main()
