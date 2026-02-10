"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSidebar } from "@/lib/SidebarContext";
import {
  LayoutDashboard,
  FolderTree,
  Package,
  Users,
  CreditCard,
  Receipt,
  TrendingUp,
} from "lucide-react";

const NAV = [
  { href: "/admin", label: "Головна", icon: LayoutDashboard },
  { href: "/admin/finance", label: "Фінанси", icon: TrendingUp },
  { href: "/admin/categories", label: "Категорії", icon: FolderTree },
  { href: "/admin/products", label: "Товари", icon: Package },
  { href: "/admin/users", label: "Користувачі", icon: Users },
  { href: "/admin/subscriptions", label: "Підписки", icon: CreditCard },
  { href: "/admin/payments", label: "Платежі", icon: Receipt },
];

export default function AppSidebar() {
  const pathname = usePathname();
  const { isExpanded, isHovered, isMobileOpen, setHovered } = useSidebar();
  const showLabels = isExpanded || isHovered;

  return (
    <aside
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={`fixed left-0 top-0 z-[100] flex h-full flex-col border-r border-gray-200 bg-white shadow-lg transition-all duration-300 ease-in-out
        ${isMobileOpen ? "w-[280px] translate-x-0 sm:w-[300px]" : "-translate-x-full"}
        lg:translate-x-0 ${showLabels ? "lg:w-[290px]" : "lg:w-[90px]"}
      `}
    >
      <div className="flex h-14 items-center border-b border-gray-100 px-4">
        <Link href="/admin" className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-600 text-white">
            <LayoutDashboard className="h-5 w-5" />
          </div>
          {showLabels && (
            <span className="truncate text-base font-semibold text-gray-900">
              Flix Market
            </span>
          )}
        </Link>
      </div>
      <nav className="flex-1 space-y-0.5 p-2">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/admin" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? "bg-violet-50 text-violet-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {showLabels && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
