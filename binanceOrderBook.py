import threading
import logging
import functools
from time import time, sleep
from decimal import Decimal
from binance import ThreadedWebsocketManager

logger = logging.getLogger(__name__)


class BINANCE_ORDER_BOOK(threading.Thread):
    def __init__(self, threadId, name, order_book, api_details):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.order_book = order_book
        self.api_details = api_details
        self.reset_time = 108000
        self.twm = None

    def run(self):
        while True:
            try:
                self._start_ws()
                sleep(self.reset_time)
                self._stop_ws()
            except Exception as e:
                logger.error("Binance WS error: %s", e)
                self._stop_ws()
                sleep(5)

    def _convert_order_data(self, res):
        return [[Decimal(r[0]), Decimal(r[1])] for r in res]

    def _process_message(self, msg, symbol=None):
        if msg.get("e") == "error":
            logger.error("Binance WS stream error: %s", msg)
            return
        if "asks" in msg and "bids" in msg:
            self.order_book[symbol]["sell"] = self._convert_order_data(msg["asks"])
            self.order_book[symbol]["buy"] = self._convert_order_data(msg["bids"])
            self.order_book[symbol]["lastUpdate"] = time()

    def _start_ws(self):
        logger.info("Binance WS starting")
        self.twm = ThreadedWebsocketManager(
            api_key=self.api_details["API_KEY"],
            api_secret=self.api_details["API_SECRET"],
        )
        self.twm.start()
        for pair in self.order_book:
            callback = functools.partial(self._process_message, symbol=pair)
            self.twm.start_depth_socket(callback=callback, symbol=pair, depth=20)

    def _stop_ws(self):
        logger.info("Binance WS stopping")
        if self.twm:
            try:
                self.twm.stop()
            except Exception as e:
                logger.warning("Error stopping Binance WS: %s", e)
            self.twm = None
