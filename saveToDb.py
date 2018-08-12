import pymysql

hst = 'HOST' 
prt = 3306
usr = 'USER' 
pwd = 'PASSWORD'
dbe = 'DATABASE'

def connConnect():
    return pymysql.connect(host=hst,port=prt,user=usr,passwd=pwd,db=dbe)

def mysql_query(*args):
    q = args[0]
    debug = True if len(args) < 2 else args[1]
    response = None
    conn = connConnect()
    cur = conn.cursor()
    try:
        cur.execute(q)
        response = cur.fetchall()
        q_response_text = "Successfully executed: "+" ".join(q.split(" ")[:3])
    except:
        q_response_text = "Error while executing: "+" ".join(q.split(" ")[:3]) 
        
    if debug:
        print(q_response_text)

    conn.commit()
    conn.close()
    return response

def save_wallets(wallets):
    for curr, balance in wallets.items():
        #print("insert into balances (currency, balance, ts) values ('{}',{},current_timestamp);".format(curr, balance))
        mysql_query("insert into balances (currency, balance, ts) values ('{}',{},current_timestamp);".format(curr, balance))
    
def save_order(market):
    mysql_query("insert into orders (ts,market) values (current_timestamp,'{}');".format(market))
    order_id = mysql_query("select max(id) from orders;")[0][0]
    return order_id

def save_order_data(order_info, order_id):
    # "id" : order_id, "rate" : order_data["price"], "volume" : Decimal(order_data["quantity"]) - Decimal(order_data["quantityRemaining"])
    exchange = order_info["exchange"]
    side = order_info["side"]
    for order in order_info["orderData"]:
        mysql_query("insert into order_details (id, volume, rate, origId, exchange, side) values ({oid}, {volume}, {rate}, '{id}', '{e}', '{s}');".format(oid = order_id, s = side, e = exchange, **order))
