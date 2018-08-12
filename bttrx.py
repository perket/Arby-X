from time import time
import hmac
import hashlib
import requests
from decimal import Decimal

class BITTREX():
    def __init__(self, api_details, currencies):
        self.api_details = api_details
        self.currencies = currencies
        self.name = "bittrex"

    def auth(self, url):
        return hmac.new(self.api_details["API_SECRET"].encode() ,url.encode(), hashlib.sha512).hexdigest()

    def req(self, url):
        #
        t0 = time()
        nonce = str(int(time() * 1000))
        url += "&nonce=" + nonce
        
        api_sign = self.auth(url)
        res = requests.get(url, headers = {"apisign" : api_sign})
        print(time()-t0)
        print()
        if not res.ok:
            print(res)
        return res

    def getOrderData(self, order_id, currency, base_currency):
        #
        url = self.api_details["API_BASE_URL"] + "account/getorder?apikey=" + self.api_details["API_KEY"] + "&uuid=" + order_id
        res = self.req(url)
        if not res.ok:
            return None
        r = res.json()
        if r["success"]:
            result = r["result"]
            return {"quantity" : result["Quantity"], "price" : result["PricePerUnit"], "quantityRemaining" : result["QuantityRemaining"], "open" : result["IsOpen"]}
        print(r)
        return None

    def getMarketInfo(self, markets):
        # 
        url = self.api_details["API_BASE_URL"] + "public/getmarkets?apikey=" + self.api_details["API_KEY"]
        res = self.req(url)
        if not res.ok:
            return None 
        r = res.json()
        
        if r["success"]:
            result = r["result"]
            return {market : {"minOrderValueBTC" : Decimal(.0005), "minOrderValueETH" : None, "tradeFees" : Decimal(.0025), "ratePrecision" : 8, "minTradeVolume" : MI["MinTradeSize"], "volumePrecision" : 8} for market, info in markets.items() for MI in result if MI["MarketCurrency"] == info["trade"] and MI["BaseCurrency"] == info["base"]}
        return None

    def order(self, currency, base_currency, rate, volume, side):
        # Takes a tradepair (currency + base_currency), rate, volume and side (buy/sell) returns order id 
        market = base_currency + "-" + currency
        query = self.api_details["API_KEY"] + "&market=" + market + "&quantity=" + str(volume) + "&rate=" + str(rate) 
        
        if side == "BUY":
            url = self.api_details["API_BASE_URL"] + "market/buylimit?apikey=" + query
        elif side == "SELL":
            url = self.api_details["API_BASE_URL"] + "market/selllimit?apikey=" + query
        else:
            return False
        
        res = self.req(url)
        if not res.ok:
            return False
        r = res.json()

        if r["success"]:
            return r["result"]["uuid"]

        return False

    def closeOrder(self, order_id, currency, base_currency):
        # Takes a order_id, returns close response
        url = self.api_details["API_BASE_URL"] + "market/cancel?apikey=" + self.api_details["API_KEY"] + "&uuid=" + order_id
        res = self.req(url)
        if not res.ok:
            return False
        return res.json()["success"]
        
    def getBalances(self):
        # Takes a list of currencies and returns a dict like this : {"BTC" : {"available" : .05, "reserved" : 0, "total" : .05}, ...}
        url = self.api_details["API_BASE_URL"] + "account/getbalances?apikey=" + self.api_details["API_KEY"]
        res = self.req(url)
        if not res.ok:
            return None
        r = res.json()
        
        if r["success"]:
            return {x["Currency"] : {"available" : Decimal(x["Available"]), "reserved" : Decimal(x["Pending"]), "total" : Decimal(x["Balance"])} for x in r["result"] if x["Currency"] in self.currencies}
        
        return None

