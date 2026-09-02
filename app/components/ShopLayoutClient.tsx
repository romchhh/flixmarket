"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import BottomNav from "@/components/BottomNav";
import ShopFooter from "@/components/ShopFooter";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        expand?: () => void;
        ready?: () => void;
        disableVerticalSwipes?: () => void;
        enableClosingConfirmation?: () => void;
      };
    };
  }
}

export default function ShopLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isAdmin = pathname?.startsWith("/admin") ?? false;

  useEffect(() => {
    const tg = typeof window !== "undefined" ? window.Telegram?.WebApp : undefined;
    if (tg) {
      tg.expand?.();
      tg.disableVerticalSwipes?.();
      tg.enableClosingConfirmation?.();
      tg.ready?.();
    }
  }, []);

  if (isAdmin) {
    return <>{children}</>;
  }

  return (
    <>
      <div className="min-h-screen pb-24 flex flex-col">
        <div className="flex-1">{children}</div>
        <ShopFooter />
      </div>
      <BottomNav />
    </>
  );
}
