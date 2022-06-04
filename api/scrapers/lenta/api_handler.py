from fp.fp import FreeProxy, FreeProxyException


def get_proxy():
    try:
        proxy = FreeProxy(https=True, google=False, elite=True,
                          country_id=['RU'], anonym=True, timeout=0.3,
                          rand=True).get()
        return proxy
    except FreeProxyException:
        # There are no working proxies at this time.
        print('There are no working proxies at this time.')
        return None

if __name__ == '__main__':
    print(get_proxy())