"use client";

import Header from "./Header";
import Sidebar from "./Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header />
      <Sidebar />
      <main className="ml-64 mt-14 h-[calc(100vh-3.5rem)] overflow-y-auto bg-surface relative">
        {children}
        {/* Ghost decoration lines */}
        <div className="absolute top-0 right-10 w-px h-full bg-outline-variant/5 pointer-events-none" />
        <div className="absolute bottom-40 left-0 w-full h-px bg-outline-variant/5 pointer-events-none" />
      </main>
      {/* Floating system status */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2 pointer-events-none">
        <div className="glass px-3 py-1 flex items-center gap-3 border-l-2 border-primary">
          <div className="w-1 h-1 bg-primary animate-pulse" />
          <span className="font-mono text-[10px] text-on-surface uppercase tracking-tight">
            Sistema nominali
          </span>
        </div>
      </div>
    </>
  );
}
