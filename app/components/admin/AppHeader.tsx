"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSidebar } from "@/lib/SidebarContext";

export default function AppHeader() {
  const router = useRouter();
  const { isMobileOpen, toggleSidebar, toggleMobileSidebar } = useSidebar();

  const handleToggle = () => {
    if (typeof window !== "undefined" && window.innerWidth >= 1024) {
      toggleSidebar();
    } else {
      toggleMobileSidebar();
    }
  };

  return (
    <header className="sticky top-0 z-[9999] flex w-full border-b border-gray-200 bg-white text-gray-900">
      <div className="flex w-full items-center justify-between px-3 py-2.5 sm:px-4 sm:py-3 lg:px-6">
        <button
          type="button"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 sm:h-10 sm:w-10"
          onClick={handleToggle}
          aria-label="Меню"
        >
          {isMobileOpen ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </button>
        <div className="flex items-center gap-3">
          <Link
            href="/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Відкрити сайт →
          </Link>
          <button
            type="button"
            onClick={async () => {
              if (!confirm("Вийти з адмін-панелі?")) return;
              await fetch("/api/admin/logout", { method: "POST" });
              router.push("/admin/login");
              router.refresh();
            }}
            className="text-sm text-gray-600 hover:text-red-600"
          >
            Вийти
          </button>
        </div>
      </div>
    </header>
  );
}
