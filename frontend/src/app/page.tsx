"use client";

import { useEffect, useState } from "react";
import {
  fetchApi,
  type AutoTradeConfig,
  type AutoTradeLog,
  type PortfolioItem,
  type SchedulerStatus,
} from "@/lib/api";

interface SafetyStatus {
  kill_switch: boolean;
  trade_count: number;
  max_trades: number;
  trade_amount: number;
  max_amount: number;
  stop_loss_pct: number;
  take_profit_pct: number;
}

export default function Home() {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [configs, setConfigs] = useState<AutoTradeConfig[]>([]);
  const [logs, setLogs] = useState<AutoTradeLog[]>([]);
  const [scheduler, setScheduler] = useState<SchedulerStatus>({ running: false });
  const [safety, setSafety] = useState<SafetyStatus | null>(null);

  useEffect(() => {
    fetchApi<PortfolioItem[]>("/api/portfolio").then(setPortfolio).catch(() => {});
    fetchApi<AutoTradeConfig[]>("/api/auto-trade/configs").then(setConfigs).catch(() => {});
    fetchApi<AutoTradeLog[]>("/api/auto-trade/logs?limit=5").then(setLogs).catch(() => {});
    fetchApi<SchedulerStatus>("/api/auto-trade/scheduler/status").then(setScheduler).catch(() => {});
    fetchApi<SafetyStatus>("/api/safety/status").then(setSafety).catch(() => {});
  }, []);

  const activeConfigs = configs.filter((c) => c.is_active).length;
  const totalValue = portfolio.reduce((sum, p) => sum + p.quantity * p.avg_price, 0);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">대시보드</h1>

      {/* 상태 카드 */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="text-xs text-gray-400">환경</h2>
          <p className="mt-1 text-xl font-semibold text-green-400">Paper Trading</p>
        </div>
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="text-xs text-gray-400">스케줄러</h2>
          <div className="mt-1 flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${scheduler.running ? "bg-green-400" : "bg-gray-600"}`} />
            <span className="text-xl font-semibold">{scheduler.running ? "실행 중" : "중지"}</span>
          </div>
        </div>
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="text-xs text-gray-400">보유 종목 / 활성 전략</h2>
          <p className="mt-1 text-xl font-semibold">
            {portfolio.length}종목 / {activeConfigs}전략
          </p>
        </div>
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="text-xs text-gray-400">총 매입 금액</h2>
          <p className="mt-1 text-xl font-semibold">{totalValue.toLocaleString()}원</p>
        </div>
      </div>

      {/* 안전장치 상태 */}
      {safety && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="text-sm font-semibold mb-3">안전장치</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5 text-sm">
            <div>
              <span className="text-gray-400">Kill Switch</span>
              <p className={`font-medium ${safety.kill_switch ? "text-red-400" : "text-green-400"}`}>
                {safety.kill_switch ? "ON" : "OFF"}
              </p>
            </div>
            <div>
              <span className="text-gray-400">오늘 매매</span>
              <p className="font-medium">{safety.trade_count} / {safety.max_trades}회</p>
            </div>
            <div>
              <span className="text-gray-400">오늘 금액</span>
              <p className="font-medium">{safety.trade_amount.toLocaleString()} / {safety.max_amount.toLocaleString()}원</p>
            </div>
            <div>
              <span className="text-gray-400">손절</span>
              <p className="font-medium text-red-400">{safety.stop_loss_pct}%</p>
            </div>
            <div>
              <span className="text-gray-400">익절</span>
              <p className="font-medium text-green-400">{safety.take_profit_pct}%</p>
            </div>
          </div>
        </div>
      )}

      {/* 최근 실행 로그 */}
      <div>
        <h2 className="text-sm font-semibold mb-3">최근 실행 로그</h2>
        {logs.length === 0 ? (
          <p className="text-gray-500 text-sm">실행 로그가 없습니다.</p>
        ) : (
          <div className="space-y-1.5">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex items-center gap-3 rounded border border-gray-800 bg-gray-900 px-4 py-2 text-sm"
              >
                <span className="text-gray-500 text-xs w-36 shrink-0">{log.created_at}</span>
                <span className="font-medium w-16">{log.stock_code}</span>
                <span
                  className={`w-12 font-medium ${
                    log.signal === "buy" ? "text-red-400" : log.signal === "sell" ? "text-blue-400" : "text-gray-500"
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
                <span className="text-gray-500 text-xs truncate flex-1">{log.reason}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 보유 종목 */}
      {portfolio.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold mb-3">보유 종목</h2>
          <div className="overflow-x-auto rounded-lg border border-gray-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-900 text-gray-400">
                <tr>
                  <th className="px-4 py-2">종목</th>
                  <th className="px-4 py-2 text-right">수량</th>
                  <th className="px-4 py-2 text-right">평균가</th>
                  <th className="px-4 py-2 text-right">매입금액</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {portfolio.map((p) => (
                  <tr key={p.stock_code}>
                    <td className="px-4 py-2 font-medium">{p.stock_code}</td>
                    <td className="px-4 py-2 text-right">{p.quantity}</td>
                    <td className="px-4 py-2 text-right">{p.avg_price.toLocaleString()}원</td>
                    <td className="px-4 py-2 text-right">{(p.quantity * p.avg_price).toLocaleString()}원</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
