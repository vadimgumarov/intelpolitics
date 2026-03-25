"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import Link from "next/link";

const allPoliticians = [
  { id: 1, name: "Andrius Kubilius", party: "Tėvynės Sąjunga", position: "Europos Komisijos narys", region: "Vilnius", trustScore: 72, rosePoints: "50,12 88,38 78,88 22,88 12,38" },
  { id: 2, name: "Viktorija Čmilytė-Nielsen", party: "Liberalų Sąjūdis", position: "Seimo pirmininkė", region: "Vilnius", trustScore: 84, rosePoints: "50,8 92,32 82,92 18,92 8,32" },
  { id: 3, name: "Ramūnas Karbauskis", party: "LVŽS", position: "Frakcijos seniūnas", region: "Kaunas", trustScore: 31, rosePoints: "50,38 62,48 57,72 43,72 38,48" },
  { id: 4, name: "Gabrielius Landsbergis", party: "Tėvynės Sąjunga", position: "Užsienio reikalų ministras", region: "Vilnius", trustScore: 68, rosePoints: "50,15 82,35 72,85 28,85 18,35" },
  { id: 5, name: "Aušrinė Armonaitė", party: "Laisvės partija", position: "Ekonomikos ministrė", region: "Vilnius", trustScore: 77, rosePoints: "50,10 86,34 76,90 24,90 14,34" },
  { id: 6, name: "Saulius Skvernelis", party: "Demokratų sąjunga", position: "Buvęs ministras pirmininkas", region: "Vilnius", trustScore: 45, rosePoints: "50,28 72,42 66,78 34,78 28,42" },
  { id: 7, name: "Ingrida Šimonytė", party: "Tėvynės Sąjunga", position: "Ministrė pirmininkė", region: "Vilnius", trustScore: 71, rosePoints: "50,14 84,36 74,86 26,86 16,36" },
  { id: 8, name: "Agnė Bilotaitė", party: "Tėvynės Sąjunga", position: "Vidaus reikalų ministrė", region: "Klaipėda", trustScore: 63, rosePoints: "50,18 78,38 70,82 30,82 22,38" },
  { id: 9, name: "Simonas Gentvilas", party: "Liberalų Sąjūdis", position: "Aplinkos ministras", region: "Klaipėda", trustScore: 69, rosePoints: "50,16 80,36 72,84 28,84 20,36" },
  { id: 10, name: "Vilija Blinkevičiūtė", party: "Socialdemokratai", position: "EP narė", region: "Kaunas", trustScore: 74, rosePoints: "50,12 86,36 76,88 24,88 14,36" },
  { id: 11, name: "Gintautas Paluckas", party: "Socialdemokratai", position: "Seimo narys", region: "Vilnius", trustScore: 66, rosePoints: "50,18 76,40 68,80 32,80 24,40" },
  { id: 12, name: "Vytautas Bakas", party: "Mišri grupė", position: "Seimo narys", region: "Šiauliai", trustScore: 42, rosePoints: "50,32 66,46 60,74 40,74 34,46" },
];

const parties = ["VISOS", "Tėvynės Sąjunga", "Liberalų Sąjūdis", "LVŽS", "Laisvės partija", "Demokratų sąjunga", "Socialdemokratai", "Mišri grupė"];
const regions = ["VISI", "Vilnius", "Kaunas", "Klaipėda", "Šiauliai"];
const positions = ["VISOS", "Ministras", "Seimo narys", "EP narys"];

