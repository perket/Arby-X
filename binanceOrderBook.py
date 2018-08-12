import threading
from time import time, sleep
import functools
from twisted.internet import reactor
from binance.client import Client
from binance.websockets import BinanceSocketManager
from decimal import Decimal
import requests

class BINANCE_ORDER_BOOK(threading.Thread):
    def __init__(self, threadId, name, order_book, api_details):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.order_book = order_book
        self.process_functions = {pair : functools.partial(self.p_data, symbol=pair) for pair, _ in order_book.items()} 
        self.api_details = api_details
        self.reset_time = 108000
        self.client = Client(self.api_details['API_KEY'], self.api_details['API_SECRET']) 
        self.bm = BinanceSocketManager(self.client)
        self.conn_keys = None

    def run(self):
        
        while True:
            self.bm_init()
            sleep(self.reset_time)
            self.bm_reset()
        
    def convert_order_data(self, res):
        conv_data = []
        for r in res:
            conv_data.append([Decimal(r[0]), Decimal(r[1])])
        return conv_data

    def p_data(self, msg, symbol=None):
        self.order_book[symbol]['sell'] = self.convert_order_data(msg['asks'])
        self.order_book[symbol]['buy'] = self.convert_order_data(msg['bids'])
        self.order_book[symbol]['lastUpdate'] = time()

    def bm_init(self):
        print("***START***")
        self.client = Client(self.api_details['API_KEY'], self.api_details['API_SECRET'])
        self.bm = BinanceSocketManager(self.client)
        self.conn_keys = [self.bm.start_depth_socket(pair, f, depth=BinanceSocketManager.WEBSOCKET_DEPTH_20) for pair, f in self.process_functions.items()]
        self.bm.start()
        

    def bm_reset(self):
        print("***STOP***")
        self.bm.close()
        self.bm = None
        self.conn_keys = None
        self.client = None


class BINANCE_ORDER_BOOK2(threading.Thread):
    def __init__(self, threadId, name, order_book, api_details):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.order_book = order_book
        self.api_details = api_details

    def run(self):
        pass

url = "wss://stream.binance.com:9443/ws/ethbtc@depth5"


#order_books = {"binance" : {"ETHBTC" : {"sell" : None, "buy" : None}}}
#bob = BINANCE_ORDER_BOOK(1, "BINANCE ORDER BOOK", order_books["binance"], binance_api_details)
#bob.start()
