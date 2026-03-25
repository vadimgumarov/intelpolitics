"use client";

import AppLayout from "@/components/AppLayout";

const categoryBreakdown = [
  { name: "Ekonominis_Integralumas", score: 0.88, change: "+1.2%", changeColor: "text-primary", variance: "Žema", lastVerified: "2024.05.22_12:30" },
  { name: "Socialinis_Nuoseklumas", score: 0.65, change: "-0.8%", changeColor: "text-tertiary-container", variance: "Vidutinė", lastVerified: "2024.05.22_13:15" },
  { name: "Saugumo_Patikra", score: 0.22, change: "-15.4%", changeColor: "text-tertiary-container", variance: "KRITINĖ", lastVerified: "2024.05.22_13:45", critical: true },
  { name: "Politinis_Svoris", score: 0.45, change: "+4.5%", changeColor: "text-primary", variance: "Aukšta", lastVerified: "2024.05.21_18:00" },
  { name: "Švietimo_Politika", score: 0.73, change: "+2.1%", changeColor: "text-primary", variance: "Žema", lastVerified: "2024.05.20_09:00" },
  { name: "Sveikatos_Sektorius", score: 0.56, change: "-3.2%", changeColor: "text-tertiary-container", variance: "Vidutinė", lastVerified: "2024.05.19_14:30" },
];

const statementsTable = [
  { date: "2024-11-15", statement: "\u201EBVP augimas vir\u0161ijo 4% \u0161\u012F ketvirt\u012F.\u201C", verdict: "TIESA", source: "Seimo posėdis", verdictColor: "text-primary bg-primary/10" },
  { date: "2024-11-10", statement: "\u201EBedarbyst\u0117 pasiek\u0117 istorin\u012F minimum\u0105.\u201C", verdict: "KLAIDINGA", source: "Spaudos konferencija", verdictColor: "text-tertiary bg-tertiary-container/10" },
  { date: "2024-10-28", statement: "\u201EInvesticijos \u012F moksl\u0105 padid\u0117jo dvigubai.\u201C", verdict: "NEPATVIRTINTA", source: "Interviu LRT", verdictColor: "text-on-surface-variant bg-surface-bright" },
  { date: "2024-10-15", statement: "\u201EGynybos biud\u017Eetas atitinka 2.5% BVP.\u201C", verdict: "TIESA", source: "NATO ataskaita", verdictColor: "text-primary bg-primary/10" },
  { date: "2024-09-30", statement: "\u201EEmigracija suma\u017E\u0117jo 30% per metus.\u201C", verdict: "KLAIDINGA", source: "Vie\u0161as parei\u0161kimas", verdictColor: "text-tertiary bg-tertiary-container/10" },
  { date: "2024-09-15", statement: "\u201EKorupcijos lygis \u017Eemiausias regione.\u201C", verdict: "NEPATVIRTINTA", source: "Seimo debatai", verdictColor: "text-on-surface-variant bg-surface-bright" },
];

const trendData = [
  { month: "SAU", value: 72 },
  { month: "VAS", value: 68 },
  { month: "KOV", value: 74 },
  { month: "BAL", value: 61 },
  { month: "GEG", value: 58 },
  { month: "BIR", value: 65 },
  { month: "LIE", value: 52 },
  { month: "RGP", value: 48 },
  { month: "RGS", value: 55 },
  { month: "SPL", value: 44 },
  { month: "LAP", value: 42 },
  { month: "GRD", value: 38 },
];

const evidenceNodes = [
  { name: "Ekonominis_Srautas_A1", hash: "44F9...A221" },
  { name: "Socialinis_Sentimentas_Gamma", hash: "881E...330B" },
  { name: "Politinis_Pulsas_Pirminis", hash: "22C0...990F" },
];

