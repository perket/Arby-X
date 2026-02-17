import os
import sys
import threading
import logging
from time import time, sleep
from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP

from dotenv import load_dotenv

from bnnc import BINANCE
from krkn import KRAKEN
from binanceOrderBook import BINANCE_ORDER_BOOK
from krakenOrderBook import KRAKEN_ORDER_BOOK
from saveToDb import save_wallets, save_order, save_order_data

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# 0 - Only base, 1 - Both base and trade, 2 - Trade only (all bases), 3 - Trade only (BTC exclusive)
currencies = {"ETH": 2, "BTC": 0, "XLM": 2, "XRP": 2, "ADA": 2}

MIN_ARB = Decimal("0.005")
MIN_VOLUME_DIFF = Decimal("2")
MIN_VOLUME_MARGIN = Decimal("2")
MAX_TIME_SINCE_UPDATE = Decimal("5")

markets = {
    trade + base: {"base": base, "trade": trade}
    for trade, x in currencies.items()
    for base, v in currencies.items()
    if (v < 2 and 0 < x < 3 and base != trade) or (x == 3 and v == 0)
}

# --- API credentials ---
binance_api_details = {
    "API_KEY": os.environ.get("BINANCE_API_KEY", ""),
    "API_SECRET": os.environ.get("BINANCE_API_SECRET", ""),
    "API_BASE_URL": os.environ.get("BINANCE_API_BASE_URL", "https://api.binance.com"),
}
kraken_api_details = {
    "API_KEY": os.environ.get("KRAKEN_API_KEY", ""),
    "API_SECRET": os.environ.get("KRAKEN_API_SECRET", ""),
}

