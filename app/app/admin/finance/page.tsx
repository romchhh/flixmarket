"use client";

import { useState, useEffect } from "react";

type FinanceData = {
  fromDate: string;
  toDate: string;
  totalRevenue: number;
  totalOneTime: number;
  totalSubscription: number;
  paymentsCount: number;
  subPaymentsCount: number;
  daily: Array<{ date: string; oneTime: number; subscription: number; total: number }>;
};

const MONTHS_UK = ["Січ", "Лют", "Бер", "Кві", "Тра", "Чер", "Лип", "Сер", "Вер", "Жов", "Лис", "Гру"];

function formatDateLabel(d: string) {
  const [y, m, day] = d.split("-").map(Number);
  return `${day} ${MONTHS_UK[(m ?? 1) - 1]}`;
}

export default function AdminFinancePage() {
  const today = new Date().toISOString().slice(0, 10);
  const firstDayOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10);

  const [fromDate, setFromDate] = useState(firstDayOfMonth);
  const [toDate, setToDate] = useState(today);
  const [singleDate, setSingleDate] = useState("");
  const [mode, setMode] = useState<"range" | "single">("range");
  const [data, setData] = useState<FinanceData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchFinance = (from: string, to: string) => {
    setLoading(true);
    fetch(`/api/admin/finance?from=${from}&to=${to}`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setData)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (mode === "single" && singleDate) {
      fetchFinance(singleDate, singleDate);
    } else if (mode === "range" && fromDate && toDate) {
      fetchFinance(fromDate, toDate);
    } else {
      setData(null);
    }
  }, [mode, fromDate, toDate, singleDate]);

  const handleApplyRange = () => {
    if (fromDate && toDate) fetchFinance(fromDate, toDate);
  };

  const handleApplySingle = () => {
    if (singleDate) fetchFinance(singleDate, singleDate);
  };

  const maxDaily = data?.daily?.length ? Math.max(...data.daily.map((d) => d.total), 1) : 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Фінанси та аналітика</h1>
        <p className="mt-1 text-sm text-gray-500">Дохід за обраний період або дату</p>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setMode("range")}
              className={`rounded-lg px-3 py-2 text-sm font-medium ${mode === "range" ? "bg-violet-600 text-white" : "bg-gray-100 text-gray-700"}`}
            >
              Період
            </button>
            <button
              type="button"
              onClick={() => setMode("single")}
              className={`rounded-lg px-3 py-2 text-sm font-medium ${mode === "single" ? "bg-violet-600 text-white" : "bg-gray-100 text-gray-700"}`}
            >
              Одна дата
            </button>
          </div>

          {mode === "range" ? (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <label className="text-sm text-gray-600">З</label>
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
                <label className="text-sm text-gray-600">по</label>
                <input
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <button
                type="button"
                onClick={handleApplyRange}
                disabled={loading}
                className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
              >
                Застосувати
              </button>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">Дата</label>
                <input
                  type="date"
                  value={singleDate}
                  onChange={(e) => setSingleDate(e.target.value)}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <button
                type="button"
                onClick={handleApplySingle}
                disabled={loading || !singleDate}
                className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
              >
                Застосувати
              </button>
            </>
          )}
        </div>
      </div>

      {loading && (
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-gray-500">
          Завантаження…
        </div>
      )}

      {!loading && data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-500">Дохід за період</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">{data.totalRevenue.toFixed(0)} ₴</p>
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-500">Одноразові платежі</p>
              <p className="mt-1 text-xl font-bold text-gray-900">{data.totalOneTime.toFixed(0)} ₴</p>
              <p className="text-xs text-gray-500">{data.paymentsCount} шт.</p>
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-500">По підписках</p>
              <p className="mt-1 text-xl font-bold text-gray-900">{data.totalSubscription.toFixed(0)} ₴</p>
              <p className="text-xs text-gray-500">{data.subPaymentsCount} шт.</p>
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-500">Всього транзакцій</p>
              <p className="mt-1 text-xl font-bold text-gray-900">{data.paymentsCount + data.subPaymentsCount}</p>
            </div>
          </div>

          {data.daily.length > 0 && (
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900">Дохід по днях</h3>
              <div className="mt-4 overflow-x-auto">
                <div className="flex min-w-0 items-end justify-between gap-1 pb-2" style={{ minHeight: "180px" }}>
                  {data.daily.map((d) => (
                    <div
                      key={d.date}
                      className="flex min-w-0 flex-1 flex-col items-center gap-1"
                      title={`${d.date}: ${d.total.toFixed(0)} ₴`}
                    >
                      <div
                        className="w-full max-w-[40px] rounded-t bg-violet-200 transition-colors hover:bg-violet-300 sm:max-w-[32px]"
                        style={{
                          height: `${(d.total / maxDaily) * 140}px`,
                          minHeight: d.total > 0 ? "4px" : "0",
                        }}
                      />
                      <span className="hidden text-xs text-gray-600 sm:inline">{d.total > 0 ? d.total.toFixed(0) : ""}</span>
                      <span className="truncate text-[10px] text-gray-500 sm:text-xs">{formatDateLabel(d.date)}</span>
                    </div>
                  ))}
                </div>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                Період: {formatDateLabel(data.fromDate)} — {formatDateLabel(data.toDate)}
              </p>
            </div>
          )}

          {data.daily.length === 0 && data.fromDate && (
            <div className="rounded-2xl border border-gray-200 bg-white p-6 text-center text-gray-500">
              За обраний період немає успішних платежів.
            </div>
          )}
        </>
      )}
    </div>
  );
}
