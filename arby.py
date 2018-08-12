from bnnc import BINANCE
from bttrx import BITTREX
from binanceOrderBook import *
from bittrexOrderBook import *
from bittrexV2OrderBook import *
from decimal import Decimal
from saveToDb import *

## This you may change
# 0 - Only base, 1 - Booth base and trade, 2 - Trade only (all bases), 3 - Trade only (BTC exclusiv)
currencies = {"ETH" : 2, "BTC" : 0, "XLM" : 2, "XRP" : 2, "ADA" : 2, "NEO" : 2, "XVG" : 2, "BCC" : 2}
min_volume = Decimal(.05 * 2)

MIN_ARB = .005
MIN_VOLUME_DIFF = Decimal(2) # Minimum ratio over min order value
MIN_VOLUME_MARGIN = Decimal(2) # Minimum ratio over 
MAX_TIME_SINCE_UPDATE = Decimal(.1)

## This you should not touch
markets = {trade+base : {"base" : base, "trade" : trade} for trade, x in currencies.items() for base, v in currencies.items() if (v < 2 and 0 < x < 3 and base != trade) or (x == 3 and v == 0)}

## API details
binance_api_details = {
"API_KEY" : "BINANCE_API_KEY",
"API_SECRET" : "BINANCE_API_SECRET",
"API_BASE_URL" : "BINANCE_API_BASE_URL",
"API_PASSPHRASE" :"BINANCE_API_PASSPHRASE"}
bittrex_api_details = {
"API_KEY" : "BITTREX_API_KEY",
"API_SECRET" : "BITTREX_API_SECRET",
"API_BASE_URL" : "BITTREX_API_BASE_URL",
"API_PASSPHRASE" : "BITTREX_API_PASSPHRASE"}

exchanges = {"binance" : BINANCE(binance_api_details, currencies), "bittrex" : BITTREX(bittrex_api_details, currencies)}
order_books = {exchange : {market : {"sell" : None, "buy" : None, "lastUpdate" : None} for market, _ in markets.items()} for exchange, _ in exchanges.items()} 
wallets = {exchange : o.getBalances() for exchange, o in exchanges.items()}  
market_info = {exchange : o.getMarketInfo(markets) for exchange, o in exchanges.items()}


def rndDown(x, n):
    return Decimal(int(x * 10 ** n)/10 ** n)

def rndUp(x, n):
    return Decimal(int(x * 10 ** n + 1)/10 ** n)

def rnd(x, n):
    return int(x * 10 ** n + Decimal(.5))/10 ** n

class TRADE(threading.Thread):
    def __init__(self, threadId, name, tradeNum, tradeData, e, exchange):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.tradeNum = tradeNum
        self.tradeData = tradeData
        self.e = e
        self.exchanges = exchanges
        self.order_value = 0
        
    def run(self):
        while True:
            self.trade()

    def update_rate_and_volume(self, td, order_data):
        # TODO Fix this, borde ta bästa erbjudandet från orderboken.
        self.order_value -= Decimal(td["rate"]) * (Decimal(order_data["quantity"]) - Decimal(order_data["quantityRemaining"]))
        change = max(td["rate"] * Decimal(.001), Decimal(10 ** -market_info[td["exchange"]][td["market"]]["ratePrecision"]))
        td["rate"] += (-1 if td["side"] == "SELL" else 1) * change
        
        #td["rate"] =  
        if td["side"] == "BUY":
            td["volume"] = rndDown(self.order_value / td["rate"], market_info[td["exchange"]][td["market"]]["volumePrecision"])
        else:
            td["volume"] = rndDown(Decimal(order_data["quantityRemaining"]), market_info[td["exchange"]][td["market"]]["volumePrecision"])
        return td

    def trade(self):
        self.e[0].wait()
        
        td = self.tradeData[self.tradeNum - 1]
        self.order_value = td["rate"] * td["volume"]
        exchange = self.exchanges[td["exchange"]]
        remainingQty = td["volume"]
        
        while td["volume"] * td["rate"] > td["minOrderValue"]:
            print("%s %s %s %.8f %.8f %s" % (td["exchange"], markets[td["market"]]["trade"], markets[td["market"]]["base"], td["rate"], td["volume"], td["side"]))
            order_id = exchange.order(markets[td["market"]]["trade"], markets[td["market"]]["base"], rnd(td["rate"],market_info[td["exchange"]][td["market"]]["ratePrecision"]), rnd(td["volume"],market_info[td["exchange"]][td["market"]]["volumePrecision"]), td["side"])
            if order_id:
                sleep(1)
                exchange.closeOrder(order_id, markets[td["market"]]["trade"], markets[td["market"]]["base"])
                order_data = exchange.getOrderData(order_id, markets[td["market"]]["trade"], markets[td["market"]]["base"])
                td["orderData"].append({"id" : order_id, "rate" : order_data["price"], "volume" : Decimal(order_data["quantity"]) - Decimal(order_data["quantityRemaining"])})
                
                td = self.update_rate_and_volume(td, order_data)
                
        self.e[self.tradeNum].set()
        self.e[0].clear()

