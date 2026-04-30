"use client";

import { useState } from "react";
import { fetchApi, type Order, type PriceInfo } from "@/lib/api";

const PRESET_STOCKS = [
  { code: "005930", name: "삼성전자" },
  { code: "000660", name: "SK하이닉스" },
  { code: "035420", name: "NAVER" },
  { code: "051910", name: "LG화학" },
  { code: "006400", name: "삼성SDI" },
];

export default function MarketPage() {
  const [code, setCode] = useState("");
  const [price, setPrice] = useState<PriceInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [orderSide, setOrderSide] = useState<"buy" | "sell">("buy");
  const [orderType, setOrderType] = useState<"market" | "limit">("market");
  const [orderQty, setOrderQty] = useState("1");
  const [orderPrice, setOrderPrice] = useState("");
  const [orderMsg, setOrderMsg] = useState("");

  async function handleSearch(stockCode: string) {
    setLoading(true);
    setError("");
    try {
      const data = await fetchApi<PriceInfo>(`/api/price/${stockCode}`);
      setPrice(data);
      setCode(stockCode);
    } catch {
      setError("시세 조회에 실패했습니다.");
      setPrice(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">시세 조회</h1>

      {/* 종목 검색 */}
      <div className="flex gap-2">
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="종목 코드 (예: 005930)"
          className="rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
        />
        <button
          onClick={() => handleSearch(code)}
          disabled={!code || loading}
          className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "조회 중..." : "조회"}
        </button>
      </div>

      {/* 프리셋 종목 */}
      <div className="flex flex-wrap gap-2">
        {PRESET_STOCKS.map((stock) => (
          <button
            key={stock.code}
            onClick={() => handleSearch(stock.code)}
            className="rounded-lg border border-gray-700 px-3 py-1.5 text-sm text-gray-300 hover:border-blue-500 hover:text-white transition-colors"
          >
            {stock.name}
          </button>
        ))}
      </div>

      {error && <p className="text-red-400">{error}</p>}

      {/* 시세 결과 */}
      {price && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-lg font-semibold">{price.code}</h2>
          <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
            <div>
              <p className="text-sm text-gray-400">현재가</p>
              <p className="text-xl font-bold">
                {price.current_price.toLocaleString()}원
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">고가</p>
              <p className="text-xl font-bold text-red-400">
                {price.high.toLocaleString()}원
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">저가</p>
              <p className="text-xl font-bold text-blue-400">
                {price.low.toLocaleString()}원
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">거래량</p>
              <p className="text-xl font-bold">
                {price.volume.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}
      {/* 주문 생성 */}
      {price && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-lg font-semibold mb-4">주문</h2>
          <div className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="block text-xs text-gray-400 mb-1">매매</label>
              <select
                value={orderSide}
                onChange={(e) => setOrderSide(e.target.value as "buy" | "sell")}
                className="rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
              >
                <option value="buy">매수</option>
                <option value="sell">매도</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">유형</label>
              <select
                value={orderType}
                onChange={(e) => setOrderType(e.target.value as "market" | "limit")}
                className="rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
              >
                <option value="market">시장가</option>
                <option value="limit">지정가</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">수량</label>
              <input
                type="number"
                min="1"
                value={orderQty}
                onChange={(e) => setOrderQty(e.target.value)}
                className="w-24 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
              />
            </div>
            {orderType === "limit" && (
              <div>
                <label className="block text-xs text-gray-400 mb-1">가격</label>
                <input
                  type="number"
                  value={orderPrice}
                  onChange={(e) => setOrderPrice(e.target.value)}
                  placeholder={price.current_price.toString()}
                  className="w-32 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
                />
              </div>
            )}
            <button
              onClick={async () => {
                try {
                  setOrderMsg("");
                  await fetchApi<Order>("/api/orders", {
                    method: "POST",
                    body: JSON.stringify({
                      stock_code: price.code,
                      side: orderSide,
                      order_type: orderType,
                      quantity: parseInt(orderQty),
                      price: orderType === "limit" ? parseFloat(orderPrice) : null,
                    }),
                  });
                  setOrderMsg(`${orderSide === "buy" ? "매수" : "매도"} 주문 생성 완료`);
                } catch {
                  setOrderMsg("주문 생성 실패");
                }
              }}
              className={`rounded px-4 py-2 font-medium text-white ${
                orderSide === "buy"
                  ? "bg-red-600 hover:bg-red-700"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              {orderSide === "buy" ? "매수" : "매도"}
            </button>
          </div>
          {orderMsg && (
            <p className="mt-3 text-sm text-green-400">{orderMsg}</p>
          )}
        </div>
      )}
    </div>
  );
}
