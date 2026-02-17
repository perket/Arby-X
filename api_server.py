import os
import logging
import threading
from time import time
from decimal import Decimal

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn

from saveToDb import mysql_query

logger = logging.getLogger(__name__)

app = FastAPI(title="Arby-X API", version="1.0.0")

# References to shared state — set by init_api_state()
_state = {}


def _decimal_to_float(obj):
    """Recursively convert Decimal values to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_decimal_to_float(i) for i in obj]
    return obj


def init_api_state(*, order_books, wallets, market_info, routes, exchanges,
                   order_book_lock, wallets_lock, comparisons_lock,
                   latest_comparisons, dry_run, bot_start_time, currencies):
    _state.update({
        "order_books": order_books,
        "wallets": wallets,
        "market_info": market_info,
        "routes": routes,
        "exchanges": exchanges,
        "order_book_lock": order_book_lock,
        "wallets_lock": wallets_lock,
        "comparisons_lock": comparisons_lock,
        "latest_comparisons": latest_comparisons,
        "dry_run": dry_run,
        "bot_start_time": bot_start_time,
        "currencies": currencies,
    })


def start_api_server(port=8000):
    def _run():
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
    t = threading.Thread(target=_run, daemon=True, name="API_SERVER")
    t.start()
    logger.info("API server started on port %d", port)
    return t


# ---------- Endpoints ----------

@app.get("/api/status")
def get_status():
    uptime = time() - _state.get("bot_start_time", time())
    routes = _state.get("routes", [])
    direct = sum(1 for r in routes if r["type"] == "direct")
    multi_leg = sum(1 for r in routes if r["type"] == "multi_leg")

    exchange_health = {}
    with _state["order_book_lock"]:
        for ex_name in _state["exchanges"]:
            books = _state["order_books"].get(ex_name, {})
            has_data = any(
                b.get("lastUpdate") is not None and (time() - b["lastUpdate"]) < 30
                for b in books.values()
            )
            exchange_health[ex_name] = "connected" if has_data else "disconnected"

    return {
        "mode": "dry-run" if _state.get("dry_run") else "live",
        "uptime_seconds": round(uptime, 1),
        "routes": {"direct": direct, "multi_leg": multi_leg, "total": len(routes)},
        "exchange_health": exchange_health,
    }


@app.get("/api/live")
def get_live():
    with _state["comparisons_lock"]:
        data = dict(_state["latest_comparisons"])
    return _decimal_to_float(data)


@app.get("/api/wallets")
def get_wallets():
    with _state["wallets_lock"]:
        data = {
            ex: {
                curr: {k: float(v) for k, v in balances.items()}
                for curr, balances in funds.items()
            }
            for ex, funds in _state["wallets"].items()
        }
    return data


@app.get("/api/orderbooks")
def get_orderbooks():
    result = {}
    with _state["order_book_lock"]:
        for ex_name, markets in _state["order_books"].items():
            result[ex_name] = {}
            for market, book in markets.items():
                result[ex_name][market] = {
                    "buy": [[float(p), float(q)] for p, q in (book["buy"] or [])[:5]],
                    "sell": [[float(p), float(q)] for p, q in (book["sell"] or [])[:5]],
                    "lastUpdate": book["lastUpdate"],
                }
    return result


@app.get("/api/opportunities")
def get_opportunities(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    route_label: str = Query(None),
    min_spread: float = Query(None),
    executed: bool = Query(None),
    route_type: str = Query(None),
    search: str = Query(None),
):
    conditions = []
    params = []

    if route_label:
        conditions.append("route_label = %s")
        params.append(route_label)
    if min_spread is not None:
        conditions.append("spread_pct >= %s")
        params.append(str(min_spread))
    if executed is not None:
        conditions.append("executed = %s")
        params.append(executed)
    if route_type:
        conditions.append("route_type = %s")
        params.append(route_type)
    if search:
        conditions.append("(route_label LIKE %s OR buy_exchange LIKE %s OR sell_exchange LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like])

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * per_page

    count_result = mysql_query(f"SELECT COUNT(*) FROM opportunities{where}", params)
    total = count_result[0][0] if count_result else 0

    rows = mysql_query(
        f"SELECT id, ts, route_type, route_label, buy_exchange, sell_exchange, "
        f"spread_pct, buy_rate, sell_rate, cross_rate, qty_a, qty_b, executed, dry_run "
        f"FROM opportunities{where} ORDER BY ts DESC LIMIT %s OFFSET %s",
        params + [per_page, offset],
    )

    items = []
    for r in (rows or []):
        items.append({
            "id": r[0], "ts": str(r[1]), "route_type": r[2], "route_label": r[3],
            "buy_exchange": r[4], "sell_exchange": r[5],
            "spread_pct": float(r[6]), "buy_rate": float(r[7]), "sell_rate": float(r[8]),
            "cross_rate": float(r[9]) if r[9] is not None else None,
            "qty_a": float(r[10]), "qty_b": float(r[11]),
            "executed": bool(r[12]), "dry_run": bool(r[13]),
        })

    return {"items": items, "total": total, "page": page, "per_page": per_page}


@app.get("/api/analytics/top-pairs")
def analytics_top_pairs(days: int = Query(7, ge=1, le=365)):
    rows = mysql_query(
        "SELECT route_label, COUNT(*) as cnt FROM opportunities "
        "WHERE ts >= DATE_SUB(NOW(), INTERVAL %s DAY) "
        "GROUP BY route_label ORDER BY cnt DESC LIMIT 20",
        (days,),
    )
    return [{"route_label": r[0], "count": r[1]} for r in (rows or [])]


@app.get("/api/analytics/direction")
def analytics_direction(days: int = Query(7, ge=1, le=365)):
    rows = mysql_query(
        "SELECT CONCAT(buy_exchange, ' → ', sell_exchange) as direction, COUNT(*) as cnt "
        "FROM opportunities WHERE ts >= DATE_SUB(NOW(), INTERVAL %s DAY) "
        "GROUP BY direction ORDER BY cnt DESC",
        (days,),
    )
    return [{"direction": r[0], "count": r[1]} for r in (rows or [])]


@app.get("/api/analytics/frequency")
def analytics_frequency(days: int = Query(7, ge=1, le=365)):
    rows = mysql_query(
        "SELECT DATE_FORMAT(ts, '%%Y-%%m-%%d %%H:00:00') as hour, COUNT(*) as cnt "
        "FROM opportunities WHERE ts >= DATE_SUB(NOW(), INTERVAL %s DAY) "
        "GROUP BY hour ORDER BY hour",
        (days,),
    )
    return [{"hour": r[0], "count": r[1]} for r in (rows or [])]


@app.get("/api/analytics/returns")
def analytics_returns():
    row = mysql_query(
        "SELECT AVG(spread_pct), COUNT(*), "
        "MIN(ts), MAX(ts) FROM opportunities WHERE executed = TRUE"
    )
    if not row or not row[0][0]:
        return {"avg_spread_pct": 0, "total_trades": 0,
                "daily": 0, "weekly": 0, "monthly": 0, "yearly": 0}

    avg_spread = float(row[0][0])
    total = row[0][1]
    min_ts = row[0][2]
    max_ts = row[0][3]

    if min_ts and max_ts and min_ts != max_ts:
        span_days = max((max_ts - min_ts).total_seconds() / 86400, 1)
        daily_trades = total / span_days
    else:
        daily_trades = total
        span_days = 1

    daily_return = daily_trades * avg_spread / 100
    return {
        "avg_spread_pct": round(avg_spread, 4),
        "total_trades": total,
        "span_days": round(span_days, 1),
        "daily": round(daily_return, 6),
        "weekly": round(daily_return * 7, 6),
        "monthly": round(daily_return * 30, 6),
        "yearly": round(daily_return * 365, 6),
    }


@app.get("/api/trades")
def get_trades(page: int = Query(1, ge=1), per_page: int = Query(50, ge=1, le=200)):
    offset = (page - 1) * per_page
    count_result = mysql_query("SELECT COUNT(*) FROM orders")
    total = count_result[0][0] if count_result else 0

    rows = mysql_query(
        "SELECT o.id, o.ts, o.market, "
        "d.volume, d.rate, d.origId, d.exchange, d.side "
        "FROM orders o LEFT JOIN order_details d ON o.id = d.id "
        "ORDER BY o.ts DESC LIMIT %s OFFSET %s",
        (per_page * 4, offset * 4),
    )

    trades = {}
    for r in (rows or []):
        oid = r[0]
        if oid not in trades:
            trades[oid] = {"id": oid, "ts": str(r[1]), "market": r[2], "legs": []}
        if r[3] is not None:
            trades[oid]["legs"].append({
                "volume": float(r[3]), "rate": float(r[4]),
                "origId": r[5], "exchange": r[6], "side": r[7],
            })

    items = list(trades.values())[:per_page]
    return {"items": items, "total": total, "page": page, "per_page": per_page}


@app.get("/api/balances")
def get_balances(days: int = Query(7, ge=1, le=365)):
    rows = mysql_query(
        "SELECT currency, balance, ts FROM balances "
        "WHERE ts >= DATE_SUB(NOW(), INTERVAL %s DAY) ORDER BY ts",
        (days,),
    )
    result = []
    for r in (rows or []):
        result.append({"currency": r[0], "balance": float(r[1]), "ts": str(r[2])})
    return result


@app.get("/api/config")
def get_config():
    def mask(key):
        val = os.environ.get(key, "")
        if len(val) <= 8:
            return "****" if val else ""
        return val[:4] + "****" + val[-4:]

    return {
        "mode": "dry-run" if _state.get("dry_run") else "live",
        "uptime_seconds": round(time() - _state.get("bot_start_time", time()), 1),
        "routes_count": len(_state.get("routes", [])),
        "keys": {
            "BINANCE_API_KEY": mask("BINANCE_API_KEY"),
            "BINANCE_API_SECRET": mask("BINANCE_API_SECRET"),
            "KRAKEN_API_KEY": mask("KRAKEN_API_KEY"),
            "KRAKEN_API_SECRET": mask("KRAKEN_API_SECRET"),
        },
    }


@app.put("/api/config")
def update_config(body: dict):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    allowed_keys = {"BINANCE_API_KEY", "BINANCE_API_SECRET", "KRAKEN_API_KEY", "KRAKEN_API_SECRET"}
    updates = {k: v for k, v in body.items() if k in allowed_keys and v}

    if not updates:
        return JSONResponse({"error": "No valid keys provided"}, status_code=400)

    # Read existing .env
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    # Update or append
    updated_keys = set()
    new_lines = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}\n")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)

    return {"updated": list(updates.keys()), "message": "Restart required for changes to take effect"}
