"use client";

import React, { createContext, useCallback, useContext, useState } from "react";

type SidebarState = {
  isExpanded: boolean;
  isHovered: boolean;
  isMobileOpen: boolean;
  toggleSidebar: () => void;
  toggleMobileSidebar: () => void;
  setHovered: (v: boolean) => void;
};

const SidebarContext = createContext<SidebarState | null>(null);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isHovered, setIsHovered] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const toggleSidebar = useCallback(() => setIsExpanded((v) => !v), []);
  const toggleMobileSidebar = useCallback(() => setIsMobileOpen((v) => !v), []);
  const setHovered = useCallback((v: boolean) => setIsHovered(v), []);

  return (
    <SidebarContext.Provider
      value={{
        isExpanded,
        isHovered,
        isMobileOpen,
        toggleSidebar,
        toggleMobileSidebar,
        setHovered,
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error("useSidebar must be used within SidebarProvider");
  return ctx;
}
