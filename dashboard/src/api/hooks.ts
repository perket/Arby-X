import { useQuery, keepPreviousData } from "@tanstack/react-query";
import api from "./client";
import type {
  StatusResponse,
  LiveComparison,
  WalletsResponse,
  Opportunity,
  PaginatedResponse,
  TopPair,
  DirectionStat,
  FrequencyPoint,
  ReturnProjections,
  Trade,
  BalancePoint,
  ConfigResponse,
  CurrencyDiscovery,
  CurrencyConfig,
} from "../types";

export function useStatus() {
  return useQuery<StatusResponse>({
    queryKey: ["status"],
    queryFn: () => api.get("/api/status").then((r) => r.data),
    refetchInterval: 10_000,
  });
}

export function useLive() {
  return useQuery<Record<string, LiveComparison>>({
    queryKey: ["live"],
    queryFn: () => api.get("/api/live").then((r) => r.data),
    refetchInterval: 3_000,
  });
}

export function useWallets() {
  return useQuery<WalletsResponse>({
    queryKey: ["wallets"],
    queryFn: () => api.get("/api/wallets").then((r) => r.data),
    refetchInterval: 30_000,
  });
}

export function useOrderbooks() {
  return useQuery({
    queryKey: ["orderbooks"],
    queryFn: () => api.get("/api/orderbooks").then((r) => r.data),
    refetchInterval: 10_000,
  });
}

export function useOpportunities(params: {
  page: number;
  per_page?: number;
  route_label?: string;
  min_spread?: number;
  executed?: boolean;
  route_type?: string;
  search?: string;
}) {
  return useQuery<PaginatedResponse<Opportunity>>({
    queryKey: ["opportunities", params],
    queryFn: () => api.get("/api/opportunities", { params }).then((r) => r.data),
    refetchInterval: 15_000,
    placeholderData: keepPreviousData,
  });
}

export function useTopPairs(days: number) {
  return useQuery<TopPair[]>({
    queryKey: ["analytics", "top-pairs", days],
    queryFn: () => api.get("/api/analytics/top-pairs", { params: { days } }).then((r) => r.data),
  });
}

export function useDirection(days: number) {
  return useQuery<DirectionStat[]>({
    queryKey: ["analytics", "direction", days],
    queryFn: () => api.get("/api/analytics/direction", { params: { days } }).then((r) => r.data),
  });
}

export function useFrequency(days: number) {
  return useQuery<FrequencyPoint[]>({
    queryKey: ["analytics", "frequency", days],
    queryFn: () => api.get("/api/analytics/frequency", { params: { days } }).then((r) => r.data),
  });
}

export function useReturns() {
  return useQuery<ReturnProjections>({
    queryKey: ["analytics", "returns"],
    queryFn: () => api.get("/api/analytics/returns").then((r) => r.data),
  });
}

export function useTrades(page: number, per_page = 50) {
  return useQuery<PaginatedResponse<Trade>>({
    queryKey: ["trades", page, per_page],
    queryFn: () => api.get("/api/trades", { params: { page, per_page } }).then((r) => r.data),
    placeholderData: keepPreviousData,
  });
}

export function useBalances(days: number) {
  return useQuery<BalancePoint[]>({
    queryKey: ["balances", days],
    queryFn: () => api.get("/api/balances", { params: { days } }).then((r) => r.data),
  });
}

export function useConfig() {
  return useQuery<ConfigResponse>({
    queryKey: ["config"],
    queryFn: () => api.get("/api/config").then((r) => r.data),
  });
}

export function useCurrencyDiscovery(enabled: boolean) {
  return useQuery<CurrencyDiscovery>({
    queryKey: ["currencies", "discover"],
    queryFn: () => api.get("/api/currencies/discover").then((r) => r.data),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCurrencyConfig() {
  return useQuery<CurrencyConfig>({
    queryKey: ["currencies", "config"],
    queryFn: () => api.get("/api/currencies").then((r) => r.data),
  });
}