export default function SearchPage() {
  const [search, setSearch] = useState("");
  const [selectedParty, setSelectedParty] = useState("VISOS");
  const [selectedRegion, setSelectedRegion] = useState("VISI");
  const [minScore, setMinScore] = useState(0);
  const [maxScore, setMaxScore] = useState(100);

  const filtered = allPoliticians.filter(p => {
    const matchesSearch = search === "" ||
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.party.toLowerCase().includes(search.toLowerCase()) ||
      p.position.toLowerCase().includes(search.toLowerCase());
    const matchesParty = selectedParty === "VISOS" || p.party === selectedParty;
    const matchesRegion = selectedRegion === "VISI" || p.region === selectedRegion;
    const matchesScore = p.trustScore >= minScore && p.trustScore <= maxScore;
    return matchesSearch && matchesParty && matchesRegion && matchesScore;
  });

  return (
    <AppLayout>
      {/* Header */}
      <div className="p-10 border-b border-outline-variant/10">
        <div className="max-w-7xl mx-auto">
          <h1 className="font-headline text-4xl font-bold tracking-tight text-on-surface uppercase mb-2">
            Paieška ir archyvas
          </h1>
          <p className="font-label text-xs uppercase tracking-widest text-on-surface-variant opacity-60">
            Politikų duomenų bazės paieška // Aktyvūs įrašai: {allPoliticians.length}
          </p>
        </div>
      </div>

      <div className="p-10 max-w-7xl mx-auto">
        {/* Filter Section */}
        <div className="bg-surface-container-low p-6 mb-10">
          <div className="grid grid-cols-12 gap-4 items-end">
            {/* Search */}
            <div className="col-span-4 relative">
              <label className="block font-label text-[10px] uppercase tracking-tighter text-on-surface-variant mb-2">
                Paieškos užklausa
              </label>
              <div className="relative">
                <input
                  className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 pl-10 focus:outline-none focus:border-primary focus:bg-surface-bright transition-all font-mono text-sm"
                  placeholder="VARDAS, PARTIJA, POZICIJA..."
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
              </div>
            </div>

            {/* Party */}
            <div className="col-span-2">
              <label className="block font-label text-[10px] uppercase tracking-tighter text-on-surface-variant mb-2">
                Partija
              </label>
              <select
                className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 px-3 focus:outline-none focus:border-primary font-mono text-xs appearance-none"
                value={selectedParty}
                onChange={e => setSelectedParty(e.target.value)}
              >
                {parties.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            {/* Region */}
            <div className="col-span-2">
              <label className="block font-label text-[10px] uppercase tracking-tighter text-on-surface-variant mb-2">
                Regionas
              </label>
              <select
                className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 px-3 focus:outline-none focus:border-primary font-mono text-xs appearance-none"
                value={selectedRegion}
                onChange={e => setSelectedRegion(e.target.value)}
              >
                {regions.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>

            {/* Trust Score Range */}
            <div className="col-span-2">
              <label className="block font-label text-[10px] uppercase tracking-tighter text-on-surface-variant mb-2">
                Tiesos indeksas (min-max)
              </label>
              <div className="flex gap-2">
                <input
                  className="w-1/2 bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 px-2 focus:outline-none focus:border-primary font-mono text-xs text-center"
                  type="number"
                  min={0}
                  max={100}
                  value={minScore}
                  onChange={e => setMinScore(Number(e.target.value))}
                />
                <input
                  className="w-1/2 bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-3 px-2 focus:outline-none focus:border-primary font-mono text-xs text-center"
                  type="number"
                  min={0}
                  max={100}
                  value={maxScore}
                  onChange={e => setMaxScore(Number(e.target.value))}
                />
              </div>
            </div>

            {/* Reset */}
            <div className="col-span-2">
              <button
                className="w-full bg-surface-bright py-3 font-headline font-bold text-on-surface text-xs uppercase tracking-widest hover:bg-primary-container hover:text-on-primary-container transition-all flex items-center justify-center gap-2"
                onClick={() => { setSearch(""); setSelectedParty("VISOS"); setSelectedRegion("VISI"); setMinScore(0); setMaxScore(100); }}
              >
                <span className="material-symbols-outlined text-sm">restart_alt</span>
                Atstatyti
              </button>
            </div>
          </div>
        </div>

        {/* Results count */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-1.5 h-1.5 bg-primary" />
          <span className="font-label text-[10px] uppercase tracking-widest text-on-surface-variant">
            Rasta rezultatų: {filtered.length}
          </span>
        </div>

        {/* Results Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filtered.map(politician => {
            const isCritical = politician.trustScore < 40;
            const borderColor = isCritical ? "border-tertiary-container" : "border-primary";
            const scoreColor = isCritical ? "text-tertiary" : politician.trustScore < 60 ? "text-on-surface" : "text-primary";
            const roseStroke = isCritical ? "#ff544e" : "#a7c8ff";
            const roseFill = isCritical ? "rgba(255, 84, 78, 0.2)" : "rgba(68, 145, 244, 0.2)";

            return (
              <Link
                key={politician.id}
                href={`/dossier?id=${politician.id}`}
                className={`bg-surface-container-low border-l-2 ${borderColor} group hover:bg-surface-container-high transition-all p-0 block`}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-headline font-bold text-lg text-on-surface leading-tight">{politician.name}</h3>
                      <p className={`font-mono text-[10px] ${isCritical ? "text-tertiary" : "text-primary"} mt-1`}>{politician.party}</p>
                      <p className="font-label text-[9px] text-on-surface-variant mt-0.5">{politician.position}</p>
                    </div>
                    <div className="relative w-14 h-14">
                      <svg className="w-full h-full" viewBox="0 0 100 100">
                        <polygon fill={roseFill} points={politician.rosePoints} stroke={roseStroke} strokeWidth="1.5" />
                        {politician.rosePoints.split(" ").map((point, i) => {
                          const [cx, cy] = point.split(",");
                          return <rect key={i} x={Number(cx) - 2} y={Number(cy) - 2} width="4" height="4" fill={roseStroke} />;
                        })}
                      </svg>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="font-label text-[9px] uppercase text-on-surface-variant">{politician.region}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-label text-[9px] uppercase text-on-surface-variant">Tiesos indeksas</span>
                      <span className={`font-mono text-sm font-bold ${scoreColor}`}>{politician.trustScore}%</span>
                    </div>
                  </div>
                </div>
                <div className="px-6 py-3 border-t border-outline-variant/10 flex items-center justify-between">
                  <span className="font-mono text-[9px] text-on-surface-variant/50">ID: {politician.id.toString().padStart(4, "0")}-X</span>
                  <span className="font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant group-hover:text-primary transition-colors">
                    Atidaryti dosje
                  </span>
                </div>
              </Link>
            );
          })}
        </div>

        {filtered.length === 0 && (
          <div className="bg-surface-container-low/30 border border-dashed border-outline-variant/20 p-16 flex flex-col items-center justify-center gap-4">
            <span className="material-symbols-outlined text-4xl text-outline-variant/50">search_off</span>
            <p className="font-label text-[10px] uppercase tracking-[0.2em] text-outline">Rezultatų nerasta. Patikslinkite paieškos kriterijus.</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="p-10 max-w-7xl mx-auto flex justify-between items-center opacity-40 border-t border-outline-variant/10">
        <div className="flex gap-8 items-center">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary" />
            <span className="font-mono text-[9px] uppercase">Duomenų bazė: Sinchronizuota</span>
          </div>
        </div>
        <div className="font-mono text-[9px] uppercase">
          &copy; 2026 INTEL_POLITIKA.SIS // ARCHYVO_MODULIS
        </div>
      </footer>
    </AppLayout>
  );
}