# --- Validate required env vars ---
def _validate_env():
    required = ["BINANCE_API_KEY", "BINANCE_API_SECRET", "KRAKEN_API_KEY", "KRAKEN_API_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        logger.warning("Missing environment variables: %s", ", ".join(missing))
        logger.warning("The bot will start but trading will fail without valid API keys.")

# --- Thread locks ---
order_book_lock = threading.Lock()
wallets_lock = threading.Lock()
data_lock = threading.Lock()

# --- Exchanges ---
exchanges = {
    "binance": BINANCE(binance_api_details, currencies),
    "kraken": KRAKEN(kraken_api_details, currencies),
}
order_books = {
    exchange: {
        market: {"sell": None, "buy": None, "lastUpdate": None}
        for market in markets
    }
    for exchange in exchanges
}

wallets = {}
market_info = {}


def init_wallets():
    global wallets
    for name, obj in exchanges.items():
        funds = obj.getBalances()
        if funds is None:
            logger.warning("Could not fetch initial balances for %s, using empty", name)
            funds = {c: {"available": Decimal("0"), "reserved": Decimal("0"), "total": Decimal("0")} for c in currencies}
        wallets[name] = funds


def init_market_info():
    global market_info
    for name, obj in exchanges.items():
        info = obj.getMarketInfo(markets)
        if info is None:
            logger.error("Could not fetch market info for %s", name)
            sys.exit(1)
        market_info[name] = info


# --- Rounding helpers using Decimal.quantize ---
def rnd_down(x, n):
    """Round down to n decimal places."""
    if n <= 0:
        return Decimal(int(x))
    quant = Decimal(10) ** -n
    return Decimal(str(x)).quantize(quant, rounding=ROUND_DOWN)


def rnd_up(x, n):
    """Round up to n decimal places."""
    if n <= 0:
        return Decimal(int(x)) + (1 if Decimal(str(x)) % 1 > 0 else 0)
    quant = Decimal(10) ** -n
    return Decimal(str(x)).quantize(quant, rounding=ROUND_UP)


def rnd(x, n):
    """Round half-up to n decimal places."""
    if n <= 0:
        return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    quant = Decimal(10) ** -n
    return Decimal(str(x)).quantize(quant, rounding=ROUND_HALF_UP)


class TRADE(threading.Thread):
    MAX_RETRIES = 5

    def __init__(self, threadId, name, tradeNum, tradeData, e):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.tradeNum = tradeNum
        self.tradeData = tradeData
        self.e = e
        self.order_value = Decimal("0")
        self.daemon = True

    def run(self):
        while True:
            self.trade()

    def update_rate_and_volume(self, td, order_data):
        self.order_value -= Decimal(str(td["rate"])) * (Decimal(str(order_data["quantity"])) - Decimal(str(order_data["quantityRemaining"])))
        mi = market_info[td["exchange"]][td["market"]]
        change = max(td["rate"] * Decimal("0.001"), Decimal(10) ** -mi["ratePrecision"])
        td["rate"] += (-1 if td["side"] == "SELL" else 1) * change

        if td["side"] == "BUY":
            td["volume"] = rnd_down(self.order_value / td["rate"], mi["volumePrecision"])
        else:
            td["volume"] = rnd_down(Decimal(str(order_data["quantityRemaining"])), mi["volumePrecision"])
        return td

    def trade(self):
        # Wait for signal to trade, with timeout to prevent infinite hang
        signalled = self.e[0].wait(timeout=30)
        if not signalled:
            return

        with data_lock:
            td = self.tradeData[self.tradeNum - 1]
            if not td:
                return

        self.order_value = td["rate"] * td["volume"]
        exchange = exchanges[td["exchange"]]
        retries = 0

        while td["volume"] * td["rate"] > td["minOrderValue"] and retries < self.MAX_RETRIES:
            mi = market_info[td["exchange"]][td["market"]]
            logger.info(
                "%s %s %s %.8f %.8f %s",
                td["exchange"], markets[td["market"]]["trade"],
                markets[td["market"]]["base"], td["rate"], td["volume"], td["side"],
            )
            order_id = exchange.order(
                markets[td["market"]]["trade"],
                markets[td["market"]]["base"],
                rnd(td["rate"], mi["ratePrecision"]),
                rnd(td["volume"], mi["volumePrecision"]),
                td["side"],
            )
            if order_id:
                sleep(1)
                exchange.closeOrder(order_id, markets[td["market"]]["trade"], markets[td["market"]]["base"])
                order_data = exchange.getOrderData(order_id, markets[td["market"]]["trade"], markets[td["market"]]["base"])
                if order_data:
                    td["orderData"].append({
                        "id": order_id,
                        "rate": order_data["price"],
                        "volume": Decimal(str(order_data["quantity"])) - Decimal(str(order_data["quantityRemaining"])),
                    })
                    td = self.update_rate_and_volume(td, order_data)
                else:
                    logger.warning("Could not get order data for %s", order_id)
                    break
            else:
                retries += 1
                backoff = min(2 ** retries, 30)
                logger.warning("Order failed, retry %d/%d in %ds", retries, self.MAX_RETRIES, backoff)
                sleep(backoff)

        self.e[self.tradeNum].set()
        self.e[0].clear()


class MAIN2(threading.Thread):
    def __init__(self, threadId, name, eventFlags, data):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.eventFlags = eventFlags
        self.data = data
        self.highest_arb = Decimal("0")
        self.arb_counter = [0, 0, 0, 0]
        self.daemon = True

    def run(self):
        while True:
            self.compare()
            sleep(0.1)

    def compare(self):
        for market in markets:
            with order_book_lock:
                info = [
                    {
                        "info": self.get_market_info(A, B, market),
                        "A": A, "B": B, "market": market, "makeTrade": False,
                    }
                    for B in exchanges
                    for A in exchanges
                    if A != B
                ]
            best = max(info, key=lambda x: x["info"]["arbitrage"])
            bold = "\033[1m" if best["info"]["arbitrage"] > 0 else "\033[0m"
            ac = ", ".join([str(x) for x in self.arb_counter])
            logger.debug(
                "%s - %.5f%% A:%.8f B:%.8f best:%.8f%% [%s]",
                market, best["info"]["arbitrage"] * 100,
                best["info"]["A"], best["info"]["B"],
                self.highest_arb * 100, ac,
            )
            if best["info"]["arbitrage"] >= MIN_ARB:
                best = self.calc_rates(best)
                best = self.calc_r(best)
                with wallets_lock:
                    best = self.calc_volumes(best)
                if best["makeTrade"]:
                    logger.info("TRADE OPPORTUNITY: %s arb=%.5f%%", market, best["info"]["arbitrage"] * 100)
                    self.trade(best)
                    logger.info(
                        "%s | buy: %.8f, sell: %.8f, r: %.8f",
                        market, best["info"]["A"], best["info"]["B"], best["info"]["r"],
                    )
                    self.update_wallets()
                    self.save_trade(best["market"])
                    with data_lock:
                        self.data[0] = {}
                        self.data[1] = {}
                if best["info"]["arbitrage"] > self.highest_arb:
                    self.highest_arb = best["info"]["arbitrage"]

            self.arb_counter[0] += 1 if best["info"]["arbitrage"] > Decimal("0.004") else 0
            self.arb_counter[1] += 1 if best["info"]["arbitrage"] > Decimal("0.005") else 0
            self.arb_counter[2] += 1 if best["info"]["arbitrage"] > Decimal("0.0075") else 0
            self.arb_counter[3] += 1 if best["info"]["arbitrage"] > Decimal("0.01") else 0
            sleep(0.1)

    def save_trade(self, market):
        order_id = save_order(market)
        save_order_data(self.data[0], order_id)
        save_order_data(self.data[1], order_id)

    def get_market_info(self, A, B, market):
        buy = order_books[A][market]["buy"]
        sell = order_books[B][market]["sell"]
        last_a = order_books[A][market]["lastUpdate"]
        last_b = order_books[B][market]["lastUpdate"]
        zero = {
            "arbitrage": Decimal("0"), "A": Decimal("0"), "B": Decimal("0"),
            "qtyA": Decimal("0"), "qtyB": Decimal("0"), "r": Decimal("0"),
            "minOrderValueA": Decimal("0"), "minOrderValueB": Decimal("0"),
        }

        if not buy or not sell:
            return zero

        # Staleness check
        now = time()
        if last_a is not None and Decimal(str(now - last_a)) > MAX_TIME_SINCE_UPDATE:
            return zero
        if last_b is not None and Decimal(str(now - last_b)) > MAX_TIME_SINCE_UPDATE:
            return zero

        # Use index [0] for best price
        buy_rate = buy[0][0]
        sell_rate = sell[0][0]
        return {
            "arbitrage": buy_rate / sell_rate - 1,
            "A": buy_rate,
            "B": sell_rate,
            "qtyA": Decimal("0"),
            "qtyB": Decimal("0"),
            "r": Decimal("0"),
            "minOrderValueA": Decimal("0"),
            "minOrderValueB": Decimal("0"),
        }

    def calc_rates(self, info):
        buy_rate = info["info"]["A"] / (1 + market_info[info["A"]][info["market"]]["tradeFees"])
        sell_rate = info["info"]["B"] * (1 + market_info[info["B"]][info["market"]]["tradeFees"])
        diff = buy_rate - sell_rate

        info["info"]["A"] = rnd_up(
            (buy_rate - diff / 3) * (1 + market_info[info["A"]][info["market"]]["tradeFees"]),
            market_info[info["A"]][info["market"]]["ratePrecision"],
        )
        info["info"]["B"] = rnd_down(
            (sell_rate + diff / 3) / (1 + market_info[info["B"]][info["market"]]["tradeFees"]),
            market_info[info["B"]][info["market"]]["ratePrecision"],
        )
        return info

    def calc_r(self, info):
        buy_rate = info["info"]["A"] / (1 + market_info[info["A"]][info["market"]]["tradeFees"])
        sell_rate = info["info"]["B"] * (1 + market_info[info["B"]][info["market"]]["tradeFees"])
        info["info"]["r"] = sell_rate / buy_rate
        return info

    def get_min_order_value(self, exchange, info):
        mi = market_info.get(exchange, {}).get(info["market"])
        if mi is None:
            logger.warning("No market info for %s on %s", info["market"], exchange)
            return Decimal("1e99")
        mov_btc = mi["minOrderValueBTC"]
        mov_eth = mi["minOrderValueETH"]
        if markets[info["market"]]["base"] == "BTC":
            if mov_btc is not None:
                return mov_btc
        elif markets[info["market"]]["base"] == "ETH":
            if mov_eth is not None:
                return mov_eth
            elif order_books[exchange]["ETHBTC"]["buy"]:
                return (mov_btc or Decimal("0.0001")) / Decimal(str(order_books[exchange]["ETHBTC"]["buy"][0][0]))
        logger.warning("Could not determine min order value for %s on %s", info["market"], exchange)
        return Decimal("1e99")

    def calc_volumes(self, info):
        # Fix: check base currency on buy exchange (A), trade currency on sell exchange (B)
        buy_exchange = info["A"]
        sell_exchange = info["B"]
        base = markets[info["market"]]["base"]
        trade = markets[info["market"]]["trade"]

        wallet_buy = wallets[buy_exchange].get(base, {}).get("available", Decimal("0"))
        wallet_sell = wallets[sell_exchange].get(trade, {}).get("available", Decimal("0")) * info["info"]["B"]

        info["info"]["minOrderValueA"] = self.get_min_order_value(info["A"], info)
        info["info"]["minOrderValueB"] = self.get_min_order_value(info["B"], info)

        obv_buy = self.get_order_book_value(info["info"]["A"], "buy", info["A"], info["market"]) / 3
        obv_sell = self.get_order_book_value(info["info"]["B"], "sell", info["B"], info["market"]) / 3

        min_val = min(obv_buy, obv_sell, wallet_buy, wallet_sell)
        max_min_order = max(info["info"]["minOrderValueA"], info["info"]["minOrderValueB"])

        if min_val > max_min_order * Decimal("1.25"):
            order_size = min_val
            precision_A = market_info[info["A"]][info["market"]]["volumePrecision"]
            precision_B = market_info[info["B"]][info["market"]]["volumePrecision"]
            if precision_A < precision_B:
                info["info"]["qtyA"] = rnd_down(
                    info["info"]["r"] * order_size / (info["info"]["B"] * (1 + market_info[info["B"]][info["market"]]["tradeFees"])),
                    precision_A,
                )
                info["info"]["qtyB"] = rnd_down(info["info"]["qtyA"] / info["info"]["r"], precision_B)
            else:
                info["info"]["qtyB"] = rnd_down(
                    order_size / (info["info"]["B"] * (1 + market_info[info["B"]][info["market"]]["tradeFees"])),
                    precision_B,
                )
                info["info"]["qtyA"] = rnd_down(info["info"]["r"] * info["info"]["qtyB"], precision_A)
            info["makeTrade"] = True
        return info

    def get_order_book_value(self, rate, mode, exchange, market):
        volume = Decimal("0")
        i = 0
        ob = order_books[exchange][market][mode]
        if not ob:
            return Decimal("0")
        while i < len(ob) and ((mode == "buy" and ob[i][0] >= rate) or (mode == "sell" and ob[i][0] <= rate)):
            volume += ob[i][1]
            i += 1
        return volume * rate

    def trade(self, info):
        with data_lock:
            self.data[0] = {
                "side": "SELL", "exchange": info["A"],
                "rate": info["info"]["A"], "volume": info["info"]["qtyA"],
                "market": info["market"], "minOrderValue": info["info"]["minOrderValueA"],
                "orderData": [],
            }
            self.data[1] = {
                "side": "BUY", "exchange": info["B"],
                "rate": info["info"]["B"], "volume": info["info"]["qtyB"],
                "market": info["market"], "minOrderValue": info["info"]["minOrderValueB"],
                "orderData": [],
            }
        self.eventFlags[0].set()
        # Wait with timeouts to prevent infinite hang
        if not self.eventFlags[1].wait(timeout=60):
            logger.error("TRADE 1 timed out")
        if not self.eventFlags[2].wait(timeout=60):
            logger.error("TRADE 2 timed out")

        self.eventFlags[1].clear()
        self.eventFlags[2].clear()

    def update_wallets(self):
        sleep(1)
        for e_name, obj in exchanges.items():
            funds = None
            for attempt in range(3):
                funds = obj.getBalances()
                if funds is not None:
                    break
                sleep(1)
            if funds is not None:
                with wallets_lock:
                    wallets[e_name] = funds
            else:
                logger.error("Failed to update wallets for %s after 3 attempts", e_name)
        print_wallets()


def print_wallets():
    sums = {curr: Decimal("0") for curr in currencies}
    with wallets_lock:
        for _, w in wallets.items():
            for c, b in w.items():
                if c in sums:
                    sums[c] += b["total"]

    logger.info("Balances: %s", ", ".join(["%.8f %s" % (b, c) for c, b in sorted(sums.items())]))
    save_wallets(sums)


if __name__ == "__main__":
    _validate_env()

    logger.info("Initializing market info...")
    init_market_info()
    logger.info("Initializing wallets...")
    init_wallets()

    e = [threading.Event(), threading.Event(), threading.Event()]
    data = [{}, {}]

    binance_ob = BINANCE_ORDER_BOOK(1, "BINANCE_ORDER_BOOK", order_books["binance"], binance_api_details)
    kraken_ob = KRAKEN_ORDER_BOOK(2, "KRAKEN_ORDER_BOOK", order_books["kraken"])
    main = MAIN2(3, "MAIN_LOOP", e, data)
    trade1 = TRADE(4, "TRADE_1", 1, data, e)
    trade2 = TRADE(5, "TRADE_2", 2, data, e)

    binance_ob.daemon = True
    kraken_ob.daemon = True

    logger.info("Starting threads...")
    binance_ob.start()
    kraken_ob.start()
    main.start()
    trade1.start()
    trade2.start()

    # Keep main thread alive
    try:
        while True:
            sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
