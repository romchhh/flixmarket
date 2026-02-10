"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  Package,
  FolderTree,
  CreditCard,
  Receipt,
  TrendingUp,
  Calendar,
} from "lucide-react";

type Stats = {
  totalUsers: number;
  totalProducts: number;
  totalCategories: number;
  totalSubscriptions: number;
  activeSubscriptions: number;
  totalPaymentsCount: number;
  totalRevenue: number;
  todayPaymentsCount: number;
  todayRevenue: number;
  monthPaymentsCount: number;
  monthRevenue: number;
  newUsersToday: number;
  newUsersMonth: number;
};

const MONTHS = ["Січ", "Лют", "Бер", "Кві", "Тра", "Чер", "Лип", "Сер", "Вер", "Жов", "Лис", "Гру"];

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [paymentsByMonth, setPaymentsByMonth] = useState<number[]>([]);

  useEffect(() => {
    fetch("/api/admin/stats")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setStats(data);
      });
  }, []);

  useEffect(() => {
    fetch("/api/admin/payments?limit=500")
      .then((r) => (r.ok ? r.json() : { payments: [], subPayments: [] }))
      .then((data) => {
        const byMonth = new Array(12).fill(0);
        const thisYear = new Date().getFullYear();
        [...(data.payments || []), ...(data.subPayments || [])].forEach((p: { amount: number; created_at?: string; payment_date?: string }) => {
          const dateStr = p.created_at || p.payment_date;
          if (!dateStr || (p as { status?: string }).status !== "success") return;
          const d = new Date(dateStr);
          if (d.getFullYear() === thisYear) byMonth[d.getMonth()] += Number(p.amount) || 0;
        });
        setPaymentsByMonth(byMonth);
      });
  }, []);

  if (stats === null) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Головна</h1>
        <p className="text-gray-500">Завантаження…</p>
      </div>
    );
  }

  const maxRevenue = Math.max(1, ...paymentsByMonth);

  const cards = [
    {
      label: "Користувачі",
      value: stats.totalUsers,
      sub: `+${stats.newUsersMonth} за місяць`,
      icon: Users,
      href: "/admin/users",
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600",
    },
    {
      label: "Категорії",
      value: stats.totalCategories,
      icon: FolderTree,
      href: "/admin/categories",
      iconBg: "bg-violet-100",
      iconColor: "text-violet-600",
    },
    {
      label: "Товари",
      value: stats.totalProducts,
      icon: Package,
      href: "/admin/products",
      iconBg: "bg-amber-100",
      iconColor: "text-amber-600",
    },
    {
      label: "Активні підписки",
      value: stats.activeSubscriptions,
      sub: `всього ${stats.totalSubscriptions}`,
      icon: CreditCard,
      href: "/admin/subscriptions",
      iconBg: "bg-emerald-100",
      iconColor: "text-emerald-600",
    },
    {
      label: "Дохід (всього)",
      value: `${stats.totalRevenue.toFixed(0)} ₴`,
      icon: TrendingUp,
      iconBg: "bg-green-100",
      iconColor: "text-green-600",
    },
    {
      label: "Платежі сьогодні",
      value: stats.todayPaymentsCount,
      sub: `${stats.todayRevenue.toFixed(0)} ₴`,
      icon: Calendar,
      iconBg: "bg-sky-100",
      iconColor: "text-sky-600",
    },
    {
      label: "За місяць",
      value: `${stats.monthRevenue.toFixed(0)} ₴`,
      sub: `${stats.monthPaymentsCount} платежів`,
      icon: Receipt,
      iconBg: "bg-gray-100",
      iconColor: "text-gray-700",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">Дашборд</h1>
        <p className="mt-1 text-sm text-gray-500">Огляд статистики Flix Market</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {cards.map((item) => {
          const Icon = item.icon;
          const content = (
            <>
              <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${item.iconBg} ${item.iconColor}`}>
                <Icon className="h-6 w-6" />
              </div>
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-500">{item.label}</p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{item.value}</p>
                {item.sub && <p className="mt-0.5 text-xs text-gray-500">{item.sub}</p>}
              </div>
            </>
          );
          const className = "rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow";
          if (item.href) {
            return (
              <Link key={item.label} href={item.href} className={className}>
                {content}
              </Link>
            );
          }
          return (
            <div key={item.label} className={className}>
              {content}
            </div>
          );
        })}
      </div>

      <div className="overflow-x-auto rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <h3 className="text-base font-semibold text-gray-900 sm:text-lg">Дохід по місяцях ({new Date().getFullYear()})</h3>
        <div className="mt-4 flex min-w-0 items-end justify-between gap-0.5 sm:gap-1" style={{ minHeight: "140px" }}>
          {MONTHS.map((month, i) => {
            const value = paymentsByMonth[i] ?? 0;
            return (
            <div key={month} className="flex flex-1 flex-col items-center gap-1">
              <div
                className="w-full max-w-[28px] rounded-t bg-violet-200 transition-colors hover:bg-violet-300"
                style={{
                  height: `${(value / maxRevenue) * 120}px`,
                  minHeight: value > 0 ? "4px" : "0",
                }}
                title={`${month}: ${value.toFixed(0)} ₴`}
              />
              <span className="text-xs text-gray-500">{month}</span>
            </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
