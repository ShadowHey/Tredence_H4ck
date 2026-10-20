"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Layers,
  Store,
} from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    {
      label: "Dashboard",
      href: "/",
      icon: LayoutDashboard,
      active: pathname === "/",
    },
    {
      label: "Design Planogram",
      href: "/designer",
      icon: Layers,
      active: pathname.startsWith("/designer"),
    },
  ];

  return (
    <aside
      className="w-16 md:w-64 flex flex-col justify-between border-r border-[#262b36] bg-[#13161c] h-screen select-none shrink-0 transition-all duration-200"
      data-testid="main-sidebar"
    >
      <div>
        {/* Brand header */}
        <div className="h-16 flex items-center px-4 md:px-5 border-b border-[#262b36] gap-3">
          <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0">
            <Store className="w-5 h-5 text-amber-400" />
          </div>
          <div className="hidden md:flex flex-col">
            <span className="font-semibold text-sm tracking-wide text-gray-100">
              ShelfSense <span className="text-amber-400 font-bold">AI</span>
            </span>
            <span className="text-[11px] text-gray-400">Planogram Studio</span>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="p-3 space-y-1.5">
          <div className="hidden md:block px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
            Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  item.active
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30 shadow-sm"
                    : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1e26] border border-transparent"
                }`}
                title={item.label}
              >
                <Icon className={`w-5 h-5 shrink-0 ${item.active ? "text-amber-400" : "text-gray-400"}`} />
                <span className="hidden md:inline">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-[#262b36]">
        <div className="hidden md:flex items-center gap-3 px-3 py-2 bg-[#1a1e26] rounded-lg border border-[#262b36]">
          <div className="w-7 h-7 rounded-full bg-amber-500/20 text-amber-400 font-bold text-xs flex items-center justify-center">
            SS
          </div>
          <div className="flex flex-col overflow-hidden">
            <span className="text-xs font-medium text-gray-200 truncate">Store Workspace</span>
            <span className="text-[10px] text-gray-400">v0.1.0 · Stage 1</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
