# Arby-X

Automated cryptocurrency arbitrage bot that monitors order books on **Binance** and **Kraken**, detects price discrepancies, and executes simultaneous buy/sell trades when the spread exceeds a configurable threshold.

## How it works

```
Binance WebSocket ──┐
                    ├──▶ Comparison Engine ──▶ Trade Execution ──▶ MySQL
Kraken WebSocket  ──┘       (every 0.1s)       (simultaneous)
```

Five threads run concurrently:

1. **Binance order book** — streams depth data via WebSocket
2. **Kraken order book** — streams depth data via WebSocket (`wss://ws.kraken.com/v2`)
3. **Comparison engine** — scans all configured pairs for arbitrage above `MIN_ARB` (default 0.5%)
4. **Trade thread 1** — executes the SELL leg
5. **Trade thread 2** — executes the BUY leg

When an opportunity is found, both legs execute simultaneously. Results are persisted to MySQL and a PHP dashboard visualizes balance history.

## Quick start

### Docker (recommended)

```bash
cp .env.example .env    # fill in your API keys
docker compose up -d
```

This starts three containers:

| Service     | Description                        | Port |
|-------------|------------------------------------|------|
| `bot`       | The arbitrage bot                  | —    |
| `db`        | MySQL 8.0 (schema auto-created)   | 3306 |
| `dashboard` | PHP dashboard with balance charts  | 8080 |

### Manual

```bash
pip install -r requirements.txt
cp .env.example .env    # fill in API keys and DB credentials
python3 arby.py
```

Requires a running MySQL instance with the schema from `init.sql`.

## Configuration

All credentials are loaded from environment variables (`.env` file):

```
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_API_BASE_URL=https://api.binance.com

KRAKEN_API_KEY=
KRAKEN_API_SECRET=

DB_HOST=db
DB_PORT=3306
DB_USER=arbyx
DB_PASSWORD=arbyx
DB_NAME=arbyx
DB_ROOT_PASSWORD=rootpassword
```

Trading parameters are set at the top of `arby.py`:

| Parameter              | Default | Description                                    |
|------------------------|---------|------------------------------------------------|
| `MIN_ARB`              | 0.5%    | Minimum arbitrage spread to trigger a trade     |
| `MAX_TIME_SINCE_UPDATE`| 5s      | Max order book staleness before skipping a pair |
| `currencies`           | ETH, BTC, XLM, XRP, ADA | Tracked currencies and their roles |

## Project structure

```
arby.py                 Entry point and orchestrator
bnnc.py                 Binance REST API wrapper
krkn.py                 Kraken REST API wrapper
binanceOrderBook.py     Binance WebSocket order book
krakenOrderBook.py      Kraken WebSocket order book
saveToDb.py             MySQL persistence layer
init.sql                Database schema
web/
  config.php            Shared DB connection
  index.php             Dashboard (Plotly.js charts)
  balances/index.php    Balance history JSON endpoint
  tradeData/index.php   Trade data JSON endpoint
```

## Requirements

- Python 3.10+
- MySQL 8.0+
- Binance and Kraken API keys with trading permissions

## License

This project is provided as-is for educational purposes.
