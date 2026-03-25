"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export type SidebarItem =
  | "hub"
  | "dossier"
  | "truthfulness"
  | "compare"
  | "search";

const mainNavItems: {
  id: SidebarItem;
  label: string;
  icon: string;
  href: string;
}[] = [
  { id: "hub", label: "VALDYMO CENTRAS", icon: "grid_view", href: "/" },
  {
    id: "dossier",
    label: "POLITIKŲ DOSJE",
    icon: "folder_shared",
    href: "/dossier",
  },
  {
    id: "truthfulness",
    label: "TIESOS MATAVIMAS",
    icon: "analytics",
    href: "/truthfulness",
  },
  {
    id: "compare",
    label: "PALYGINIMO CENTRAS",
    icon: "compare_arrows",
    href: "/compare",
  },
  { id: "search", label: "ARCHYVAS", icon: "search", href: "/search" },
];

export default function Sidebar() {
  const pathname = usePathname();

  function isActive(item: (typeof mainNavItems)[0]) {
    if (item.href === "/") return pathname === "/";
    return pathname.startsWith(item.href);
  }

  return (
    <aside className="fixed left-0 top-14 h-[calc(100vh-3.5rem)] w-64 bg-surface-container-low border-r border-outline-variant/15 flex flex-col pt-4 pb-6 z-40">
      {/* Agent identity */}
      <div className="px-6 mb-8">
        <div className="text-[11px] font-bold uppercase tracking-[0.05rem] text-primary font-label">
          SISTEMOS_OPERATORIUS
        </div>
        <div className="text-[9px] text-on-surface-variant/50 font-bold uppercase tracking-[0.05rem] font-label">
          LYGIS_04_LEIDIMAS
        </div>
      </div>

      {/* Main navigation */}
      <nav className="flex-1">
        <div className="space-y-1">
          {mainNavItems.map((item) => {
            const active = isActive(item);
            return (
              <Link
                key={item.id}
                href={item.href}
                className={`flex items-center px-4 py-3 font-label text-[11px] font-bold uppercase tracking-[0.05rem] transition-all duration-200 ${
                  active
                    ? "text-primary bg-surface-container-high border-l-4 border-primary"
                    : "text-on-surface-variant/60 hover:bg-surface-container-high hover:text-primary"
                }`}
              >
                <span className="material-symbols-outlined mr-3">
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Bottom section */}
      <div className="mt-auto space-y-1 border-t border-outline-variant/15 pt-4">
        <Link
          href="#"
          className="text-on-surface-variant/60 hover:bg-surface-container-high hover:text-primary flex items-center px-4 py-3 font-label text-[11px] font-bold uppercase tracking-[0.05rem] transition-all duration-200"
        >
          <span className="material-symbols-outlined mr-3">settings</span>
          SISTEMOS BŪSENA
        </Link>
        <Link
          href="#"
          className="text-on-surface-variant/60 hover:bg-surface-container-high hover:text-primary flex items-center px-4 py-3 font-label text-[11px] font-bold uppercase tracking-[0.05rem] transition-all duration-200"
        >
          <span className="material-symbols-outlined mr-3">logout</span>
          ATSIJUNGTI
        </Link>
      </div>
    </aside>
  );
}
