"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Heart, CreditCard, User } from "lucide-react";
import type { LucideProps } from "lucide-react";

type NavItem = {
  href: string;
  icon: React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
  label: string;
  badgeKey?: string;
};

const navItems: NavItem[] = [
  { href: "/", icon: Home, label: "Головна" },
  { href: "/favorites", icon: Heart, label: "Обране", badgeKey: "flix-favorites" },
  { href: "/subscriptions", icon: CreditCard, label: "Мої підписки" },
  { href: "/profile", icon: User, label: "Мій профіль" },
];

const FAVORITES_CHANGED_EVENT = "flix-favorites-changed";

function useFavoritesCount(pathname: string): number {
  const [count, setCount] = useState(0);
  const refresh = () => {
    try {
      const raw = localStorage.getItem("flix-favorites");
      if (raw) {
        const arr = JSON.parse(raw);
        setCount(Array.isArray(arr) ? arr.length : 0);
      } else setCount(0);
    } catch {
      setCount(0);
    }
  };
  useEffect(() => {
    refresh();
  }, [pathname]);
  useEffect(() => {
    const handler = () => refresh();
    window.addEventListener(FAVORITES_CHANGED_EVENT, handler);
    return () => window.removeEventListener(FAVORITES_CHANGED_EVENT, handler);
  }, []);
  return count;
}

export default function BottomNav() {
  const pathname = usePathname();
  const favoritesCount = useFavoritesCount(pathname);

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-[100] px-4 pb-4" style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}>
      <div className="max-w-md mx-auto flex items-center justify-around rounded-[2rem] bg-white/90 backdrop-blur-xl border border-gray-100 shadow-lg py-1.5 px-2">
        {navItems.map(({ href, icon: Icon, label, badgeKey }) => {
          const isActive =
            href === "/"
              ? pathname === "/"
              : pathname === href || pathname.startsWith(href + "/");
          const badge = badgeKey === "flix-favorites" && favoritesCount > 0 ? favoritesCount : null;
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-0.5 min-w-[56px] py-1 rounded-2xl transition-all ${
                isActive ? "text-violet-600" : "text-gray-500 hover:text-gray-700"
              }`}
              aria-label={label}
            >
              <span
                className={`relative flex items-center justify-center w-9 h-9 rounded-full transition-all ${
                  isActive ? "bg-violet-500 text-white" : ""
                }`}
              >
                <Icon
                  className="w-5 h-5"
                  fill={isActive ? "currentColor" : "none"}
                  strokeWidth={isActive ? 2.5 : 2}
                />
                {badge != null && (
                  <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white px-1">
                    {badge > 99 ? "99+" : badge}
                  </span>
                )}
              </span>
              <span className="text-xs font-bold leading-tight">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
