"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { SidebarProvider } from "@/lib/SidebarContext";
import ClientLayoutShell from "@/components/admin/ClientLayoutShell";

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    if (pathname === "/admin/login") {
      setChecked(true);
      setAuthenticated(false);
      return;
    }
    fetch("/api/admin/me")
      .then((r) => r.json())
      .then((data) => {
        setAuthenticated(data.authenticated === true);
        if (!data.authenticated) {
          router.replace("/admin/login");
        }
      })
      .catch(() => router.replace("/admin/login"))
      .finally(() => setChecked(true));
  }, [pathname, router]);

  if (pathname === "/admin/login") {
    return <>{children}</>;
  }

  if (!checked) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <p className="text-gray-500">Завантаження…</p>
      </div>
    );
  }

  if (!authenticated) {
    return null;
  }

  return (
    <SidebarProvider>
      <ClientLayoutShell>{children}</ClientLayoutShell>
    </SidebarProvider>
  );
}
