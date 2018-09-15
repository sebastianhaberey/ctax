# raw trade data as returned by ccxt for kraken

kraken_trades = [{
    'amount': 0.02,
    'datetime': '2017-02-02T18:00:20.000Z',
    'fee': {
        'cost': 0.05,
        'currency': 'EUR'
    },
    'id': 'ABCDEF-GHIJK-LMNOPQ',
    'info': {
        'cost': '20.8',
        'fee': '0.05',
        'id': 'ABCDEF-GHIJK-LMNOPQ',
        'margin': '0.00000',
        'misc': '',
        'ordertxid': 'XXXXXX-XXXXX-XXXXXX',
        'ordertype': 'stop market',
        'pair': 'XXBTZEUR',
        'price': '1000.0',
        'time': 1486058420.0,
        'type': 'buy',
        'vol': '0.02'
    },
    'order': 'XXXXXX-XXXXX-XXXXXX',
    'price': 1000.0,
    'side': 'buy',
    'symbol': 'BTC/EUR',
    'timestamp': 1486058420,
    'type': 'stop market'
}, {
    'amount': 15.3,
    'datetime': '2017-02-02T18:00:21.000Z',
    'fee': {
        'cost': 0.02,
        'currency': 'USD'
    },
    'id': 'AAAAAA-AAAAA-AAAAAA',
    'info': {
        'cost': '250.00000',
        'fee': '0.02',
        'id': 'AAAAAA-AAAAA-AAAAAA',
        'margin': '0.00000',
        'misc': '',
        'ordertxid': 'XXXXXX-XXXXX-XXXXXX',
        'ordertype': 'stop market',
        'pair': 'XETHZUSD',
        'price': '1900.2',
        'time': 1486058421.0,
        'type': 'sell',
        'vol': '15.3'
    },
    'order': 'XXXXXX-XXXXX-XXXXXX',
    'price': 150.1,
    'side': 'sell',
    'symbol': 'ETH/USD',
    'timestamp': 1486058421,
    'type': 'stop market'
}]
