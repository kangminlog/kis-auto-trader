"use client";

import { useEffect, useState } from "react";
import {
  fetchApi,
  type AutoTradeConfig,
  type AutoTradeLog,
  type SchedulerStatus,
  type StrategyInfo,
} from "@/lib/api";

const PRESET_STOCKS = [
  { code: "005930", name: "삼성전자" },
  { code: "000660", name: "SK하이닉스" },
  { code: "035420", name: "NAVER" },
  { code: "051910", name: "LG화학" },
  { code: "006400", name: "삼성SDI" },
];

export default function AutoTradePage() {
  const [configs, setConfigs] = useState<AutoTradeConfig[]>([]);
  const [logs, setLogs] = useState<AutoTradeLog[]>([]);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [scheduler, setScheduler] = useState<SchedulerStatus>({ running: false });
  const [error, setError] = useState("");

  // 새 설정 폼
  const [newCode, setNewCode] = useState("");
  const [newName, setNewName] = useState("");
  const [newStrategy, setNewStrategy] = useState("");
  const [newQty, setNewQty] = useState("10");
  const [newStopLoss, setNewStopLoss] = useState("");
  const [newTakeProfit, setNewTakeProfit] = useState("");

  function loadAll() {
    fetchApi<AutoTradeConfig[]>("/api/auto-trade/configs").then(setConfigs).catch(() => {});
    fetchApi<AutoTradeLog[]>("/api/auto-trade/logs?limit=20").then(setLogs).catch(() => {});
    fetchApi<SchedulerStatus>("/api/auto-trade/scheduler/status").then(setScheduler).catch(() => {});
  }

  useEffect(() => {
    fetchApi<StrategyInfo[]>("/api/strategy/list").then((s) => {
      setStrategies(s);
      if (s.length > 0) setNewStrategy(s[0].name);
    }).catch(() => {});
    loadAll();
  }, []);

  async function handleAddConfig() {
    if (!newCode || !newStrategy) return;
    try {
      await fetchApi("/api/auto-trade/configs", {
        method: "POST",
        body: JSON.stringify({
          stock_code: newCode,
          stock_name: newName,
          strategy_name: newStrategy,
          quantity: parseInt(newQty),
          stop_loss_price: newStopLoss ? parseFloat(newStopLoss) : null,
          take_profit_price: newTakeProfit ? parseFloat(newTakeProfit) : null,
        }),
      });
      setNewCode("");
      setNewName("");
      loadAll();
    } catch {
      setError("설정 추가 실패");
    }
  }

  async function handleToggle(id: number) {
    await fetchApi(`/api/auto-trade/configs/${id}/toggle`, { method: "PATCH" });
    loadAll();
  }

  async function handleDelete(id: number) {
    await fetchApi(`/api/auto-trade/configs/${id}`, { method: "DELETE" });
    loadAll();
  }

  async function handleScheduler(action: "start" | "stop") {
    await fetchApi(`/api/auto-trade/scheduler/${action}`, { method: "POST" });
    loadAll();
  }

  async function handleTrigger() {
    await fetchApi("/api/auto-trade/scheduler/trigger", { method: "POST" });
    loadAll();
  }

  function selectPreset(stock: { code: string; name: string }) {
    setNewCode(stock.code);
    setNewName(stock.name);
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">자동매매</h1>
        <div className="flex items-center gap-3">
          <span
            className={`inline-block h-3 w-3 rounded-full ${scheduler.running ? "bg-green-400" : "bg-gray-600"}`}
          />
          <span className="text-sm text-gray-400">
            {scheduler.running ? "스케줄러 실행 중" : "스케줄러 중지"}
          </span>
          {scheduler.running ? (
            <button
              onClick={() => handleScheduler("stop")}
              className="rounded bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700"
            >
              중지
            </button>
          ) : (
            <button
              onClick={() => handleScheduler("start")}
              className="rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"
            >
              시작
            </button>
          )}
          <button
            onClick={handleTrigger}
            className="rounded border border-gray-600 px-3 py-1.5 text-sm text-gray-300 hover:border-white hover:text-white"
          >
            수동 실행
          </button>
        </div>
      </div>

      {error && <p className="text-red-400">{error}</p>}

      {/* 새 설정 추가 */}
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
        <h2 className="text-lg font-semibold mb-4">전략 설정 추가</h2>
        <div className="flex flex-wrap gap-2 mb-4">
          {PRESET_STOCKS.map((s) => (
            <button
              key={s.code}
              onClick={() => selectPreset(s)}
              className={`rounded border px-3 py-1.5 text-sm transition-colors ${
                newCode === s.code
                  ? "border-blue-500 text-white"
                  : "border-gray-700 text-gray-400 hover:border-blue-500"
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-400 mb-1">종목 코드</label>
            <input
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              placeholder="005930"
              className="w-28 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">종목명</label>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="삼성전자"
              className="w-28 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">전략</label>
            <select
              value={newStrategy}
              onChange={(e) => setNewStrategy(e.target.value)}
              className="rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
            >
              {strategies.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name} — {s.description}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">수량</label>
            <input
              type="number"
              min="1"
              value={newQty}
              onChange={(e) => setNewQty(e.target.value)}
              className="w-20 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">손절가</label>
            <input
              type="number"
              value={newStopLoss}
              onChange={(e) => setNewStopLoss(e.target.value)}
              placeholder="미설정"
              className="w-28 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">익절가</label>
            <input
              type="number"
              value={newTakeProfit}
              onChange={(e) => setNewTakeProfit(e.target.value)}
              placeholder="미설정"
              className="w-28 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white"
            />
          </div>
          <button
            onClick={handleAddConfig}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            추가
          </button>
        </div>
      </div>

      {/* 설정 목록 */}
      {configs.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-800">
          <table className="w-full text-left">
            <thead className="bg-gray-900 text-sm text-gray-400">
              <tr>
                <th className="px-4 py-3">종목</th>
                <th className="px-4 py-3">전략</th>
                <th className="px-4 py-3 text-right">수량</th>
                <th className="px-4 py-3 text-right">손절가</th>
                <th className="px-4 py-3 text-right">익절가</th>
                <th className="px-4 py-3">상태</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {configs.map((c) => (
                <tr key={c.id} className="hover:bg-gray-900/50">
                  <td className="px-4 py-3">
                    <span className="font-medium">{c.stock_code}</span>
                    {c.stock_name && (
                      <span className="ml-2 text-sm text-gray-500">{c.stock_name}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-300">{c.strategy_name}</td>
                  <td className="px-4 py-3 text-right">{c.quantity}</td>
                  <td className="px-4 py-3 text-right text-red-400">
                    {c.stop_loss_price ? `${c.stop_loss_price.toLocaleString()}` : "-"}
                  </td>
                  <td className="px-4 py-3 text-right text-green-400">
                    {c.take_profit_price ? `${c.take_profit_price.toLocaleString()}` : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggle(c.id)}
                      className={`rounded px-2 py-1 text-xs font-medium ${
                        c.is_active
                          ? "bg-green-900 text-green-300"
                          : "bg-gray-800 text-gray-500"
                      }`}
                    >
                      {c.is_active ? "활성" : "비활성"}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleDelete(c.id)}
                      className="text-sm text-red-400 hover:text-red-300"
                    >
                      삭제
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 실행 로그 */}
      <div>
        <h2 className="text-lg font-semibold mb-3">실행 로그</h2>
        {logs.length === 0 ? (
          <p className="text-gray-500">실행 로그가 없습니다.</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex items-center gap-3 rounded border border-gray-800 bg-gray-900 px-4 py-2 text-sm"
              >
                <span className="text-gray-500 text-xs w-36 shrink-0">
                  {log.created_at}
                </span>
                <span className="font-medium w-16">{log.stock_code}</span>
                <span className="text-gray-400 w-24">{log.strategy_name}</span>
                <span
                  className={`w-12 font-medium ${
                    log.signal === "buy"
                      ? "text-red-400"
                      : log.signal === "sell"
                        ? "text-blue-400"
                        : "text-gray-500"
                  }`}
                >
                  {log.signal.toUpperCase()}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    log.action_taken === "order_placed"
                      ? "bg-green-900 text-green-300"
                      : log.action_taken === "error"
                        ? "bg-red-900 text-red-300"
                        : "bg-gray-800 text-gray-500"
                  }`}
                >
                  {log.action_taken}
                </span>
                <span className="text-gray-500 text-xs truncate flex-1">
                  {log.reason}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
