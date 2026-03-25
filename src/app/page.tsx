"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import Link from "next/link";

const politicians = [
  {
    id: 1,
    name: "Andrius Kubilius",
    party: "TĖVYNĖS SĄJUNGA",
    role: "Europos Komisijos narys",
    trustScore: 72,
    funding: "€1.2M",
    status: "active" as const,
    rosePoints: "50,12 88,38 78,88 22,88 12,38",
  },
  {
    id: 2,
    name: "Viktorija Čmilytė-Nielsen",
    party: "LIBERALŲ SĄJŪDIS",
    role: "Seimo pirmininkė",
    trustScore: 84,
    funding: "€0.8M",
    status: "active" as const,
    rosePoints: "50,8 92,32 82,92 18,92 8,32",
  },
  {
    id: 3,
    name: "Ramūnas Karbauskis",
    party: "LVŽS",
    role: "Frakcijos seniūnas",
    trustScore: 31,
    funding: "€4.1M",
    status: "critical" as const,
    rosePoints: "50,38 62,48 57,72 43,72 38,48",
  },
  {
    id: 4,
    name: "Gabrielius Landsbergis",
    party: "TĖVYNĖS SĄJUNGA",
    role: "Užsienio reikalų ministras",
    trustScore: 68,
    funding: "€0.6M",
    status: "active" as const,
    rosePoints: "50,15 82,35 72,85 28,85 18,35",
  },
];

const activityFeed = [
  {
    time: "Prieš 2 val.",
    text: "Naujas balsavimo įrašas aptiktas: Energetikos reforma Nr. 447",
    type: "info",
  },
  {
    time: "Prieš 4 val.",
    text: `Kritinis nukrypimas: Lobizmo ryšiai su \u201EEnergijos grup\u0117\u201C patvirtinti`,
    type: "critical",
  },
  {
    time: "Prieš 6 val.",
    text: "Tiesos indeksas atnaujintas 3 politikams pagal naujus duomenis",
    type: "info",
  },
  {
    time: "Vakar",
    text: "Naujas pareiškimas užfiksuotas iš Seimo posėdžio stenogramos",
    type: "info",
  },
];

