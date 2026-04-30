"use client";

import { useEffect, useState } from "react";
import { fetchApi, type PortfolioItem } from "@/lib/api";

export default function PortfolioPage() {
  const [items, setItems] = useState<PortfolioItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchApi<PortfolioItem[]>("/api/portfolio")
      .then(setItems)
      .catch(() => setError("포트폴리오 조회에 실패했습니다."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">포트폴리오</h1>

      {loading && <p className="text-gray-400">로딩 중...</p>}
      {error && <p className="text-red-400">{error}</p>}

      {!loading && items.length === 0 && (
        <p className="text-gray-500">보유 종목이 없습니다.</p>
      )}

      {items.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-800">
          <table className="w-full text-left">
            <thead className="bg-gray-900 text-sm text-gray-400">
              <tr>
                <th className="px-4 py-3">종목 코드</th>
                <th className="px-4 py-3 text-right">보유 수량</th>
                <th className="px-4 py-3 text-right">평균 매입가</th>
                <th className="px-4 py-3 text-right">매입 금액</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {items.map((item) => (
                <tr key={item.stock_code} className="hover:bg-gray-900/50">
                  <td className="px-4 py-3 font-medium">{item.stock_code}</td>
                  <td className="px-4 py-3 text-right">
                    {item.quantity.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {item.avg_price.toLocaleString()}원
                  </td>
                  <td className="px-4 py-3 text-right">
                    {(item.quantity * item.avg_price).toLocaleString()}원
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
