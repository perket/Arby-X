import threading
from time import time, sleep
import requests
import json
from decimal import Decimal

class BITTREX_V2_ORDER_BOOK(threading.Thread):
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
            
    def test_result(self, res):
        return (res["success"] == True and 
                res["message"] == "" and 
                type(res["result"]) == dict and 
                bool(res["result"]["sell"]) and
                bool(res["result"]["buy"]) and
                len(res["result"]["sell"]) > 0 and
                len(res["result"]["buy"]) > 0
        )

    def sort_book(self, book, order):
        return sorted(book, key=lambda x:x[0], reverse=order)

    def convert_order_data(self, res):
        conv_res = []
        for r in res:
            conv_res.append([Decimal(r["Rate"]), Decimal(r["Quantity"])])
        return conv_res
        
    def get_order_book(self):
        for m, ob in self.order_book.items():
            t0 = time()
            url = 'https://bittrex.com/Api/v2.0/pub/market/getmarketorderbook?marketname={}'.format(self.markets[m])
            res = requests.get(url)
            t1 = time()-t0
            #print(t1)
            if t1 > .05:
                print("OPPS!!!", t1)
            if res.ok and t1 < .2:
                r = res.json()
                if self.test_result(r):
                    self.order_book[m]['sell'] = self.sort_book(self.convert_order_data(r["result"]["sell"]), False) 
                    self.order_book[m]['buy'] = self.sort_book(self.convert_order_data(r["result"]["buy"]), True)
                    self.order_book[m]['lastUpdate'] = time()
                    #print(time() - t0)
                else:
                    self.order_book[m] = {"sell" : None, "buy" : None, "lastUpdate" : 0}
            else:
                self.order_book[m] = {"sell" : None, "buy" : None, "lastUpdate" : 0}
                sleep(1)
