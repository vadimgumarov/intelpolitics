"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";

const allPoliticians = [
  { id: 1, name: "Andrius Kubilius", party: "Tėvynės Sąjunga", role: "Europos Komisijos narys", credibility: 72.4, contributions: "€1.2M", sentiment: "+8.4" },
  { id: 2, name: "Viktorija Čmilytė-Nielsen", party: "Liberalų Sąjūdis", role: "Seimo pirmininkė", credibility: 84.2, contributions: "€0.8M", sentiment: "+12.2" },
  { id: 3, name: "Ramūnas Karbauskis", party: "LVŽS", role: "Frakcijos seniūnas", credibility: 31.0, contributions: "€4.1M", sentiment: "-15.8" },
  { id: 4, name: "Gabrielius Landsbergis", party: "Tėvynės Sąjunga", role: "Užsienio reikalų ministras", credibility: 68.1, contributions: "€0.6M", sentiment: "+5.1" },
  { id: 5, name: "Aušrinė Armonaitė", party: "Laisvės partija", role: "Ekonomikos ministrė", credibility: 76.8, contributions: "€0.4M", sentiment: "+9.7" },
  { id: 6, name: "Saulius Skvernelis", party: "Demokratų sąjunga", role: "Buvęs ministras pirmininkas", credibility: 45.3, contributions: "€2.3M", sentiment: "-4.2" },
];

const performanceMatrix = [
  { vector: "Įstatymų efektyvumas", field: "legislative" },
  { vector: "Žiniasklaidos nuotaika", field: "media" },
  { vector: "Išteklių paskirstymas", field: "resources" },
  { vector: "Politikos nuoseklumas", field: "policy" },
  { vector: "Viešasis pasitikėjimas", field: "trust" },
];

// Score data per politician id
const scores: Record<number, Record<string, number>> = {
  1: { legislative: 0.74, media: -0.12, resources: 0.89, policy: 0.55, trust: 0.68 },
  2: { legislative: 0.82, media: 0.68, resources: 0.71, policy: 0.91, trust: 0.84 },
  3: { legislative: 0.22, media: -0.45, resources: 0.81, policy: 0.18, trust: 0.15 },
  4: { legislative: 0.65, media: 0.42, resources: 0.58, policy: 0.72, trust: 0.61 },
  5: { legislative: 0.71, media: 0.55, resources: 0.62, policy: 0.78, trust: 0.74 },
  6: { legislative: 0.48, media: -0.22, resources: 0.72, policy: 0.35, trust: 0.38 },
};

// Rose polygon points per politician
const rosePoints: Record<number, string> = {
  1: "50,15 80,35 75,70 50,85 20,65 25,30",
  2: "50,10 85,30 80,75 50,90 15,70 20,25",
  3: "50,42 60,48 58,68 50,72 42,65 40,50",
  4: "50,20 75,38 70,72 50,82 25,68 30,35",
  5: "50,14 82,32 76,74 50,88 18,72 22,28",
  6: "50,30 68,42 65,70 50,78 32,68 35,40",
};

