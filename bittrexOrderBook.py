import threading
import requests
import json
from time import time
from decimal import Decimal

class BITTREX_ORDER_BOOK(threading.Thread):
    def __init__(self, threadID, name, order_book):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.order_book = order_book
        self.markets = self.get_markets()

    def get_markets(self):
        markets = {m : m[-3:] + "-" + m[:-3] for m, _ in self.order_book.items()}
        return markets

    def run(self):
        while True:
            self.get_order_book()

    def convert_order_data(self, res):
        conv_res = []
        for r in res:
            conv_res.append([Decimal(r["Rate"]), Decimal(r["Quantity"])])
        return conv_res

    def get_order_book(self):
        for m, ob in self.order_book.items():
            url = "https://bittrex.com/api/v1.1/public/getorderbook?market=%s&type=both" % self.markets[m]
            res = requests.get(url)
            if res.ok:
                r = res.json()
                if 'result' in r and 'sell' in r['result'] and bool(r['result']['sell']) and len(r['result']['sell']) > 0:
                    self.order_book[m]['sell'] = self.convert_order_data(r['result']['sell'])
                    self.order_book[m]['buy'] = self.convert_order_data(r['result']['buy'])
                    self.order_book[m]['lastUpdate'] = time()
                else:
                    self.order_book[m] = {"sell" : None, "buy" : None, "lastUpdate" : 0}

### HOW TO USE ###
#
#markets = {"ETHBTC" : "BTC-ETH"}
#order_books = {"bittrex" : {"ETHBTC" : {"sell" : None, "buy" : None}}}
#bob = BITTREX_ORDER_BOOK(1, "BITTREX ORDER BOOK", order_books["bittrex"])
#bob.start()
