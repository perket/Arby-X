CREATE TABLE IF NOT EXISTS balances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    currency VARCHAR(10) NOT NULL,
    balance DECIMAL(20, 8) NOT NULL,
    ts TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ts TIMESTAMP NOT NULL,
    market VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS order_details (
    id INT NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    rate DECIMAL(20, 8) NOT NULL,
    origId VARCHAR(100) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    FOREIGN KEY (id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS opportunities (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts          TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    route_type  ENUM('direct', 'multi_leg') NOT NULL,
    route_label VARCHAR(40) NOT NULL,
    buy_exchange  VARCHAR(20) NOT NULL,
    sell_exchange VARCHAR(20) NOT NULL,
    spread_pct  DECIMAL(10, 6) NOT NULL,
    buy_rate    DECIMAL(20, 8) NOT NULL,
    sell_rate   DECIMAL(20, 8) NOT NULL,
    cross_rate  DECIMAL(20, 8) DEFAULT NULL,
    qty_a       DECIMAL(20, 8) NOT NULL,
    qty_b       DECIMAL(20, 8) NOT NULL,
    executed    BOOLEAN NOT NULL DEFAULT FALSE,
    dry_run     BOOLEAN NOT NULL DEFAULT FALSE,
    INDEX idx_ts (ts),
    INDEX idx_route_label (route_label),
    INDEX idx_spread (spread_pct)
);
