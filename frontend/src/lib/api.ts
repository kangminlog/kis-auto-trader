import { getToken, removeToken } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });
  if (res.status === 401) {
    removeToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export interface PriceInfo {
  code: string;
  current_price: number;
  high: number;
  low: number;
  volume: number;
}

export interface Order {
  id: number;
  stock_code: string;
  side: string;
  order_type: string;
  status: string;
  quantity: number;
  price: number | null;
}

export interface PortfolioItem {
  stock_code: string;
  quantity: number;
  avg_price: number;
}

export interface AutoTradeConfig {
  id: number;
  stock_code: string;
  stock_name: string;
  strategy_name: string;
  is_active: boolean;
  quantity: number;
  max_invest_amount: number;
  stop_loss_price: number | null;
  take_profit_price: number | null;
}

export interface AutoTradeLog {
  id: number;
  config_id: number;
  stock_code: string;
  strategy_name: string;
  signal: string;
  reason: string;
  action_taken: string;
  order_id: number | null;
  created_at: string;
}

export interface SchedulerStatus {
  running: boolean;
}

export interface StrategyInfo {
  name: string;
  description: string;
}
