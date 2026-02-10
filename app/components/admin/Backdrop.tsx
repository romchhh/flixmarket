"use client";

import { useSidebar } from "@/lib/SidebarContext";

export default function Backdrop() {
  const { isMobileOpen, toggleMobileSidebar } = useSidebar();

  if (!isMobileOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[90] bg-black/40 lg:hidden"
      onClick={toggleMobileSidebar}
      onKeyDown={(e) => e.key === "Escape" && toggleMobileSidebar()}
      role="button"
      tabIndex={0}
      aria-label="Закрити меню"
    />
  );
}
