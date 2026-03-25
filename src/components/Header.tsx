"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "SKYDELIS", href: "/" },
  { label: "DOSJE", href: "/dossier" },
  { label: "TIESOS INDEKSAS", href: "/truthfulness" },
  { label: "PALYGINIMAS", href: "/compare" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-6 h-14 bg-surface border-b border-outline-variant/15">
      <div className="flex items-center gap-8">
        <Link
          href="/"
          className="text-xl font-bold tracking-tighter text-primary font-headline uppercase"
        >
          INTEL_POLITIKA
        </Link>
        <nav className="hidden md:flex gap-6 items-center h-full">
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`font-headline tracking-tight text-sm uppercase h-14 flex items-center px-2 transition-colors duration-150 ${
                  isActive
                    ? "text-primary border-b-2 border-primary"
                    : "text-on-surface-variant hover:bg-surface-bright"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="flex items-center gap-1">
        <button className="p-2 text-primary hover:bg-surface-bright transition-colors duration-150">
          <span className="material-symbols-outlined">sensors</span>
        </button>
        <button className="p-2 text-primary hover:bg-surface-bright transition-colors duration-150">
          <span className="material-symbols-outlined">security</span>
        </button>
        <button className="p-2 text-primary hover:bg-surface-bright transition-colors duration-150 relative">
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-tertiary-container" />
        </button>
        <button className="p-2 text-primary hover:bg-surface-bright transition-colors duration-150">
          <span className="material-symbols-outlined">account_circle</span>
        </button>
      </div>
    </header>
  );
}