export default function ComparePage() {
  const [leftId, setLeftId] = useState(2);
  const [rightId, setRightId] = useState(3);

  const leftPol = allPoliticians.find(p => p.id === leftId)!;
  const rightPol = allPoliticians.find(p => p.id === rightId)!;
  const leftScores = scores[leftId];
  const rightScores = scores[rightId];
  const leftRose = rosePoints[leftId];
  const rightRose = rosePoints[rightId];

  return (
    <AppLayout>
      {/* Header Section */}
      <div className="p-8 border-b border-outline-variant/10">
        <div className="flex justify-between items-end max-w-7xl mx-auto">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 bg-primary" />
              <span className="text-on-surface-variant font-label text-[10px] uppercase tracking-[0.2em]">
                Gyva analizė / Sesijos ID: 992-XPL
              </span>
            </div>
            <h1 className="font-headline text-4xl font-bold tracking-tight text-on-surface uppercase">
              Palyginimo valdymo centras
            </h1>
          </div>
          <div className="flex gap-4">
            <button className="bg-surface-bright text-on-surface px-6 py-2 text-xs font-bold uppercase tracking-wider hover:bg-primary-container transition-all">
              Eksportuoti dosje
            </button>
            <button className="bg-primary-container text-on-primary-container px-6 py-2 text-xs font-bold uppercase tracking-wider hover:brightness-110 transition-all">
              Generuoti santrauką
            </button>
          </div>
        </div>
      </div>

      <div className="p-8 max-w-7xl mx-auto">
        {/* Comparison Grid */}
        <div className="grid grid-cols-12 gap-6 items-start">
          {/* Left Candidate */}
          <div className="col-span-3 space-y-8">
            <div className="bg-surface-container-low p-6 border-l-4 border-primary">
              {/* Selector */}
              <div className="mb-4">
                <label className="block font-label text-[9px] uppercase text-on-surface-variant tracking-widest mb-2">Pasirinkti subjektą A</label>
                <select
                  className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-2 px-3 focus:outline-none focus:border-primary font-mono text-xs appearance-none"
                  value={leftId}
                  onChange={e => setLeftId(Number(e.target.value))}
                >
                  {allPoliticians.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              {/* Photo placeholder */}
              <div className="relative w-full aspect-square mb-6 bg-surface-container-high overflow-hidden">
                <div className="w-full h-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, #0d1a2d 0%, #111a2e 50%, #111417 100%)" }}>
                  <span className="material-symbols-outlined text-6xl text-on-surface-variant/15">person</span>
                </div>
                <div className="absolute inset-0 bg-primary/5" />
              </div>
              <div className="font-headline font-bold text-2xl mb-1 uppercase text-primary">{leftPol.name}</div>
              <div className="font-label text-[10px] text-on-surface-variant uppercase tracking-widest mb-4">{leftPol.role}</div>
              <div className="space-y-2">
                <div className="flex justify-between text-[11px] uppercase tracking-tighter">
                  <span className="text-on-surface-variant">Patikimumo reitingas</span>
                  <span className="text-primary">{leftPol.credibility}%</span>
                </div>
                <div className="w-full h-0.5 bg-surface-variant">
                  <div className="h-full bg-primary" style={{ width: `${leftPol.credibility}%` }} />
                </div>
              </div>
            </div>
            <div className="space-y-4">
              <h3 className="font-headline text-xs font-bold uppercase text-on-surface-variant tracking-[0.1em]">Pagrindiniai rodikliai</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-surface-container-low p-3">
                  <div className="text-[9px] text-on-surface-variant uppercase mb-1">Bendri įnašai</div>
                  <div className="text-lg font-headline font-bold text-primary">{leftPol.contributions}</div>
                </div>
                <div className="bg-surface-container-low p-3">
                  <div className="text-[9px] text-on-surface-variant uppercase mb-1">Rinkėjų nuotaika</div>
                  <div className="text-lg font-headline font-bold text-primary">{leftPol.sentiment}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Central Visual Engine: Truthfulness Rose */}
          <div className="col-span-6 relative aspect-square flex items-center justify-center">
            {/* Grid background */}
            <div className="absolute inset-0 opacity-10 pointer-events-none" style={{
              backgroundImage: "radial-gradient(circle at center, #414752 1px, transparent 1px), linear-gradient(to right, #414752 1px, transparent 1px), linear-gradient(to bottom, #414752 1px, transparent 1px)",
              backgroundSize: "40px 40px"
            }} />

            <div className="relative w-[85%] h-[85%] flex items-center justify-center">
              <svg className="absolute w-full h-full" viewBox="0 0 100 100">
                {/* Background circles */}
                <circle cx="50" cy="50" r="48" fill="none" stroke="#414752" strokeDasharray="1 2" strokeWidth="0.25" />
                <circle cx="50" cy="50" r="36" fill="none" stroke="#414752" strokeDasharray="1 2" strokeWidth="0.25" />
                <circle cx="50" cy="50" r="24" fill="none" stroke="#414752" strokeDasharray="1 2" strokeWidth="0.25" />
                <circle cx="50" cy="50" r="12" fill="none" stroke="#414752" strokeDasharray="1 2" strokeWidth="0.25" />
                <path d="M50 2 L50 98 M2 50 L98 50 M15.5 15.5 L84.5 84.5 M84.5 15.5 L15.5 84.5" stroke="#414752" strokeWidth="0.1" />
                {/* Candidate A */}
                <polygon fill="rgba(167, 200, 255, 0.15)" points={leftRose} stroke="#A7C8FF" strokeWidth="1.5" />
                {/* Candidate B */}
                <polygon fill="rgba(255, 179, 173, 0.15)" points={rightRose} stroke="#FFB3AD" strokeWidth="1.5" />
              </svg>

              {/* Labels */}
              <span className="absolute top-0 text-[10px] font-bold uppercase text-on-surface-variant tracking-widest">Nuoseklumas</span>
              <span className="absolute right-0 text-[10px] font-bold uppercase text-on-surface-variant tracking-widest rotate-90 translate-x-12">Skaidrumas</span>
              <span className="absolute bottom-0 text-[10px] font-bold uppercase text-on-surface-variant tracking-widest">Faktų patikra</span>
              <span className="absolute left-0 text-[10px] font-bold uppercase text-on-surface-variant tracking-widest -rotate-90 -translate-x-12">Retorika</span>

              <div className="text-center z-10 pointer-events-none">
                <div className="font-headline text-5xl font-bold tracking-tighter text-on-surface">ROŽĖ_01</div>
                <div className="text-[9px] uppercase tracking-[0.4em] text-on-surface-variant">Analitinis persidengimas</div>
              </div>
            </div>

            {/* Floating data node */}
            <div className="absolute top-10 right-10 flex flex-col items-end">
              <div className="w-12 h-[1px] bg-primary mb-2" />
              <span className="text-[9px] text-primary uppercase font-bold">Mazgo konfliktas: 78.4</span>
            </div>
          </div>

          {/* Right Candidate */}
          <div className="col-span-3 space-y-8">
            <div className="bg-surface-container-low p-6 border-r-4 border-tertiary">
              {/* Selector */}
              <div className="mb-4">
                <label className="block font-label text-[9px] uppercase text-on-surface-variant tracking-widest mb-2">Pasirinkti subjektą B</label>
                <select
                  className="w-full bg-surface-container-high border-b border-outline-variant/30 text-on-surface py-2 px-3 focus:outline-none focus:border-primary font-mono text-xs appearance-none"
                  value={rightId}
                  onChange={e => setRightId(Number(e.target.value))}
                >
                  {allPoliticians.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              {/* Photo placeholder */}
              <div className="relative w-full aspect-square mb-6 bg-surface-container-high overflow-hidden">
                <div className="w-full h-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, #2a1215 0%, #1a0a0b 50%, #111417 100%)" }}>
                  <span className="material-symbols-outlined text-6xl text-on-surface-variant/15">person</span>
                </div>
                <div className="absolute inset-0 bg-tertiary/5" />
              </div>
              <div className="font-headline font-bold text-2xl mb-1 uppercase text-tertiary">{rightPol.name}</div>
              <div className="font-label text-[10px] text-on-surface-variant uppercase tracking-widest mb-4">{rightPol.role}</div>
              <div className="space-y-2">
                <div className="flex justify-between text-[11px] uppercase tracking-tighter">
                  <span className="text-on-surface-variant">Patikimumo reitingas</span>
                  <span className="text-tertiary">{rightPol.credibility}%</span>
                </div>
                <div className="w-full h-0.5 bg-surface-variant">
                  <div className="h-full bg-tertiary" style={{ width: `${rightPol.credibility}%` }} />
                </div>
              </div>
            </div>
            <div className="space-y-4 text-right">
              <h3 className="font-headline text-xs font-bold uppercase text-on-surface-variant tracking-[0.1em]">Pagrindiniai rodikliai</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-surface-container-low p-3">
                  <div className="text-[9px] text-on-surface-variant uppercase mb-1">Bendri įnašai</div>
                  <div className="text-lg font-headline font-bold text-tertiary">{rightPol.contributions}</div>
                </div>
                <div className="bg-surface-container-low p-3">
                  <div className="text-[9px] text-on-surface-variant uppercase mb-1">Rinkėjų nuotaika</div>
                  <div className="text-lg font-headline font-bold text-tertiary">{rightPol.sentiment}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Network Collision */}
          <div className="col-span-4 bg-surface-container-low p-6">
            <div className="flex items-center justify-between mb-8">
              <h4 className="font-headline text-xs font-bold uppercase tracking-widest text-on-surface">Tinklo susidūrimas</h4>
              <span className="material-symbols-outlined text-primary text-sm">hub</span>
            </div>
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="flex-1 bg-surface-container-highest h-4 relative">
                  <div className="absolute right-0 top-0 bottom-0 w-[45%] bg-primary opacity-30" />
                  <div className="absolute left-0 top-0 bottom-0 w-[45%] bg-tertiary opacity-30" />
                  <div className="absolute left-[40%] right-[40%] top-0 bottom-0 bg-secondary z-10" />
                </div>
                <span className="text-[10px] font-bold w-12 text-on-surface">22.4%</span>
              </div>
              <div className="text-[9px] text-on-surface-variant uppercase tracking-wider leading-relaxed">
                Reikšmingas donorų persidengimas aptiktas <span className="text-on-surface">nekilnojamojo turto</span> ir <span className="text-on-surface">finansinių technologijų</span> sektoriuose. Kryžminė paieška atskleidžia 14 bendrų subjektų identifikatorių tarp dosje.
              </div>
              <div className="grid grid-cols-3 gap-1 pt-4 border-t border-outline-variant/15">
                <div className="h-1 bg-primary" />
                <div className="h-1 bg-secondary" />
                <div className="h-1 bg-tertiary" />
              </div>
            </div>
          </div>

          {/* Performance Matrix Table */}
          <div className="col-span-8 bg-surface-container-low p-6">
            <div className="flex items-center justify-between mb-8">
              <h4 className="font-headline text-xs font-bold uppercase tracking-widest text-on-surface">Veiklos matrica</h4>
              <div className="flex gap-4 text-[9px] uppercase font-bold tracking-widest">
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-primary" /> {leftPol.name.split(" ").pop()}</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-tertiary" /> {rightPol.name.split(" ").pop()}</span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[11px] font-body">
                <thead>
                  <tr className="border-b border-outline-variant/20 uppercase tracking-widest text-on-surface-variant">
                    <th className="py-3 font-normal">Vektorius</th>
                    <th className="py-3 font-normal">A_Signalas</th>
                    <th className="py-3 font-normal">B_Signalas</th>
                    <th className="py-3 font-normal">Delta</th>
                    <th className="py-3 font-normal text-right">Pasitikėjimas</th>
                  </tr>
                </thead>
                <tbody className="text-on-surface">
                  {performanceMatrix.map((row, i) => {
                    const a = leftScores[row.field];
                    const b = rightScores[row.field];
                    const delta = (a - b).toFixed(2);
                    const confidence = (85 + Math.random() * 15).toFixed(1);
                    return (
                      <tr key={i} className="border-b border-outline-variant/10">
                        <td className="py-4 font-bold uppercase text-[10px]">{row.vector}</td>
                        <td className="py-4 text-primary">{a.toFixed(2)}</td>
                        <td className="py-4 text-tertiary">{b.toFixed(2)}</td>
                        <td className="py-4">{Number(delta) >= 0 ? "+" : ""}{delta}</td>
                        <td className="py-4 text-right">{confidence}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* System Logs Footer */}
        <div className="mt-12 flex justify-between items-center border-t border-outline-variant/15 pt-6">
          <div className="flex gap-8">
            <div className="flex flex-col">
              <span className="text-[9px] uppercase text-on-surface-variant mb-1 tracking-widest">Apdorojimo greitis</span>
              <span className="text-xs font-mono text-primary">14.2 teraflops/s</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] uppercase text-on-surface-variant mb-1 tracking-widest">Duomenų šaltiniai</span>
              <span className="text-xs font-mono text-primary">8 412 aktyvių srautų</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-primary animate-pulse" />
            <span className="text-[10px] font-bold uppercase text-on-surface tracking-[0.2em]">Visos sistemos nominalios // Archyvas sinchronizuotas</span>
          </div>
        </div>
      </div>

      {/* Ghost Lines */}
      <div className="fixed top-[20%] right-10 w-[1px] h-32 bg-outline-variant/20 pointer-events-none" />
      <div className="fixed bottom-10 left-[20rem] h-[1px] w-48 bg-outline-variant/20 pointer-events-none" />
      <div className="fixed top-20 right-20 w-8 h-8 border border-outline-variant/20 pointer-events-none" />
    </AppLayout>
  );
}
