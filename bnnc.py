import hmac
import hashlib
import logging
import requests
from time import time
from decimal import Decimal

logger = logging.getLogger(__name__)


class BINANCE:
    def __init__(self, api_details, currencies):
        self.api_details = api_details
        self.currencies = currencies
        self.name = "binance"

    def auth(self, query):
        return hmac.new(
            self.api_details["API_SECRET"].encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def req(self, url_part, query, method):
        timestamp = str(int(time() * 1000))
        query += "timestamp=" + timestamp
        api_sign = self.auth(query)
        url = self.api_details["API_BASE_URL"] + url_part + query + "&signature=" + api_sign

        header = {
            "Accept": "application/json",
            "User-Agent": "binance/python",
            "X-MBX-APIKEY": self.api_details["API_KEY"],
        }

        try:
            if method == "simple_get":
                url = url.split("?")[0]
                res = requests.get(url, headers=header, timeout=10)
            elif method == "get":
                res = requests.get(url, headers=header, timeout=10)
            elif method == "post":
                res = requests.post(url, headers=header, timeout=10)
            elif method == "delete":
                res = requests.delete(url, headers=header, timeout=10)
            else:
                return None
        except Exception as e:
            logger.error("Binance request failed (%s): %s", url_part, e)
            return None

        if not res.ok:
            logger.error("Binance API error %s: %s", res.status_code, res.text)
        return res

    def getOrderData(self, order_id, currency, base_currency):
        query = "symbol=%s&origClientOrderId=%s&" % (currency + base_currency, order_id)
        res = self.req("/api/v3/order?", query, "get")
        if res is None:
            return None
        r = res.json()

        if "clientOrderId" in r:
            return {
                "quantity": r["origQty"],
                "price": r["price"],
                "quantityRemaining": Decimal(r["origQty"]) - Decimal(r["executedQty"]),
                "open": r["status"] in ("NEW", "PARTIALLY_FILLED"),
            }
        logger.error("Unexpected order response: %s", r)
        return None

    def getFilter(self, f, ft):
        for ff in f:
            if ff["filterType"] == ft:
                return ff
        return None

    def filterHandler(self, f, pick):
        if pick == "ov":
            filt = self.getFilter(f, "MIN_NOTIONAL")
            if filt is None:
                filt = self.getFilter(f, "NOTIONAL")
            if filt:
                return Decimal(filt.get("minNotional", filt.get("minNotional", "0")))
            return Decimal("0")
        elif pick == "rp":
            filt = self.getFilter(f, "PRICE_FILTER")
            if filt is None:
                return 8
            return 0 if filt["tickSize"][0] == "1" else len(filt["tickSize"].split(".")[1].split("1")[0]) + 1
        elif pick == "tv":
            filt = self.getFilter(f, "LOT_SIZE")
            if filt is None:
                return Decimal("0.001")
            return Decimal(filt["minQty"])
        elif pick == "vp":
            filt = self.getFilter(f, "LOT_SIZE")
            if filt is None:
                return 8
            return 0 if filt["stepSize"][0] == "1" else len(filt["stepSize"].split(".")[1].split("1")[0]) + 1
        return None

    def getMarketInfo(self, markets):
        query = ""
        res = self.req("/api/v3/exchangeInfo?", query, "simple_get")
        if res is None:
            return None
        r = res.json()

        if "symbols" in r:
            result = r["symbols"]
            return {
                market: {
                    "minOrderValueBTC": None if info["base"] == "ETH" else self.filterHandler(MI["filters"], "ov"),
                    "minOrderValueETH": None if info["base"] == "BTC" else self.filterHandler(MI["filters"], "ov"),
                    "tradeFees": Decimal("0.001"),
                    "ratePrecision": self.filterHandler(MI["filters"], "rp"),
                    "minTradeVolume": self.filterHandler(MI["filters"], "tv"),
                    "volumePrecision": self.filterHandler(MI["filters"], "vp"),
                }
                for market, info in markets.items()
                for MI in result
                if MI["baseAsset"] == info["trade"] and MI["quoteAsset"] == info["base"]
            }
        return None

    def order(self, currency, base_currency, rate, volume, side):
        query = "symbol=%s&side=%s&timeInForce=GTC&type=LIMIT&quantity=%.8f&price=%.8f&" % (
            (currency + base_currency), side, volume, rate
        )
        res = self.req("/api/v3/order?", query, "post")
        if res is None:
            return False

        r = res.json()
        if res.status_code == 200:
            logger.info("Binance order placed: %s", r.get("clientOrderId"))
            return r["clientOrderId"]

        logger.error("Binance order failed: %s", r)
        return False

    def closeOrder(self, order_id, currency, base_currency):
        query = "origClientOrderId=%s&symbol=%s&" % (order_id, (currency + base_currency))
        res = self.req("/api/v3/order?", query, "delete")
        if res is None:
            return False
        r = res.json()
        if res.status_code == 200:
            logger.info("Binance order cancelled: %s", order_id)
            return True
        logger.warning("Binance cancel failed: %s", r)
        return False

    def getBalances(self):
        query = ""
        res = self.req("/api/v3/account?", query, "get")
        if res is None:
            return None
        r = res.json()

        if "balances" in r:
            return {
                x["asset"]: {
                    "available": Decimal(x["free"]),
                    "reserved": Decimal(x["locked"]),
                    "total": Decimal(x["free"]) + Decimal(x["locked"]),
                }
                for x in r["balances"]
                if x["asset"] in self.currencies
            }

        return None
