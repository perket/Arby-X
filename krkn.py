import hmac
import hashlib
import base64
import urllib.parse
import logging
import requests
from time import time, sleep
from decimal import Decimal

logger = logging.getLogger(__name__)

# Kraken uses XBT instead of BTC
KRAKEN_ASSET_MAP = {"BTC": "XBT"}
REVERSE_ASSET_MAP = {"XBT": "BTC"}


def to_kraken_asset(asset):
    return KRAKEN_ASSET_MAP.get(asset, asset)


def from_kraken_asset(asset):
    # Kraken prefixes assets with X or Z (e.g. XXBT, ZEUR, XETH)
    stripped = asset
    if len(asset) == 4 and asset[0] in ("X", "Z"):
        stripped = asset[1:]
    return REVERSE_ASSET_MAP.get(stripped, stripped)


class KRAKEN:
    def __init__(self, api_details, currencies):
        self.api_key = api_details["API_KEY"]
        self.api_secret = api_details["API_SECRET"]
        self.base_url = "https://api.kraken.com"
        self.currencies = currencies
        self.name = "kraken"
        self.pair_map = {}  # internal name -> kraken name (e.g. ETHBTC -> ETHXBT)
        self._last_private_call = 0

    def _sign(self, uri_path, data):
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + postdata).encode("utf-8")
        message = uri_path.encode("utf-8") + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()

    def _rate_limit(self):
        elapsed = time() - self._last_private_call
        if elapsed < 1.0:
            sleep(1.0 - elapsed)
        self._last_private_call = time()

    def _private_request(self, endpoint, data=None):
        self._rate_limit()
        if data is None:
            data = {}
        uri_path = "/0/private/" + endpoint
        data["nonce"] = str(int(time() * 1000))
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign(uri_path, data),
        }
        try:
            res = requests.post(self.base_url + uri_path, headers=headers, data=data, timeout=10)
            r = res.json()
            if r.get("error") and len(r["error"]) > 0:
                logger.error("Kraken API error (%s): %s", endpoint, r["error"])
                return None
            return r.get("result")
        except Exception as e:
            logger.error("Kraken request failed (%s): %s", endpoint, e)
            return None

    def _public_request(self, endpoint, params=None):
        uri_path = "/0/public/" + endpoint
        try:
            res = requests.get(self.base_url + uri_path, params=params, timeout=10)
            r = res.json()
            if r.get("error") and len(r["error"]) > 0:
                logger.error("Kraken public API error (%s): %s", endpoint, r["error"])
                return None
            return r.get("result")
        except Exception as e:
            logger.error("Kraken public request failed (%s): %s", endpoint, e)
            return None

    def _internal_pair(self, kraken_pair):
        """Convert kraken pair name back to internal format."""
        for internal, kraken in self.pair_map.items():
            if kraken == kraken_pair:
                return internal
        return None

    def _kraken_pair(self, trade, base):
        """Get Kraken pair name from trade/base currencies."""
        internal = trade + base
        return self.pair_map.get(internal)

    def getMarketInfo(self, markets):
        result = self._public_request("AssetPairs")
        if result is None:
            return None

        market_info = {}
        for market, info in markets.items():
            # Compare in internal name space (e.g. ETH, BTC)
            want_trade = info["trade"]
            want_base = info["base"]

            for pair_name, pair_data in result.items():
                # Skip .d (dark pool) pairs
                if pair_name.endswith(".d"):
                    continue
                p_base = pair_data.get("base", "")
                p_quote = pair_data.get("quote", "")
                # Convert Kraken prefixed names to internal names
                if from_kraken_asset(p_base) == want_trade and from_kraken_asset(p_quote) == want_base:
                    self.pair_map[market] = pair_name
                    pair_decimals = pair_data.get("pair_decimals", 5)
                    lot_decimals = pair_data.get("lot_decimals", 8)
                    order_min = Decimal(str(pair_data.get("ordermin", "0.0001")))

                    market_info[market] = {
                        "minOrderValueBTC": order_min if info["base"] == "BTC" else None,
                        "minOrderValueETH": order_min if info["base"] == "ETH" else None,
                        "tradeFees": Decimal("0.0026"),  # 0.26% taker fee
                        "ratePrecision": pair_decimals,
                        "minTradeVolume": order_min,
                        "volumePrecision": lot_decimals,
                    }
                    break

        return market_info

    def order(self, currency, base_currency, rate, volume, side):
        pair = self._kraken_pair(currency, base_currency)
        if not pair:
            logger.error("Unknown pair: %s%s", currency, base_currency)
            return False

        data = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": "limit",
            "price": str(rate),
            "volume": str(volume),
        }
        result = self._private_request("AddOrder", data)
        if result and "txid" in result and len(result["txid"]) > 0:
            txid = result["txid"][0]
            logger.info("Order placed: %s %s %s @ %s vol %s -> %s", side, currency, base_currency, rate, volume, txid)
            return txid
        return False

    def closeOrder(self, order_id, currency, base_currency):
        result = self._private_request("CancelOrder", {"txid": order_id})
        if result and result.get("count", 0) > 0:
            logger.info("Order cancelled: %s", order_id)
            return True
        logger.warning("Failed to cancel order: %s", order_id)
        return False

    def getOrderData(self, order_id, currency, base_currency):
        result = self._private_request("QueryOrders", {"txid": order_id})
        if result and order_id in result:
            order = result[order_id]
            vol = Decimal(order["vol"])
            vol_exec = Decimal(order["vol_exec"])
            price = Decimal(order["price"]) if Decimal(order["price"]) > 0 else Decimal(order.get("descr", {}).get("price", "0"))
            is_open = order["status"] in ("open", "pending")
            return {
                "quantity": str(vol),
                "price": str(price),
                "quantityRemaining": vol - vol_exec,
                "open": is_open,
            }
        return None

    def getBalances(self):
        result = self._private_request("Balance")
        if result is None:
            return None

        balances = {}
        for asset, balance in result.items():
            currency = from_kraken_asset(asset)
            if currency in self.currencies:
                bal = Decimal(balance)
                balances[currency] = {
                    "available": bal,
                    "reserved": Decimal("0"),
                    "total": bal,
                }
        return balances if balances else None
