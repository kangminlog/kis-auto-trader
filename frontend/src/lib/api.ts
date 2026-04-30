const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
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
