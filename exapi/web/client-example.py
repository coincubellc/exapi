#!/usr/bin/env python3
import os
import requests
from pprint import pprint

baseURL = os.getenv('EXAPI_URL') if os.getenv('EXAPI_URL') is not None else 'http://0.0.0.0:9000'


def get_orderbook(exchangeName, base=None, quote=None, count=None, side=None):
    url = baseURL + exchangeName + '/orderbook'
    # example headers, but "Accept" not strictly necessary
    headers = {'Accept': 'application/json'}
    params = {'base' : base, 'quote' : quote, 'count' : count, 'side' : side}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def get_history(exchangeName, base=None, quote=None, count=None):
    url = baseURL + exchangeName + '/history'
    params = {'base' : base, 'quote' : quote, 'count' : count}
    response = requests.get(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content
    

def get_details(exchangeName, base=None, quote=None):
    url = baseURL + exchangeName + '/details'
    params = {'base' : base, 'quote' : quote}
    response = requests.get(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def get_candles(exchangeName, base=None, quote=None, interval=None, start=None, limit=None):
    url = baseURL + exchangeName + '/candles'
    params = {'base' : base, 'quote' : quote, 'interval' : interval, 'start' : start, 'limit' : limit}
    response = requests.get(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def get_balances(exchangeName, key, secret, passphrase=None):
    url = baseURL + exchangeName + '/balances'
    params = {'key' : key, 'secret' : secret, 'passphrase' : passphrase}
    response = requests.get(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def get_order(exchangeName, base, quote, orderid, key, secret, passphrase=None):
    url = baseURL + exchangeName + '/order/' + orderid
    params = {'base' : base, 'quote' : quote, 'key' : key, 'secret' : secret, 'passphrase' : passphrase}
    response = requests.get(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def cancel(exchangeName, base, quote, orderid, key, secret, passphrase=None):
    url = baseURL + exchangeName + '/order/' + orderid
    params = {'base' : base, 'quote' : quote, 'key' : key, 'secret' : secret, 'passphrase' : passphrase}
    response = requests.delete(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def get_orders(exchangeName, base, quote, type, key, secret, passphrase=None):
    url = baseURL + exchangeName + '/orders'
    params = {'base' : base, 'quote' : quote, 'type' : type, 'key' : key, 'secret' : secret, 'passphrase' : passphrase}
    response = requests.get(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def order(exchangeName, base, quote, side, amount, key, secret, passphrase=None, price=None, otype=None):
    url = baseURL + exchangeName + '/orders'
    params = {'base' : base, 'quote' : quote, 'side' : side, 'amount' : amount,
              'otype' : otype, 'price' : price, 'key' : key, 'secret' : secret, 'passphrase' : passphrase}
    response = requests.post(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def test_withdrawal(exchangeName, key, secret, passphrase=None):
    url = baseURL + exchangeName + '/withdrawal/test'
    params = {'key' : key, 'secret' : secret, 'passphrase' : passphrase}
    response = requests.get(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


def test_trading_enabled(exchangeName, key, secret, passphrase=None):
    url = baseURL + exchangeName + '/trade/test'
    params = {'key' : key, 'secret' : secret, 'passphrase' : passphrase}
    response = requests.get(url, params=params)
    response.raise_for_status()
    json_content = response.json()
    return json_content


if __name__ == '__main__':
    balances = get_balances('Binance',
                       key='',
                       secret='')
    # print nonzero balances
    pprint({k:v for (k, v) in balances.items() if v['total'] > 0})
    
    pprint(get_orderbook('Binance', base='ETH', quote='USDT', count=10))
    
    '''
    pprint(order('Binance',
                        base='ETH',
                        quote='USDT',
                        side='sell',
                        amount='0.02',
                        otype='limit',
                        price='850',
                        key='',
                       secret=''))
    '''
    pprint(get_orders('Binance',
                        base='ETH',
                        quote='USDT',
                        type='open',
                       key='',
                       secret=''))
    pprint(cancel('Binance',
                        base='ETH',
                        quote='USDT',
                        orderid='69108580',
                       key='',
                       secret=''))
    
    pprint(get_history('Binance', count=10))
    pprint(get_details('Binance', base='BTC', quote='ETH'))
    pprint(get_candles('Binance', base='BTC', quote='USDT', limit=30))
    pprint(get_balances('Binance',
                       key='',
                       secret=''))
    pprint(test_withdrawal('Binance',
                       key='',
                       secret=''))
    pprint(test_trading_enabled('Binance',
                       key='',
                       secret=''))
    pprint(get_order('Binance',
                        base='ETH',
                        quote='BTC',
                        orderid='111024669',
                       key='',
                       secret=''))
    pprint(get_orders('Binance',
                        base='ETH',
                        quote='BTC',
                        type='open',
                       key='',
                       secret=''))
    pprint(cancel('Binance',
                        base='ETH',
                        quote='BTC',
                        orderid='111024669',
                       key='',
                       secret=''))
    
