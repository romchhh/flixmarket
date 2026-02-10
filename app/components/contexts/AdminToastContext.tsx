"use client";

import React, { createContext, useCallback, useContext, useState } from "react";

type ToastType = "success" | "error" | "info";

interface ToastState {
  message: string;
  type: ToastType;
}

interface AdminToastContextValue {
  show: (message: string, type?: ToastType) => void;
}

const AdminToastContext = createContext<AdminToastContextValue | null>(null);

export function AdminToastProvider({ children }: { children: React.ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null);

  const show = useCallback((message: string, type: ToastType = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  return (
    <AdminToastContext.Provider value={{ show }}>
      {children}
      {toast && (
        <div
          role="alert"
          className={`fixed top-4 right-4 z-[100] flex max-w-md items-center gap-3 rounded-xl border-2 px-5 py-4 shadow-xl ${
            toast.type === "success"
              ? "border-green-500 bg-green-600 text-white"
              : toast.type === "error"
                ? "border-red-400 bg-red-600 text-white"
                : "border-gray-600 bg-gray-800 text-white"
          }`}
        >
          {toast.type === "success" && (
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/20">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </span>
          )}
          <p className="text-base font-semibold">{toast.message}</p>
        </div>
      )}
    </AdminToastContext.Provider>
  );
}

export function useAdminToast() {
  const ctx = useContext(AdminToastContext);
  if (!ctx) return { show: () => {} };
  return ctx;
}
