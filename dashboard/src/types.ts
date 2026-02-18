export interface StatusResponse {
  mode: "dry-run" | "live";
  uptime_seconds: number;
  routes: { direct: number; multi_leg: number; cross: number; total: number };
  exchange_health: Record<string, "connected" | "disconnected">;
}

export interface LiveComparison {
  route_type: "direct" | "multi_leg" | "cross";
  route_label: string;
  spread_pct: number;
  buy_rate: number;
  sell_rate: number;
  buy_exchange: string;
  sell_exchange: string;
  cross_rate: number | null;
  ts: number;
}

export interface WalletsResponse {
  [exchange: string]: {
    [currency: string]: { available: number; reserved: number; total: number };
  };
}

export interface Opportunity {
  id: number;
  ts: string;
  route_type: "direct" | "multi_leg" | "cross";
  route_label: string;
  buy_exchange: string;
  sell_exchange: string;
  spread_pct: number;
  buy_rate: number;
  sell_rate: number;
  cross_rate: number | null;
  qty_a: number;
  qty_b: number;
  executed: boolean;
  dry_run: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface TopPair {
  route_label: string;
  count: number;
}

export interface DirectionStat {
  direction: string;
  count: number;
}

export interface FrequencyPoint {
  hour: string;
  count: number;
}

export interface ReturnProjections {
  avg_spread_pct: number;
  total_trades: number;
  span_days: number;
  daily: number;
  weekly: number;
  monthly: number;
  yearly: number;
}

export interface TradeLeg {
  volume: number;
  rate: number;
  origId: string;
  exchange: string;
  side: string;
}

export interface Trade {
  id: number;
  ts: string;
  market: string;
  legs: TradeLeg[];
}

export interface BalancePoint {
  currency: string;
  balance: number;
  ts: string;
}

export interface ConfigResponse {
  mode: string;
  uptime_seconds: number;
  routes_count: number;
  min_profit?: number;
  keys: Record<string, string>;
}

export interface CurrencyDiscovery {
  available_currencies: string[];
  common_pairs: [string, string][];
  selected_currencies: string[];
}

export interface CurrencyConfig {
  selected: string[];
  roles: Record<string, number>;
  markets: Record<string, { base: string; trade: string }>;
}