export default function TruthfulnessPage() {
  const maxTrend = Math.max(...trendData.map(d => d.value));

  return (
    <AppLayout>
      {/* Header Section */}
      <div className="p-10 border-b border-outline-variant/10">
        <div className="flex justify-between items-end max-w-7xl mx-auto">
          <div>
            <h1 className="font-headline text-5xl font-bold tracking-tight mb-2 uppercase">
              Subjektas: 0042_ALGORITMO_AIDAS
            </h1>
            <p className="font-label text-xs tracking-widest text-on-surface-variant uppercase">
              Analizės laiko žyma: 2024.05.22 // 14:00:00 UTC
            </p>
          </div>
          <div className="flex gap-4">
            <button className="bg-surface-bright text-on-surface px-6 py-2 font-label text-xs font-bold uppercase tracking-widest hover:bg-primary-container transition-all">
              Eksportuoti_Ataskaitą
            </button>
            <button className="border border-outline-variant/30 text-on-surface px-6 py-2 font-label text-xs font-bold uppercase tracking-widest hover:bg-surface-bright transition-all">
              Pakartotinai_Patikrinti
            </button>
          </div>
        </div>
      </div>

      <div className="p-10 max-w-7xl mx-auto">
        <div className="grid grid-cols-12 gap-10">
          {/* Truthfulness Rose Module */}
          <div className="col-span-12 lg:col-span-7 bg-surface-container-low p-10 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 font-label text-[10px] text-primary/40 uppercase">
              Interaktyvi_Vizualizacija_v2.4
            </div>
            <h2 className="font-headline text-xl mb-12 flex items-center gap-2">
              <span className="w-2 h-2 bg-primary" />
              TIESOS_ROŽĖS_MODELIS
            </h2>
            <div className="relative aspect-square flex items-center justify-center truthfulness-rose-bg">
              {/* Spider web grid rings */}
              <div className="absolute inset-0 border border-outline-variant/10 rounded-full scale-[0.2]" />
              <div className="absolute inset-0 border border-outline-variant/10 rounded-full scale-[0.4]" />
              <div className="absolute inset-0 border border-outline-variant/10 rounded-full scale-[0.6]" />
              <div className="absolute inset-0 border border-outline-variant/10 rounded-full scale-[0.8]" />
              <div className="absolute inset-0 border border-outline-variant/10 rounded-full scale-[1]" />
              {/* Structural axis lines */}
              <div className="absolute w-full h-[1px] bg-outline-variant/10" />
              <div className="absolute h-full w-[1px] bg-outline-variant/10" />
              <div className="absolute w-full h-[1px] bg-outline-variant/10 rotate-45" />
              <div className="absolute w-full h-[1px] bg-outline-variant/10 -rotate-45" />

              {/* The Radar Shape */}
              <svg className="w-full h-full relative z-10 drop-shadow-[0_0_15px_rgba(167,200,255,0.15)]" viewBox="0 0 100 100">
                <polygon
                  className="fill-primary-container/20 stroke-primary"
                  strokeWidth="0.5"
                  points="50,15 80,30 90,50 75,80 50,90 20,70 10,40 30,20"
                />
                {/* Vertex nodes */}
                {[
                  [48.5, 13.5], [78.5, 28.5], [88.5, 48.5], [73.5, 78.5],
                  [48.5, 88.5], [18.5, 68.5], [8.5, 38.5], [28.5, 18.5]
                ].map(([x, y], i) => (
                  <rect key={i} className="fill-primary" x={x} y={y} width="3" height="3" />
                ))}
              </svg>

              {/* Axis Labels */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-6 font-label text-[10px] tracking-tighter uppercase font-bold text-on-surface-variant">Ekonomika [88%]</div>
              <div className="absolute top-1/4 right-0 translate-x-1/2 font-label text-[10px] tracking-tighter uppercase font-bold text-on-surface-variant">Socialinė [65%]</div>
              <div className="absolute bottom-1/4 right-0 translate-x-1/2 font-label text-[10px] tracking-tighter uppercase font-bold text-on-surface-variant text-tertiary-container">Saugumas [22%]</div>
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-6 font-label text-[10px] tracking-tighter uppercase font-bold text-on-surface-variant">Politinė [45%]</div>
              <div className="absolute bottom-1/4 left-0 -translate-x-1/2 font-label text-[10px] tracking-tighter uppercase font-bold text-on-surface-variant">Etinė [72%]</div>
            </div>

            {/* Live feed ticker */}
            <div className="mt-16 border-t border-outline-variant/10 pt-6 flex justify-between">
              <div className="flex items-center gap-4">
                <div className="w-1.5 h-1.5 bg-primary animate-pulse" />
                <span className="font-label text-[10px] uppercase tracking-widest">Realaus laiko delta sekimas įjungtas</span>
              </div>
              <span className="font-label text-[10px] font-mono text-outline-variant">PAGRINDINIS_INTEGRALUMAS: 74.2%</span>
            </div>
          </div>

          {/* Analysis Sidebar & Alerts */}
          <div className="col-span-12 lg:col-span-5 space-y-10">
            {/* Deviation Alert */}
            <div className="bg-surface-container-high p-8 border-l-4 border-tertiary-container">
              <div className="flex items-start justify-between mb-4">
                <h3 className="font-headline font-bold text-tertiary-container uppercase tracking-tight">Kritinis_Nukrypimas_Aptiktas</h3>
                <span className="material-symbols-outlined text-tertiary-container">warning</span>
              </div>
              <p className="text-on-surface-variant text-sm mb-6 leading-relaxed">
                Saugumo kvadrantas rodo 68% nukrypimą nuo bazinių modelių per pastarąsias 48 valandas. Žvalgyba nurodo nepatvirtintus mazgų įterpimus politinėje ašyje.
              </p>
              <div className="flex gap-4">
                <button className="bg-tertiary-container text-on-tertiary-container px-4 py-1.5 font-label text-[10px] font-bold uppercase tracking-widest hover:brightness-110">
                  Izoliuoti_Šaltinį
                </button>
                <button className="text-tertiary-container border border-tertiary-container/30 px-4 py-1.5 font-label text-[10px] font-bold uppercase tracking-widest hover:bg-tertiary-container/10">
                  Ignoruoti
                </button>
              </div>
            </div>

            {/* Intelligence Metrics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-surface-container-low p-6">
                <div className="text-[9px] font-bold text-outline uppercase tracking-widest mb-1">Šaltinio_Patikimumas</div>
                <div className="font-headline text-3xl font-bold">0.94<span className="text-sm text-primary">/1.0</span></div>
              </div>
              <div className="bg-surface-container-low p-6">
                <div className="text-[9px] font-bold text-outline uppercase tracking-widest mb-1">Duomenų_Delsa</div>
                <div className="font-headline text-3xl font-bold">42<span className="text-sm text-primary">ms</span></div>
              </div>
            </div>

            {/* Evidence Node Connectors */}
            <div className="bg-surface-container-low p-8">
              <h3 className="font-headline font-bold uppercase tracking-tight mb-6">Įrodymų_Mazgai</h3>
              <div className="space-y-4">
                {evidenceNodes.map((node, i) => (
                  <div key={i} className="flex items-center group cursor-pointer">
                    <div className="w-2 h-2 bg-secondary mr-4" />
                    <div className="flex-1 border-b border-outline-variant/15 pb-2">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-label text-xs font-bold uppercase group-hover:text-primary transition-colors">{node.name}</span>
                        <span className="material-symbols-outlined text-sm text-outline">link</span>
                      </div>
                      <div className="text-[10px] text-outline-variant font-mono">MAIŠOS: {node.hash}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Trend Chart - Truthfulness Over Time */}
        <div className="mt-16 bg-surface-container-low p-8">
          <div className="flex items-center justify-between mb-8">
            <h3 className="font-headline font-bold uppercase tracking-tight">Tiesos_Tendencija_2024</h3>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-primary" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-outline">Tiesos indeksas</span>
              </div>
            </div>
          </div>
          <div className="flex items-end gap-2 h-48">
            {trendData.map((d, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-2">
                <span className="font-mono text-[9px] text-primary">{d.value}%</span>
                <div
                  className={`w-full transition-all ${d.value < 50 ? "bg-tertiary-container/60" : "bg-primary/60"} hover:opacity-100`}
                  style={{ height: `${(d.value / maxTrend) * 160}px` }}
                />
                <span className="font-label text-[9px] text-on-surface-variant uppercase">{d.month}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Statement Analysis Table */}
        <div className="mt-10 bg-surface-container-low overflow-hidden">
          <div className="px-8 py-6 border-b border-outline-variant/15 flex justify-between items-center bg-surface-container-high/30">
            <h3 className="font-headline font-bold uppercase tracking-tight">Pareiškimų_Analizės_Matrica</h3>
          </div>
          <table className="w-full text-left font-label text-xs uppercase">
            <thead className="text-on-surface-variant font-bold border-b border-outline-variant/10">
              <tr>
                <th className="px-8 py-4 tracking-widest">Data</th>
                <th className="px-8 py-4 tracking-widest">Pareiškimas</th>
                <th className="px-8 py-4 tracking-widest">Verdiktas</th>
                <th className="px-8 py-4 tracking-widest">Šaltinis</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/5">
              {statementsTable.map((s, i) => (
                <tr key={i} className={`hover:bg-surface-bright/20 transition-colors ${s.verdict === "KLAIDINGA" ? "bg-tertiary-container/5" : ""}`}>
                  <td className="px-8 py-6 font-mono text-outline-variant">{s.date}</td>
                  <td className="px-8 py-6 font-bold normal-case">{s.statement}</td>
                  <td className="px-8 py-6">
                    <span className={`${s.verdictColor} px-2 py-0.5 text-[9px] font-bold`}>{s.verdict}</span>
                  </td>
                  <td className="px-8 py-6 text-on-surface-variant">{s.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Category Breakdown Matrix */}
        <div className="mt-10 bg-surface-container-low overflow-hidden">
          <div className="px-8 py-6 border-b border-outline-variant/15 flex justify-between items-center bg-surface-container-high/30">
            <h3 className="font-headline font-bold uppercase tracking-tight">Kategorijų_Suskaidymo_Matrica</h3>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-primary" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-outline">Stabili</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-tertiary-container" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-outline">Nestabili</span>
              </div>
            </div>
          </div>
          <table className="w-full text-left font-label text-xs uppercase">
            <thead className="text-on-surface-variant font-bold border-b border-outline-variant/10">
              <tr>
                <th className="px-8 py-4 tracking-widest">Ašies_Identifikatorius</th>
                <th className="px-8 py-4 tracking-widest">Pasitikėjimo_Balas</th>
                <th className="px-8 py-4 tracking-widest">Variacijos_Norma</th>
                <th className="px-8 py-4 tracking-widest">Paskutinė_Patikra</th>
                <th className="px-8 py-4 tracking-widest text-right">Veiksmas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/5">
              {categoryBreakdown.map((cat, i) => (
                <tr key={i} className={`hover:bg-surface-bright/20 transition-colors ${cat.critical ? "bg-tertiary-container/5" : ""}`}>
                  <td className={`px-8 py-6 font-bold ${cat.critical ? "text-tertiary-container" : ""}`}>{cat.name}</td>
                  <td className="px-8 py-6">{cat.score} <span className={`text-[10px] ${cat.changeColor} ml-2`}>{cat.change}</span></td>
                  <td className={`px-8 py-6 ${cat.critical ? "font-bold text-tertiary-container" : ""}`}>{cat.variance}</td>
                  <td className="px-8 py-6 font-mono text-outline-variant">{cat.lastVerified}</td>
                  <td className="px-8 py-6 text-right">
                    <span className={`material-symbols-outlined ${cat.critical ? "text-tertiary-container cursor-pointer hover:brightness-125" : "text-on-surface-variant cursor-pointer hover:text-primary"}`}>
                      {cat.critical ? "priority_high" : "open_in_new"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* System Footer */}
        <footer className="mt-20 border-t border-outline-variant/15 pt-10 pb-10 flex flex-wrap gap-12 text-[10px] font-mono text-outline-variant uppercase">
          <div>MAZGO_ID: PROTOKOLAS_ALFA_V7</div>
          <div>VEIKIMO_LAIKAS: 14 222 VALANDOS</div>
          <div>GEO_VIETA: [REDAGUOTA]</div>
          <div className="ml-auto text-primary">ŠIFRUOTA_SESIJA_NUSTATYTA // AES-256</div>
        </footer>
      </div>
    </AppLayout>
  );
}
