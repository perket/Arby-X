# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Arby-X is an automated cryptocurrency arbitrage trading bot written in Python 3. It monitors order books on Binance and Kraken exchanges, detects arbitrage opportunities, and executes trades automatically when profitable spreads exceed a configurable threshold.

## Running the Application

### With Docker (recommended)

```bash
cp .env.example .env  # then fill in API keys
docker compose up -d
```

This starts three services:
- **bot** — the arbitrage bot (`arby.py`)
- **db** — MySQL 8.0 with schema auto-initialized from `init.sql`
- **dashboard** — PHP 8.2 + Apache serving the web UI on port 8080

The bot container waits for MySQL to be healthy before starting. Data is persisted in a Docker volume (`db_data`).

### Without Docker

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in API keys and DB credentials, set DB_HOST=localhost
python3 arby.py
```

Dependencies (pinned in `requirements.txt`): `python-binance`, `requests`, `pymysql`, `websocket-client`, `python-dotenv`.

## Testing

No formal test framework is in place. Quick smoke test for imports:

```bash
python -c "from krkn import KRAKEN; from krakenOrderBook import KRAKEN_ORDER_BOOK; from binanceOrderBook import BINANCE_ORDER_BOOK; from bnnc import BINANCE; print('OK')"
```

## Architecture

The system uses a multi-threaded, event-driven architecture with 5 concurrent threads coordinated via `threading.Event()` flags and `threading.Lock()` for shared state:

1. **BINANCE_ORDER_BOOK** (`binanceOrderBook.py`) — Collects Binance order book data via WebSocket using `ThreadedWebsocketManager` from `python-binance`. Resets periodically every 108,000 seconds.
2. **KRAKEN_ORDER_BOOK** (`krakenOrderBook.py`) — Collects Kraken order book data via WebSocket (`wss://ws.kraken.com/v2`), subscribes to `book` channel with depth 10. Reconnects with exponential backoff.
3. **MAIN2** (`arby.py`) — Comparison engine that runs every 0.1s, detecting arbitrage opportunities exceeding `MIN_ARB` (0.5%).
4. **TRADE thread 1** (`arby.py`) — Executes SELL leg of arbitrage trades.
5. **TRADE thread 2** (`arby.py`) — Executes BUY leg of arbitrage trades.

### Key modules

- **arby.py** — Entry point and orchestrator. Contains `TRADE` and `MAIN2` classes, thread initialization, arbitrage calculation (`calc_rates`, `calc_r`, `calc_volumes`), and wallet management. Uses `if __name__ == "__main__":` guard. All threads are daemon threads.
- **bnnc.py** — Binance API wrapper (`BINANCE` class). HMAC-SHA256 auth, order placement, balance queries, market info/filters. Uses `/api/v3/` endpoints.
- **krkn.py** — Kraken API wrapper (`KRAKEN` class). HMAC-SHA512 auth, order placement, balance queries. Handles BTC↔XBT symbol mapping. Rate-limited (~1s between private calls).
- **saveToDb.py** — MySQL persistence layer using PyMySQL with parameterized queries. DB credentials loaded from environment variables.
- **web/** — PHP dashboard with Plotly.js charts. `web/config.php` provides shared PDO connection. `web/index.php` renders balance history (last 7 days, computed dynamically). `web/balances/` and `web/tradeData/` serve JSON data endpoints.

### Thread safety

- `order_book_lock` — Protects `order_books` dict (order book threads write, MAIN2 reads)
- `wallets_lock` — Protects `wallets` dict
- `data_lock` — Protects shared `data` list between MAIN2 and TRADE threads

### Data flow

Order book threads continuously update a shared `order_books` dict → MAIN2 compares rates across exchanges → if arbitrage exceeds threshold, TRADE threads execute sell/buy orders simultaneously → results persisted to MySQL → wallets refreshed.

### Important conventions

- All financial arithmetic uses `decimal.Decimal` with `quantize()` for proper rounding (ROUND_DOWN, ROUND_UP, ROUND_HALF_UP).
- All credentials (API keys, DB) are loaded from environment variables via `python-dotenv` (`.env` file).
- Configuration constants (`MIN_ARB`, `MIN_VOLUME_DIFF`, `MAX_TIME_SINCE_UPDATE`, `currencies` dict) are defined at the top of `arby.py`.
- Logging is used throughout instead of print statements.
