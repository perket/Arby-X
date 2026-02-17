import os
import logging
import pymysql

logger = logging.getLogger(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "")


def conn_connect():
    return pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)


def mysql_query(query, params=None):
    response = None
    conn = conn_connect()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        response = cur.fetchall()
    except Exception as e:
        logger.error("DB error executing query: %s | %s", query.split(" ")[:3], e)

    conn.commit()
    conn.close()
    return response


def save_wallets(wallets):
    for curr, balance in wallets.items():
        mysql_query(
            "INSERT INTO balances (currency, balance, ts) VALUES (%s, %s, current_timestamp)",
            (curr, str(balance)),
        )


def save_order(market):
    mysql_query(
        "INSERT INTO orders (ts, market) VALUES (current_timestamp, %s)",
        (market,),
    )
    result = mysql_query("SELECT max(id) FROM orders")
    if result:
        return result[0][0]
    return None


def save_order_data(order_info, order_id):
    exchange = order_info.get("exchange", "")
    side = order_info.get("side", "")
    for order in order_info.get("orderData", []):
        mysql_query(
            "INSERT INTO order_details (id, volume, rate, origId, exchange, side) VALUES (%s, %s, %s, %s, %s, %s)",
            (order_id, str(order["volume"]), str(order["rate"]), order["id"], exchange, side),
        )


def save_opportunity(route_type, route_label, buy_exchange, sell_exchange,
                     spread_pct, buy_rate, sell_rate, cross_rate,
                     qty_a, qty_b, executed, dry_run):
    mysql_query(
        "INSERT INTO opportunities "
        "(route_type, route_label, buy_exchange, sell_exchange, spread_pct, "
        "buy_rate, sell_rate, cross_rate, qty_a, qty_b, executed, dry_run) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (route_type, route_label, buy_exchange, sell_exchange,
         str(spread_pct), str(buy_rate), str(sell_rate),
         str(cross_rate) if cross_rate is not None else None,
         str(qty_a), str(qty_b), executed, dry_run),
    )
