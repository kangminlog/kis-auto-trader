"use client";

import { useEffect, useState } from "react";
import { fetchApi, type Order } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "text-yellow-400",
  filled: "text-green-400",
  cancelled: "text-gray-500",
  rejected: "text-red-400",
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    fetchApi<Order[]>("/api/orders")
      .then((data) => { if (!ignore) setOrders(data); })
      .catch(() => { if (!ignore) setError("주문 내역 조회에 실패했습니다."); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, []);

  function loadOrders() {
    setLoading(true);
    fetchApi<Order[]>("/api/orders")
      .then(setOrders)
      .catch(() => setError("주문 내역 조회에 실패했습니다."))
      .finally(() => setLoading(false));
  }

  async function handleCancel(orderId: number) {
    try {
      await fetchApi(`/api/orders/${orderId}`, { method: "DELETE" });
      loadOrders();
    } catch {
      setError("주문 취소에 실패했습니다.");
    }
  }

  async function handleExecute() {
    try {
      await fetchApi("/api/execute", { method: "POST" });
      loadOrders();
    } catch {
      setError("체결 실행에 실패했습니다.");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">주문 내역</h1>
        <button
          onClick={handleExecute}
          className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
        >
          대기 주문 체결
        </button>
      </div>

      {loading && <p className="text-gray-400">로딩 중...</p>}
      {error && <p className="text-red-400">{error}</p>}

      {!loading && orders.length === 0 && (
        <p className="text-gray-500">주문 내역이 없습니다.</p>
      )}

      {orders.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-800">
          <table className="w-full text-left">
            <thead className="bg-gray-900 text-sm text-gray-400">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">종목</th>
                <th className="px-4 py-3">매매</th>
                <th className="px-4 py-3">유형</th>
                <th className="px-4 py-3 text-right">수량</th>
                <th className="px-4 py-3 text-right">가격</th>
                <th className="px-4 py-3">상태</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-900/50">
                  <td className="px-4 py-3 text-gray-500">{order.id}</td>
                  <td className="px-4 py-3 font-medium">{order.stock_code}</td>
                  <td
                    className={`px-4 py-3 font-medium ${order.side === "buy" ? "text-red-400" : "text-blue-400"}`}
                  >
                    {order.side === "buy" ? "매수" : "매도"}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {order.order_type === "market" ? "시장가" : "지정가"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {order.quantity.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {order.price ? `${order.price.toLocaleString()}원` : "-"}
                  </td>
                  <td
                    className={`px-4 py-3 font-medium ${STATUS_COLORS[order.status] || ""}`}
                  >
                    {order.status}
                  </td>
                  <td className="px-4 py-3">
                    {order.status === "pending" && (
                      <button
                        onClick={() => handleCancel(order.id)}
                        className="text-sm text-red-400 hover:text-red-300"
                      >
                        취소
                      </button>
                    )}
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