class MAIN2(threading.Thread):
    def __init__(self, threadId, name, eventFlags, data):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.eventFlags = eventFlags
        self.data = data
        self.highest_arb = Decimal(.0)
        self.arb_counter = [0, 0, 0, 0] #.4, .5, .6, 1.

    def run(self):
        while True:
            self.compare()
            sleep(.1)

    def compare(self):
        for market in markets:
            info = [{"info" : self.get_market_info(A,B,market), "A" : A, "B" : B, "market" : market, "makeTrade" : False} for B, _ in exchanges.items() for A, _ in exchanges.items() if A != B]
            best = max(info, key=lambda x:x["info"]["arbitrage"]) 
            bold = "\033[1m" if best["info"]["arbitrage"] > 0 else "\033[0m"
            #print('\033[1m' + 'Hello' + '\033[0m')
            ac = ", ".join([str(x) for x in self.arb_counter])
            print("{m:<8} - {b}{arb:>10.5f}\033[0m % {A:>15.8f} {curr} {B:>15.8f} {curr} {s:>15.8} % {cnt}\r".format(b = bold, m = market, curr = markets[market]["base"], s = self.highest_arb * 100, cnt = ac, arb = best["info"]["arbitrage"] * 100, **best["info"]), end="")
            if best["info"]["arbitrage"] >= MIN_ARB:
                #print()
                best = self.calc_rates(best)
                best = self.calc_r(best)
                best = self.calc_volumes(best)
                if best["makeTrade"]:
                    print()
                    self.trade(best)
                    print()
                    print("{m:<8} | buy : {info[A]:<10.8f} BTC, sell : {info[B]:<10.8f} BTC, r : {info[r]:<10.8f}".format(m = market, **best))
                    self.update_wallets()
                    self.save_trade(best["market"])
                    # save trade details
                    self.data[0] = {}
                    self.data[1] = {}
                if best["info"]["arbitrage"] > self.highest_arb:
                    self.highest_arb = best["info"]["arbitrage"]
            self.arb_counter[0] += (1 if best["info"]["arbitrage"] > Decimal(.004) else 0)
            self.arb_counter[1] += (1 if best["info"]["arbitrage"] > Decimal(.005) else 0)
            self.arb_counter[2] += (1 if best["info"]["arbitrage"] > Decimal(.0075) else 0)
            self.arb_counter[3] += (1 if best["info"]["arbitrage"] > Decimal(.01) else 0)
            sleep(.1)

    def save_trade(self, market):
        order_id = save_order(market)
        save_order_data(self.data[0], order_id)#, exchanges[], "SELL")
        save_order_data(self.data[1], order_id)#, exchanges[], "BUY")

    def get_market_info(self, A, B, market):
        buy = order_books[A][market]["buy"]
        sell = order_books[B][market]["sell"]
        lastUpdates = [order_books[A][market]["lastUpdate"], order_books[B][market]["lastUpdate"]]
        if bool(buy) and bool(sell):
            buy_rate = buy[1][0]
            sell_rate = sell[1][0]
            t0 = time()
            return {"arbitrage" : buy_rate / sell_rate - 1, "A" : buy_rate, "B" : sell_rate, "buyQty" : Decimal(.0), "sellQty" : Decimal(.0), "r" : Decimal(.0), "minOrderValueA" : Decimal(.0), "minOrderValueB" : Decimal(.0)}
        return {"arbitrage" : Decimal(.0), "A" : Decimal(.0), "B" : Decimal(.0), "qtyA" : Decimal(.0), "qtyB" : Decimal(.0), "r" : Decimal(.0), "minOrderValueA" : Decimal(.0), "minOrderValueB" : Decimal(.0)}

    def calc_rates(self, info):
        br = info["info"]["A"]
        sr = info["info"]["B"]
        buy_rate = info["info"]["A"] / (1 + market_info[info["A"]][info["market"]]["tradeFees"])
        sell_rate = info["info"]["B"] * (1 + market_info[info["B"]][info["market"]]["tradeFees"])
        diff = buy_rate - sell_rate
                
        info["info"]["A"] = rndUp((buy_rate - diff / 3) * (1 + market_info[info["A"]][info["market"]]["tradeFees"]), market_info[info["A"]][info["market"]]["ratePrecision"])
        info["info"]["B"] = rndDown((sell_rate + diff / 3) / (1 + market_info[info["B"]][info["market"]]["tradeFees"]), market_info[info["B"]][info["market"]]["ratePrecision"])
        
        return info

    def calc_r(self, info):
        buy_rate = info["info"]["A"]  / (1 + market_info[info["A"]][info["market"]]["tradeFees"]) 
        sell_rate = info["info"]["B"] * (1 + market_info[info["B"]][info["market"]]["tradeFees"])
        info["info"]["r"] = sell_rate / buy_rate # MAXIMIZE TRADE CURRENCY
        #info["info"]["r"] = 2 * sell_rate / (buy_rate + sell_rate) # MAXIMIZE BOTH CURRENCIES
        return info
    
    def get_min_order_value(self, exchange, info):
        movBTC = market_info[exchange][info["market"]]["minOrderValueBTC"]
        movETH = market_info[exchange][info["market"]]["minOrderValueETH"]
        if markets[info["market"]]["base"] == "BTC":
            return movBTC
        elif markets[info["market"]]["base"] == "ETH":
            if movETH:
                return movETH
            else:
                if bool(order_books[exchange]["ETHBTC"]["buy"]):
                    return movBTC / Decimal(order_books[exchange]["ETHBTC"]["buy"][0][0])
        return Decimal(1e99)

    def calc_volumes(self, info):
        # Get wallet value
        wallet_buy = wallets[info["A"]][markets[info["market"]]["trade"]]["available"] * info["info"]["B"]
        wallet_sell = wallets[info["B"]][markets[info["market"]]["base"]]["available"]
        
        # Get min order values from api
        info["info"]["minOrderValueA"] = self.get_min_order_value(info["A"],info)
        info["info"]["minOrderValueB"] = self.get_min_order_value(info["B"],info)
        
        # Get available order values from order books
        obv_buy = self.get_order_book_value(info["info"]["A"], "buy", info["A"], info["market"]) / 3
        obv_sell = self.get_order_book_value(info["info"]["B"], "sell", info["B"], info["market"]) / 3
        
        if min(obv_buy, obv_sell, wallet_buy, wallet_sell) > max(info["info"]["minOrderValueA"], info["info"]["minOrderValueB"]) * Decimal(1.25):
            order_size = min(obv_buy, obv_sell, wallet_buy, wallet_sell)
            precision_A = market_info[info["A"]][info["market"]]["volumePrecision"]
            precision_B = market_info[info["B"]][info["market"]]["volumePrecision"]
            if precision_A < precision_B:
                info["info"]["qtyA"] = rndDown(info["info"]["r"] * order_size / (info["info"]["B"] * (1 + market_info[info["B"]][info["market"]]["tradeFees"])), precision_A)
                info["info"]["qtyB"] = rndDown(info["info"]["qtyA"] / info["info"]["r"], precision_B)

            else:
                info["info"]["qtyB"] = rndDown(order_size / (info["info"]["B"] * (1 + market_info[info["B"]][info["market"]]["tradeFees"])), precision_B)
                info["info"]["qtyA"] = rndDown(info["info"]["r"] * info["info"]["qtyB"], precision_A)
            info["makeTrade"] = True
        return info

    def get_order_book_value(self, rate, mode, exchange, market):
        volume = 0
        i = 0
        ob = order_books[exchange][market][mode]
        while bool(ob) and i < len(ob) and ((mode == "buy" and ob[i][0] >= rate) or (mode == "sell" and ob[i][0] <= rate)):
            volume += ob[i][1]
            i += 1
        return volume * rate

    def trade(self, info):
        # make trade data
        self.data[0] = {"side" : "SELL", "exchange" : info["A"], "rate" : info["info"]["A"], "volume" : info["info"]["qtyA"], "market" : info["market"], "minOrderValue" : info["info"]["minOrderValueA"], "orderData" : []}
        self.data[1] = {"side" : "BUY", "exchange" : info["B"], "rate" : info["info"]["B"], "volume" : info["info"]["qtyB"], "market" : info["market"], "minOrderValue" : info["info"]["minOrderValueB"], "orderData" : []}
        self.eventFlags[0].set()
        self.eventFlags[1].wait()
        self.eventFlags[2].wait()
        
        #TODO save order details

        self.eventFlags[1].clear()
        self.eventFlags[2].clear()
        
    def update_wallets(self):
        sleep(5)
        for e, o in exchanges.items():
            funds = None
            while funds is None:
                funds = o.getBalances()
            wallets[e] = funds
        print_wallets()
        

def print_wallets():
    sums = {curr : 0 for curr in currencies}
    for _, w in wallets.items():
        for c, b in w.items():
            sums[c] += b["total"]

    print("%s" % ", ".join(["%.8f %s" % (b, c) for c, b in sorted(sums.items())]))
    save_wallets(sums)


e = [threading.Event(), threading.Event(), threading.Event()]
data = [{},{}]
## Start threads collecting order book data
binance_ob = BINANCE_ORDER_BOOK(1, "BINANCE ORDER BOOK", order_books["binance"], binance_api_details)
bittrex_ob = BITTREX_ORDER_BOOK(2, "BITTREX ORDER BOOK", order_books["bittrex"])
main = MAIN2(3, "MAIN LOOP", e, data)
trade1 = TRADE(4, "TRADE 1", 1, data, e, exchanges)
trade2 = TRADE(5, "TRADE 2", 2, data, e, exchanges)
binance_ob.start()
bittrex_ob.start()
main.start()
trade1.start()
trade2.start()
#print(wallets)
#print_wallets()
