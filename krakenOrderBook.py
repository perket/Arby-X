import threading
import json
import logging
from time import time, sleep
from decimal import Decimal
import websocket

logger = logging.getLogger(__name__)

# Kraken WebSocket uses / separator and XBT for BTC
KRAKEN_WS_PAIR_MAP = {}  # filled from order_book keys


def internal_to_ws_pair(market):
    """Convert internal pair name (e.g. ETHBTC) to Kraken WS format (ETH/XBT)."""
    # Assume last 3 chars are base for standard pairs
    # Try common bases in order of length
    for base_len in (3,):
        base = market[-base_len:]
        trade = market[:-base_len]
        k_base = "XBT" if base == "BTC" else base
        k_trade = "XBT" if trade == "BTC" else trade
        return "%s/%s" % (k_trade, k_base)
    return market


def ws_pair_to_internal(ws_pair):
    """Convert Kraken WS pair (ETH/XBT) to internal format (ETHBTC)."""
    parts = ws_pair.split("/")
    if len(parts) != 2:
        return None
    trade = "BTC" if parts[0] == "XBT" else parts[0]
    base = "BTC" if parts[1] == "XBT" else parts[1]
    return trade + base


class KRAKEN_ORDER_BOOK(threading.Thread):
    def __init__(self, threadId, name, order_book):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.order_book = order_book
        self.ws = None
        self.ws_url = "wss://ws.kraken.com/v2"
        self._backoff = 1
        self._max_backoff = 60
        # Build pair mapping
        self.pairs = {}
        for market in order_book:
            ws_pair = internal_to_ws_pair(market)
            self.pairs[ws_pair] = market

    def run(self):
        while True:
            try:
                self._connect()
            except Exception as e:
                logger.error("Kraken WS error: %s", e)
            logger.info("Kraken WS reconnecting in %ss", self._backoff)
            sleep(self._backoff)
            self._backoff = min(self._backoff * 2, self._max_backoff)

    def _connect(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def _on_open(self, ws):
        logger.info("Kraken WS connected")
        self._backoff = 1
        # Subscribe to book channel for all pairs
        sub_msg = {
            "method": "subscribe",
            "params": {
                "channel": "book",
                "depth": 10,
                "symbol": list(self.pairs.keys()),
            },
        }
        ws.send(json.dumps(sub_msg))

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        # v2 API sends channel data as {"channel": "book", "type": "snapshot"/"update", "data": [...]}
        channel = data.get("channel")
        if channel != "book":
            return

        msg_type = data.get("type")
        entries = data.get("data", [])

        for entry in entries:
            symbol = entry.get("symbol")
            if symbol not in self.pairs:
                continue
            market = self.pairs[symbol]

            if msg_type == "snapshot":
                bids = [[Decimal(str(b["price"])), Decimal(str(b["qty"]))] for b in entry.get("bids", [])]
                asks = [[Decimal(str(a["price"])), Decimal(str(a["qty"]))] for a in entry.get("asks", [])]
                self.order_book[market]["buy"] = sorted(bids, key=lambda x: x[0], reverse=True)
                self.order_book[market]["sell"] = sorted(asks, key=lambda x: x[0])
                self.order_book[market]["lastUpdate"] = time()
            elif msg_type == "update":
                self._apply_update(market, entry)

    def _apply_update(self, market, entry):
        # Apply incremental updates
        for bid in entry.get("bids", []):
            price = Decimal(str(bid["price"]))
            qty = Decimal(str(bid["qty"]))
            book = self.order_book[market].get("buy")
            if book is None:
                continue
            # Remove existing level
            book = [b for b in book if b[0] != price]
            if qty > 0:
                book.append([price, qty])
            self.order_book[market]["buy"] = sorted(book, key=lambda x: x[0], reverse=True)[:10]

        for ask in entry.get("asks", []):
            price = Decimal(str(ask["price"]))
            qty = Decimal(str(ask["qty"]))
            book = self.order_book[market].get("sell")
            if book is None:
                continue
            book = [a for a in book if a[0] != price]
            if qty > 0:
                book.append([price, qty])
            self.order_book[market]["sell"] = sorted(book, key=lambda x: x[0])[:10]

        self.order_book[market]["lastUpdate"] = time()

    def _on_error(self, ws, error):
        logger.error("Kraken WS error: %s", error)

    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning("Kraken WS closed: %s %s", close_status_code, close_msg)
