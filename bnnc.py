from time import time
import hmac
import hashlib
import requests
from decimal import Decimal

class BINANCE():
    def __init__(self, api_details, currencies):
        self.api_details = api_details
        self.currencies = currencies
        self.name = "binance"

    def auth(self, query):
        return hmac.new(self.api_details["API_SECRET"].encode("utf-8") ,query.encode("utf-8"), hashlib.sha256).hexdigest()

    def req(self, url_part, query, method):
        #
        print(query)
        t0 = time()
        timestamp = str(int(time() * 1000))
        query += "timestamp=" + timestamp
        api_sign = self.auth(query)
        url = self.api_details["API_BASE_URL"] + url_part + query + "&signature=" + api_sign

        header = {'apisign' : api_sign, 'Accept': 'application/json', 'User-Agent': 'binance/python', 'X-MBX-APIKEY': self.api_details['API_KEY']} 

        if method == "simple_get":
            url = url.split("?")[0]
            res = requests.get(url, headers = header)
        elif method == "get":
            res = requests.get(url, headers = header)
        elif method == "post":
            res= requests.post(url, headers = header)
        elif method == "delete":
            res =  requests.delete(url, headers = header)
        else:
            return None
        
        print(time()-t0)

        #print(res)
        #print(res.json())
        if not res.ok:
            print(res)
        return res

    def getOrderData(self, order_id, currency, base_currency):
        #
        query = "symbol=%s&" % (currency+base_currency)
        res = self.req("/api/v3/allOrders?", query, "get")
        r = res.json()
        
        if len(r) > 0:
            result = [x for x in r if x["clientOrderId"] == order_id][0]
            return {"quantity" : result["origQty"], "price" : result["price"], "quantityRemaining" : Decimal(result["origQty"]) - Decimal(result["executedQty"]), "open" : True if result["status"] in ["NEW", "PARTIALLY_FILLED"] else False}
        print(r)
        return None

    def getFilter(self, f, ft):
        # Selecting correct filter (extension to filterHandler()).
        r = None
        for ff in f:
            if ff["filterType"] == ft:
                r = ff
        return r

    def filterHandler(self, f, pick):
        # Function that handles information about binance filters.
        if pick == "ov":
            filt = self.getFilter(f, "MIN_NOTIONAL")
            return Decimal(filt["minNotional"])
        elif pick == "rp":
            filt = self.getFilter(f, "PRICE_FILTER")

            return 0 if filt["tickSize"][0] == "1" else len(filt["tickSize"].split(".")[1].split("1")[0]) + 1
        elif pick == "tv":
            filt = self.getFilter(f, "LOT_SIZE")
            return Decimal(filt["minQty"])
        elif pick == "vp":
            filt = self.getFilter(f, "LOT_SIZE")
            return 0 if filt["stepSize"][0] == "1" else len(filt["stepSize"].split(".")[1].split("1")[0]) + 1
        return None

    def getMarketInfo(self, markets):
        # 
        query = ""
        res = self.req("/api/v1/exchangeInfo?", query, "simple_get")
        r = res.json()
        
        if "symbols" in r:
            result = r["symbols"]
            return {market : {"minOrderValueBTC" : None if info["base"] == "ETH" else self.filterHandler(MI["filters"], "ov"), "minOrderValueETH" : None if info["base"] == "BTC" else self.filterHandler(MI["filters"], "ov"), "tradeFees" : Decimal(.001 * 0.3), "ratePrecision" : self.filterHandler(MI["filters"], "rp"), "minTradeVolume" : self.filterHandler(MI["filters"], "tv"), "volumePrecision" : self.filterHandler(MI["filters"], "vp")} for market, info in markets.items() for MI in result if MI["baseAsset"] == info["trade"] and MI["quoteAsset"] == info["base"]}
        return None

    def order(self, currency, base_currency, rate, volume, side):
        # Takes a tradepair (currency + base_currency), rate, volume and side (buy/sell) returns order id 
        query = "symbol=%s&side=%s&timeInForce=GTC&type=LIMIT&quantity=%.8f&price=%.8f&" % ((currency+base_currency), side, volume, rate)
        res = self.req("/api/v3/order?", query, "post")

        r = res.json()
        print(r)
        if res.status_code == 200:
            return r["clientOrderId"]

        return False

    def closeOrder(self, order_id, currency, base_currency):
        # Takes a order_id, returns close response
        query = "origClientOrderId=%s&symbol=%s&" % (order_id, (currency+base_currency))
        res = self.req("/api/v3/order?", query, "delete")
        print(res.json())
        return True
        
    def getBalances(self):
        # Takes a list of currencies and returns a dict like this : {"BTC" : {"available" : .05, "reserved" : 0, "total" : .05}, ...}
        query = ""
        res = self.req("/api/v3/account?" ,query, "get")
        r = res.json()
        
        if "balances" in r:
            return {x["asset"] : {"available" : Decimal(x["free"]), "reserved" : Decimal(x["locked"]), "total" : Decimal(x["free"]) + Decimal(x["locked"])} for x in r["balances"] if x["asset"] in self.currencies}
        
        return None

