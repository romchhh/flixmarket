"use client";

import { usePathname } from "next/navigation";
import BottomNav from "@/components/BottomNav";

export default function ShopLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isAdmin = pathname?.startsWith("/admin") ?? false;

  if (isAdmin) {
    return <>{children}</>;
  }

  return (
    <>
      <div className="min-h-screen pb-24">{children}</div>
      <BottomNav />
    </>
  );
}
