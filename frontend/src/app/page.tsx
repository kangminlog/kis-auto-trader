export default function Home() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">대시보드</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-sm text-gray-400">환경</h2>
          <p className="mt-1 text-2xl font-semibold text-green-400">
            Paper Trading
          </p>
        </div>
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-sm text-gray-400">보유 종목</h2>
          <p className="mt-1 text-2xl font-semibold">-</p>
        </div>
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-sm text-gray-400">총 평가 손익</h2>
          <p className="mt-1 text-2xl font-semibold">-</p>
        </div>
      </div>
    </div>
  );
}
