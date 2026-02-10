"use client";

import { useSidebar } from "@/lib/SidebarContext";
import AppSidebar from "@/components/admin/AppSidebar";
import AppHeader from "@/components/admin/AppHeader";
import Backdrop from "@/components/admin/Backdrop";
import { usePathname } from "next/navigation";

export default function ClientLayoutShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isExpanded, isHovered, isMobileOpen } = useSidebar();
  const pathname = usePathname();

  const mainContentMargin =
    isMobileOpen ? "ml-0" : isExpanded || isHovered ? "lg:ml-[290px]" : "lg:ml-[90px]";

  return (
    <div className="min-h-screen bg-gray-50 xl:flex">
      <AppSidebar />
      <Backdrop />
      <div
        className={`min-w-0 flex-1 transition-all duration-300 ease-in-out ${mainContentMargin}`}
      >
        <AppHeader />
        <div className="mx-auto min-w-0 max-w-7xl px-3 py-4 text-gray-900 sm:px-4 md:px-6 md:py-6">
          {children}
        </div>
      </div>
    </div>
  );
}