export default function Home() {
  const [search, setSearch] = useState("");

  const filtered = politicians.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.party.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout>
      {/* Dashboard Header / Search Area */}
      <section className="p-10 border-b border-outline-variant/10">
        <div className="flex flex-col gap-8 max-w-7xl mx-auto">
          <div className="flex justify-between items-end">
            <div>
              <h1 className="font-headline text-4xl font-bold tracking-tight text-on-surface uppercase">
                Žvalgybos centras
              </h1>
              <p className="font-label text-xs uppercase tracking-widest text-on-surface-variant mt-2 opacity-60">
                Realaus laiko politinio integralumo stebėjimas // Būsena:
                Aktyvi
              </p>
            </div>
            <div className="text-right">
              <span className="font-mono text-[10px] text-primary">
                SKENAVIMO_DELSA: 0.002MS
              </span>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-3 gap-0 bg-surface-container-low">
            <div className="p-6 border-r border-outline-variant/15">
              <div className="text-[9px] font-label uppercase text-on-surface-variant tracking-widest mb-2">
                Stebimų politikų skaičius
              </div>
              <div className="text-3xl font-headline font-bold text-primary">
                141
              </div>
            </div>
            <div className="p-6 border-r border-outline-variant/15">
              <div className="text-[9px] font-label uppercase text-on-surface-variant tracking-widest mb-2">
                Aktyvūs tyrimai
              </div>
              <div className="text-3xl font-headline font-bold text-primary">
                23
              </div>
            </div>
            <div className="p-6">
              <div className="text-[9px] font-label uppercase text-on-surface-variant tracking-widest mb-2">
                Tiesos indekso vidurkis
              </div>
              <div className="text-3xl font-headline font-bold text-tertiary">
                54.2%
              </div>
            </div>
          </div>

          {/* Dense Filter Grid */}
          <div className="grid grid-cols-12 gap-4 items-end bg-surface-container-low p-6">
            <div className="col-span-4 relative">
              <label className="block font-label text-[10px] uppercase tracking-tighter text-on-surface-variant mb-2">
                Subjekto paieška
              </label>
              <div className="relative">
                <input
                  className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 pl-10 focus:outline-none focus:border-primary focus:bg-surface-bright transition-all font-mono text-sm"
                  placeholder="ĮVESKITE VARDĄ ARBA ID..."
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
                  search
                </span>
              </div>
            </div>
            <div className="col-span-2">
              <label className="block font-label text-[10px] uppercase tracking-tighter text-on-surface-variant mb-2">
                Regionas
              </label>
              <select className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 px-3 focus:outline-none focus:border-primary font-mono text-xs appearance-none">
                <option>VISA_LIETUVA</option>
                <option>VILNIAUS_APSKR</option>
                <option>KAUNO_APSKR</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="block font-label text-[10px] uppercase tracking-tighter text-on-surface-variant mb-2">
                Partija
              </label>
              <select className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 px-3 focus:outline-none focus:border-primary font-mono text-xs appearance-none">
                <option>VISOS_PARTIJOS</option>
                <option>TĖVYNĖS_SĄJUNGA</option>
                <option>SOCIALDEMOKRATAI</option>
                <option>LIBERALAI</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="block font-label text-[10px] uppercase tracking-tighter text-on-surface-variant mb-2">
                Kadencija
              </label>
              <select className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 px-3 focus:outline-none focus:border-primary font-mono text-xs appearance-none">
                <option>2024_AKTYVUS</option>
                <option>2020_ARCHYVAS</option>
              </select>
            </div>
            <div className="col-span-2">
              <Link
                href="/search"
                className="w-full bg-primary py-3 font-headline font-bold text-on-primary-container text-xs uppercase tracking-widest hover:bg-surface-bright hover:text-on-surface transition-all flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-sm">
                  filter_list
                </span>
                Filtruoti
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Results Grid */}
      <section className="p-10 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
          {filtered.map((politician) => {
            const isCritical = politician.status === "critical";
            const borderColor = isCritical
              ? "border-tertiary-container"
              : "border-primary";
            const scoreColor = isCritical ? "text-tertiary" : "text-primary";
            const roseStroke = isCritical ? "#ff544e" : "#a7c8ff";
            const roseFill = isCritical
              ? "rgba(255, 84, 78, 0.2)"
              : "rgba(68, 145, 244, 0.2)";

            return (
              <div
                key={politician.id}
                className={`bg-surface-container-low border-l-2 ${borderColor} group hover:bg-surface-container-high transition-all p-0`}
              >
                <div className="flex">
                  {/* Photo placeholder with gradient */}
                  <div className="w-32 h-40 bg-surface-container-highest relative overflow-hidden">
                    <div
                      className="w-full h-full"
                      style={{
                        background: isCritical
                          ? "linear-gradient(135deg, #2a1215 0%, #1a0a0b 50%, #111417 100%)"
                          : "linear-gradient(135deg, #0d1a2d 0%, #111a2e 50%, #111417 100%)",
                      }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="material-symbols-outlined text-4xl text-on-surface-variant/20">
                        person
                      </span>
                    </div>
                    <div
                      className={`absolute bottom-0 left-0 ${isCritical ? "bg-tertiary-container text-on-tertiary" : "bg-primary/90 text-on-primary-container"} font-mono text-[9px] px-2 py-0.5`}
                    >
                      ID: {politician.id.toString().padStart(4, "0")}-X
                    </div>
                  </div>
                  <div className="flex-1 p-6 flex flex-col justify-between">
                    <div>
                      <h3 className="font-headline font-bold text-xl text-on-surface leading-tight">
                        {politician.name}
                      </h3>
                      <p
                        className={`font-mono text-[10px] ${isCritical ? "text-tertiary" : "text-primary"} mt-1`}
                      >
                        PARTIJA: {politician.party}
                      </p>
                      <p className="font-label text-[9px] text-on-surface-variant mt-0.5">
                        {politician.role}
                      </p>
                    </div>
                    <div className="flex gap-4 mt-4">
                      <div>
                        <p className="font-label text-[9px] uppercase text-on-surface-variant">
                          Finansavimas
                        </p>
                        <p className="font-mono text-sm font-bold">
                          {politician.funding}
                        </p>
                      </div>
                      <div className="h-8 w-px bg-outline-variant/20" />
                      <div>
                        <p className="font-label text-[9px] uppercase text-on-surface-variant">
                          Tiesos indeksas
                        </p>
                        <p className={`font-mono text-sm font-bold ${scoreColor}`}>
                          {politician.trustScore}%
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-6 border-t border-outline-variant/10 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="relative w-16 h-16">
                      <svg
                        className={`w-full h-full ${!isCritical ? "drop-shadow-[0_0_8px_rgba(167,200,255,0.3)]" : ""}`}
                        viewBox="0 0 100 100"
                      >
                        <polygon
                          fill={roseFill}
                          points={politician.rosePoints}
                          stroke={roseStroke}
                          strokeWidth="1.5"
                        />
                        {politician.rosePoints.split(" ").map((point, i) => {
                          const [cx, cy] = point.split(",");
                          return (
                            <rect
                              key={i}
                              x={Number(cx) - 2}
                              y={Number(cy) - 2}
                              width="4"
                              height="4"
                              fill={roseStroke}
                            />
                          );
                        })}
                      </svg>
                    </div>
                    <span
                      className={`font-label text-[10px] uppercase tracking-widest ${isCritical ? "text-tertiary" : "text-on-surface-variant"}`}
                    >
                      {isCritical ? "Kritinė anomalija" : "Tiesos rožė"}
                    </span>
                  </div>
                  <Link
                    href={`/dossier?id=${politician.id}`}
                    className={`${isCritical ? "bg-tertiary-container text-on-tertiary" : "bg-surface-bright text-on-surface"} px-4 py-2 font-label text-[10px] font-bold uppercase tracking-widest border-b border-transparent hover:border-primary transition-all`}
                  >
                    {isCritical ? "Tirti" : "Pilnas dosje"}
                  </Link>
                </div>
              </div>
            );
          })}

          {/* Empty State / Add */}
          <div className="bg-surface-container-low/30 border border-dashed border-outline-variant/20 p-8 flex flex-col items-center justify-center gap-4 group cursor-pointer hover:border-primary/50 transition-all">
            <span className="material-symbols-outlined text-4xl text-outline-variant/50 group-hover:text-primary transition-all">
              add_circle
            </span>
            <p className="font-label text-[10px] uppercase tracking-[0.2em] text-outline group-hover:text-primary">
              Inicijuoti naują dosje
            </p>
          </div>
        </div>
      </section>

      {/* Activity Feed */}
      <section className="p-10 max-w-7xl mx-auto">
        <div className="bg-surface-container-low p-8">
          <h3 className="font-headline text-xs font-bold uppercase tracking-widest mb-6 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-primary animate-pulse" />
            Paskutiniai žvalgybos atnaujinimai
          </h3>
          <div className="space-y-4">
            {activityFeed.map((item, i) => (
              <div
                key={i}
                className={`flex items-start gap-4 p-4 ${item.type === "critical" ? "bg-tertiary-container/5 border-l-2 border-tertiary-container" : "bg-surface-container-high/30 border-l-2 border-primary/30"} hover:bg-surface-bright/20 transition-colors cursor-pointer`}
              >
                <div className="flex items-center gap-2 min-w-[100px]">
                  <div
                    className={`w-1.5 h-1.5 ${item.type === "critical" ? "bg-tertiary-container" : "bg-primary"}`}
                  />
                  <span className="font-mono text-[9px] text-on-surface-variant uppercase">
                    {item.time}
                  </span>
                </div>
                <p className="text-[11px] font-label text-on-surface leading-relaxed">
                  {item.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technical Metadata Footer */}
      <footer className="p-10 max-w-7xl mx-auto flex justify-between items-center opacity-40">
        <div className="flex gap-8 items-center">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary" />
            <span className="font-mono text-[9px] uppercase">
              Ryšys: Saugus_Protokolas_44
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary" />
            <span className="font-mono text-[9px] uppercase">
              Aktyvūs mazgai: 14 902
            </span>
          </div>
        </div>
        <div className="font-mono text-[9px] uppercase">
          &copy; 2026 INTEL_POLITIKA.SIS // PRIEIGOS_TAŠKAS_CENTRAS_ALFA
        </div>
      </footer>
    </AppLayout>
  );
}
