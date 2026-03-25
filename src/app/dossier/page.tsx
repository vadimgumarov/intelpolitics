"use client";

import AppLayout from "@/components/AppLayout";

const promiseMatrix = [
  { name: "Energetikos reforma 2024", status: "Redaguota", statusBg: "bg-surface-bright text-on-surface-variant", progress: 15, color: "border-primary-container" },
  { name: "Mokesčių lengvatos V4", status: "Priimta", statusBg: "bg-primary text-on-primary", progress: 92, color: "border-secondary" },
  { name: "Sveikatos plėtra", status: "Vetuota", statusBg: "bg-tertiary-container text-on-tertiary-container", progress: 0, color: "border-tertiary" },
  { name: "Švietimo investicijos", status: "Vykdoma", statusBg: "bg-surface-bright text-on-surface-variant", progress: 47, color: "border-primary" },
];

const evidenceCards = [
  {
    ref: "DOK-901",
    time: "Prieš 2 val.",
    text: "Užfiksuotas dialogas rodo išankstinį žinojimą apie paskirstymą 4-ame rajone.",
    type: "audio",
    label: "Garso_Transkriptas.mp3",
  },
  {
    ref: "DOK-224",
    time: "Vakar",
    text: "Vizualinis patvirtinimas: susitikimas su žinomu lobistu terminale Nr. 3.",
    type: "image",
    label: "",
  },
  {
    ref: "DOK-011",
    time: "2024-10-04",
    text: '\u201EProkotolo stabilumas yra svarbiau nei individualūs sentimentai...\u201C',
    type: "quote",
    label: "Vidinis_Memo_Nutekėjimas",
  },
];

const votingRecords = [
  { date: "2024-11-15", bill: "Energetikos reforma Nr. 447", vote: "UŽ", result: "Priimta" },
  { date: "2024-10-28", bill: "Biudžeto pakeitimas Nr. 12", vote: "PRIEŠ", result: "Atmesta" },
  { date: "2024-09-14", bill: "Gynybos finansavimas Nr. 88", vote: "UŽ", result: "Priimta" },
  { date: "2024-08-20", bill: "Švietimo biudžetas Nr. 33", vote: "SUSILAIKĖ", result: "Priimta" },
  { date: "2024-07-05", bill: "Sveikatos apsauga Nr. 201", vote: "PRIEŠ", result: "Atmesta" },
];

const statements = [
  { date: "2024-11-10", text: '\u201EM\u016Bs\u0173 ekonomika auga spar\u010Diausiai regione.\u201C', verdict: "NEPATVIRTINTA", source: "Seimo posėdis" },
  { date: "2024-10-22", text: '\u201EInvesticijos \u012F \u0161vietim\u0105 padid\u0117jo 40%.\u201C', verdict: "KLAIDINGA", source: "Spaudos konferencija" },
  { date: "2024-09-15", text: '\u201EGynybos biud\u017Eetas atitinka NATO standartus.\u201C', verdict: "TIESA", source: "Interviu LRT" },
];

export default function DossierPage() {
  return (
    <AppLayout>
      {/* Page Header */}
      <div className="p-8 border-b border-outline-variant/15">
        <div className="flex items-end justify-between max-w-7xl mx-auto">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="bg-primary text-on-primary text-[10px] font-bold px-2 py-0.5 uppercase tracking-widest">
                Taikinys_Aktyvus
              </span>
              <span className="text-on-surface-variant text-[10px] font-label uppercase tracking-widest">
                ID: 4491-F4-PROTOKOLAS
              </span>
            </div>
            <h1 className="text-5xl font-headline font-bold text-on-surface tracking-tighter uppercase">
              ALEKSANDRAS_VANSEVIČIUS
            </h1>
          </div>
          <div className="flex gap-4">
            <button className="bg-surface-bright text-on-surface px-6 py-2 font-label text-xs font-bold uppercase tracking-widest hover:bg-primary-container transition-all flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">download</span>
              Eksportuoti_Dosje
            </button>
          </div>
        </div>
      </div>

      {/* Detective Board Layout */}
      <div className="p-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-12 gap-8">
          {/* Left Column: Profile & Truthfulness Rose */}
          <div className="col-span-3 space-y-8">
            {/* Profile Image Card */}
            <div className="bg-surface-container-low p-6 border-l border-primary/30 relative">
              <div className="absolute -left-[1px] top-0 h-8 w-[2px] bg-primary shadow-[0_0_12px_#A7C8FF]" />
              {/* Photo placeholder */}
              <div className="w-full aspect-[3/4] mb-4 relative" style={{ background: "linear-gradient(135deg, #0d1a2d 0%, #111a2e 50%, #111417 100%)" }}>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="material-symbols-outlined text-6xl text-on-surface-variant/15">person</span>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] font-label uppercase text-on-surface-variant tracking-widest">Partija</div>
                  <div className="text-sm font-bold text-primary uppercase">Vieningojo_Fronto_Koalicija</div>
                </div>
                <div>
                  <div className="text-[10px] font-label uppercase text-on-surface-variant tracking-widest">Pareigos</div>
                  <div className="text-sm font-bold text-on-surface uppercase tracking-tight">Vyriausias_Strateginis_Analitikas</div>
                </div>
                <div className="pt-4 border-t border-outline-variant/15">
                  <div className="flex justify-between items-center text-[10px] font-label uppercase text-on-surface-variant mb-1">
                    <span>Grėsmės_Lygis</span>
                    <span className="text-tertiary">Kritinis</span>
                  </div>
                  <div className="h-1 w-full bg-surface-variant">
                    <div className="h-full bg-tertiary-container w-[88%]" />
                  </div>
                </div>
              </div>
            </div>

            {/* Truthfulness Rose */}
            <div className="bg-surface-container-low p-6 h-[400px] flex flex-col">
              <h3 className="font-headline text-xs font-bold uppercase tracking-widest mb-8 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-primary" /> Integralumo_Matrica
              </h3>
              <div className="flex-1 relative truth-rose-grid flex items-center justify-center">
                <svg className="w-48 h-48 drop-shadow-[0_0_8px_rgba(167,200,255,0.2)]" viewBox="0 0 100 100">
                  {/* Background circles */}
                  <circle cx="50" cy="50" r="45" fill="none" stroke="#414752" strokeDasharray="2 2" strokeWidth="0.5" />
                  <circle cx="50" cy="50" r="30" fill="none" stroke="#414752" strokeDasharray="2 2" strokeWidth="0.5" />
                  <circle cx="50" cy="50" r="15" fill="none" stroke="#414752" strokeDasharray="2 2" strokeWidth="0.5" />
                  {/* Axis lines */}
                  <line x1="50" y1="5" x2="50" y2="95" stroke="#414752" strokeWidth="0.5" />
                  <line x1="5" y1="50" x2="95" y2="50" stroke="#414752" strokeWidth="0.5" />
                  {/* Data polygon */}
                  <polygon
                    fill="rgba(68,145,244,0.2)"
                    points="50,15 85,40 70,80 30,75 15,35"
                    stroke="#A7C8FF"
                    strokeWidth="1"
                  />
                  {/* Vertex nodes (4px squares) */}
                  <rect x="48" y="13" width="4" height="4" fill="#A7C8FF" />
                  <rect x="83" y="38" width="4" height="4" fill="#A7C8FF" />
                  <rect x="68" y="78" width="4" height="4" fill="#A7C8FF" />
                  <rect x="28" y="73" width="4" height="4" fill="#A7C8FF" />
                  <rect x="13" y="33" width="4" height="4" fill="#A7C8FF" />
                </svg>
                {/* Labels */}
                <span className="absolute top-2 text-[9px] font-bold uppercase text-on-surface-variant">Skaidrumas</span>
                <span className="absolute right-0 text-[9px] font-bold uppercase text-on-surface-variant">Politikos_Atmintis</span>
                <span className="absolute bottom-2 text-[9px] font-bold uppercase text-on-surface-variant">Viešas_Pasitikėjimas</span>
                <span className="absolute left-0 text-[9px] font-bold uppercase text-on-surface-variant">Nuoseklumas</span>
              </div>
              <div className="mt-4 text-[10px] text-on-surface-variant/60 font-label leading-tight">
                * DUOMENŲ_ŠALTINIS: PATIKRINTI_STENOGRAMOS_0922-2024
              </div>
            </div>
          </div>

          {/* Middle Column: Lobbying Nexus */}
          <div className="col-span-6 space-y-8">
            <div className="bg-surface-container-low p-8 relative overflow-hidden" style={{ minHeight: "832px" }}>
              {/* Title & Legend */}
              <div className="flex justify-between items-start mb-8 relative z-10">
                <div>
                  <h3 className="font-headline text-lg font-bold tracking-tight uppercase">Įtakos_Mazgas_v2.0</h3>
                  <p className="text-[10px] font-label text-on-surface-variant tracking-widest">Finansinių ir politinių tarpininkų sekimas</p>
                </div>
                <div className="flex gap-4">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-primary" />
                    <span className="text-[9px] font-bold uppercase text-primary">Didelė_Įtaka</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-tertiary" />
                    <span className="text-[9px] font-bold uppercase text-tertiary">Šešėlinis_Turtas</span>
                  </div>
                </div>
              </div>

              {/* Detective Board Workspace */}
              <div className="relative w-full border border-outline-variant/10" style={{ height: "650px" }}>
                {/* Background grid */}
                <div className="absolute inset-0 opacity-5 pointer-events-none" style={{ backgroundImage: "radial-gradient(#A7C8FF 1px, transparent 1px)", backgroundSize: "40px 40px" }} />

                {/* Connector Lines SVG */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  <line className="flow-line" stroke="#A7C8FF" strokeWidth="2" x1="50%" y1="50%" x2="50%" y2="25%" />
                  <line className="flow-line" stroke="#A7C8FF" strokeWidth="1.5" x1="50%" y1="25%" x2="25%" y2="15%" />
                  <line className="flow-line" stroke="#A7C8FF" strokeWidth="1.5" x1="50%" y1="25%" x2="50%" y2="10%" />
                  <line className="flow-line" stroke="#A7C8FF" strokeWidth="1.5" x1="50%" y1="25%" x2="75%" y2="15%" />
                  <line className="flow-line-static" stroke="#414752" strokeWidth="1" x1="50%" y1="50%" x2="20%" y2="50%" />
                  <line className="flow-line-static" stroke="#414752" strokeWidth="1" x1="50%" y1="50%" x2="80%" y2="50%" />
                  <line className="flow-line-static" stroke="#ffb3ad" strokeWidth="1" x1="20%" y1="50%" x2="20%" y2="75%" />
                  <line className="flow-line-static" stroke="#414752" strokeWidth="1" x1="80%" y1="50%" x2="80%" y2="75%" />
                </svg>

                {/* Central Node */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 group">
                  <div className="w-20 h-20 bg-primary/10 border border-primary flex items-center justify-center p-1 shadow-[0_0_15px_rgba(167,200,255,0.2)]">
                    <div className="w-full h-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, #0d1a2d, #111417)" }}>
                      <span className="material-symbols-outlined text-3xl text-primary/40">person</span>
                    </div>
                  </div>
                  <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-[10px] font-bold bg-primary text-on-primary px-2 py-0.5 whitespace-nowrap">
                    ALEKSANDRAS_V
                  </div>
                </div>

                {/* Lobbying Hub */}
                <div className="absolute top-[25%] left-1/2 -translate-x-1/2 -translate-y-1/2">
                  <div className="w-16 h-16 bg-surface-container-high border-2 border-primary flex flex-col items-center justify-center group cursor-pointer hover:bg-primary-container/20 transition-all shadow-[0_0_15px_rgba(167,200,255,0.2)]">
                    <span className="material-symbols-outlined text-primary text-3xl">account_balance</span>
                  </div>
                  <div className="mt-2 text-[10px] font-bold text-center uppercase text-primary tracking-widest bg-background/80 px-2">LOBIZMO_CENTRAS</div>
                </div>

                {/* Energy */}
                <div className="absolute top-[15%] left-[25%] -translate-x-1/2 -translate-y-1/2">
                  <div className="w-12 h-12 bg-surface-container-high border border-outline-variant flex items-center justify-center group cursor-pointer hover:border-primary transition-all">
                    <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary">bolt</span>
                  </div>
                  <div className="mt-2 text-[9px] font-bold text-center uppercase text-on-surface-variant tracking-tighter">ENERGETIKOS_SEKTORIUS</div>
                </div>

                {/* Defense */}
                <div className="absolute top-[10%] left-1/2 -translate-x-1/2 -translate-y-1/2">
                  <div className="w-12 h-12 bg-surface-container-high border border-outline-variant flex items-center justify-center group cursor-pointer hover:border-primary transition-all">
                    <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary">shield</span>
                  </div>
                  <div className="mt-2 text-[9px] font-bold text-center uppercase text-on-surface-variant tracking-tighter">GYNYBOS_RANGOVAI</div>
                </div>

                {/* Finance */}
                <div className="absolute top-[15%] left-[75%] -translate-x-1/2 -translate-y-1/2">
                  <div className="w-12 h-12 bg-surface-container-high border border-outline-variant flex items-center justify-center group cursor-pointer hover:border-primary transition-all">
                    <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary">payments</span>
                  </div>
                  <div className="mt-2 text-[9px] font-bold text-center uppercase text-on-surface-variant tracking-tighter">AVANGARDINĖ_HOLDINGAI</div>
                </div>

                {/* Media Proxy */}
                <div className="absolute top-1/2 left-[20%] -translate-x-1/2 -translate-y-1/2">
                  <div className="w-12 h-12 bg-surface-container-high border border-outline-variant flex items-center justify-center group cursor-pointer hover:border-primary transition-all">
                    <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary">broadcast_on_home</span>
                  </div>
                  <div className="mt-2 text-[9px] font-bold text-center uppercase text-on-surface-variant">Globalus_Ryšys_PR</div>
                </div>

                {/* Legislative Ally */}
                <div className="absolute top-1/2 left-[80%] -translate-x-1/2 -translate-y-1/2">
                  <div className="w-12 h-12 bg-surface-container-high border border-outline-variant flex items-center justify-center group cursor-pointer hover:border-primary transition-all">
                    <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary">gavel</span>
                  </div>
                  <div className="mt-2 text-[9px] font-bold text-center uppercase text-on-surface-variant">Komitetas_09_Vidinis</div>
                </div>

                {/* Shadow Asset */}
                <div className="absolute top-[75%] left-[20%] -translate-x-1/2 -translate-y-1/2">
                  <div className="w-12 h-12 bg-surface-container-high border border-tertiary/40 flex items-center justify-center group cursor-pointer hover:bg-tertiary-container/10 transition-all">
                    <span className="material-symbols-outlined text-tertiary group-hover:text-on-tertiary-container">person_off</span>
                  </div>
                  <div className="mt-2 text-[9px] font-bold text-center uppercase text-tertiary">Nežinomas_Tarpininkas</div>
                </div>

                {/* Data Archive */}
                <div className="absolute top-[75%] left-[80%] -translate-x-1/2 -translate-y-1/2">
                  <div className="w-12 h-12 bg-surface-container-high border border-outline-variant flex items-center justify-center group cursor-pointer hover:border-primary transition-all">
                    <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary">inventory_2</span>
                  </div>
                  <div className="mt-2 text-[9px] font-bold text-center uppercase text-on-surface-variant">Šifruotas_Archyvas_TR901</div>
                </div>
              </div>

              {/* Bottom Stats */}
              <div className="grid grid-cols-4 gap-0 mt-8 border-t border-outline-variant/15">
                <div className="p-4 border-r border-outline-variant/15">
                  <div className="text-[9px] font-label uppercase text-on-surface-variant mb-1">Tiesos indeksas</div>
                  <div className="text-2xl font-headline font-bold text-primary">62%</div>
                </div>
                <div className="p-4 border-r border-outline-variant/15">
                  <div className="text-[9px] font-label uppercase text-on-surface-variant mb-1">Pažadų vykdymas</div>
                  <div className="text-2xl font-headline font-bold text-primary">38%</div>
                </div>
                <div className="p-4 border-r border-outline-variant/15">
                  <div className="text-[9px] font-label uppercase text-on-surface-variant mb-1">Lobizmo ryšiai</div>
                  <div className="text-2xl font-headline font-bold text-primary">14</div>
                </div>
                <div className="p-4">
                  <div className="text-[9px] font-label uppercase text-on-surface-variant mb-1">Balsavimo nuoseklumas</div>
                  <div className="text-2xl font-headline font-bold text-tertiary">ŽEMAS</div>
                </div>
              </div>
            </div>

            {/* Recent Statements Timeline */}
            <div className="bg-surface-container-low p-6">
              <h3 className="font-headline text-xs font-bold uppercase tracking-widest mb-6 flex items-center gap-2">
                Paskutiniai pareiškimai
              </h3>
              <div className="space-y-4">
                {statements.map((s, i) => (
                  <div key={i} className="flex items-start gap-4 p-4 bg-surface-container-high/30 hover:bg-surface-bright/20 transition-colors">
                    <div className="min-w-[80px]">
                      <span className="font-mono text-[9px] text-on-surface-variant">{s.date}</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-[11px] font-label text-on-surface leading-relaxed italic border-l border-primary/40 pl-2">{s.text}</p>
                      <div className="mt-2 flex items-center gap-3">
                        <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 ${
                          s.verdict === "TIESA" ? "bg-primary/20 text-primary" :
                          s.verdict === "KLAIDINGA" ? "bg-tertiary-container/20 text-tertiary" :
                          "bg-surface-bright text-on-surface-variant"
                        }`}>{s.verdict}</span>
                        <span className="text-[9px] text-on-surface-variant/60">{s.source}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Voting Record Table */}
            <div className="bg-surface-container-low overflow-hidden">
              <div className="px-8 py-6 border-b border-outline-variant/15 bg-surface-container-high/30">
                <h3 className="font-headline font-bold uppercase tracking-tight">Balsavimo_Įrašai</h3>
              </div>
              <table className="w-full text-left font-label text-xs uppercase">
                <thead className="text-on-surface-variant font-bold border-b border-outline-variant/10">
                  <tr>
                    <th className="px-8 py-4 tracking-widest">Data</th>
                    <th className="px-8 py-4 tracking-widest">Įstatymo projektas</th>
                    <th className="px-8 py-4 tracking-widest">Balsas</th>
                    <th className="px-8 py-4 tracking-widest">Rezultatas</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/5">
                  {votingRecords.map((v, i) => (
                    <tr key={i} className="hover:bg-surface-bright/20 transition-colors">
                      <td className="px-8 py-4 font-mono text-on-surface-variant">{v.date}</td>
                      <td className="px-8 py-4 font-bold">{v.bill}</td>
                      <td className="px-8 py-4">
                        <span className={`px-1.5 py-0.5 text-[9px] font-bold ${
                          v.vote === "UŽ" ? "bg-primary/20 text-primary" :
                          v.vote === "PRIEŠ" ? "bg-tertiary-container/20 text-tertiary" :
                          "bg-surface-bright text-on-surface-variant"
                        }`}>{v.vote}</span>
                      </td>
                      <td className="px-8 py-4 text-on-surface-variant">{v.result}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Column: Promise vs Action & Pinned Evidence */}
          <div className="col-span-3 space-y-8">
            {/* Promise vs Action Matrix */}
            <div className="bg-surface-container-low p-6">
              <h3 className="font-headline text-xs font-bold uppercase tracking-widest mb-6 flex items-center justify-between">
                <span>Vykdymo_Matrica</span>
                <span className="text-[9px] font-label text-primary">Gyvai_Atnaujinama</span>
              </h3>
              <div className="space-y-6">
                {promiseMatrix.map((item, i) => (
                  <div key={i} className={`relative pl-4 border-l-2 ${item.color}`}>
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-[10px] font-bold uppercase text-on-surface tracking-tighter">{item.name}</span>
                      <span className={`${item.statusBg} text-[9px] px-1.5 font-label`}>{item.status}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1 bg-surface-variant">
                        <div className={`h-full ${item.progress === 0 ? "bg-tertiary" : "bg-primary"}`} style={{ width: `${item.progress}%` }} />
                      </div>
                      <span className={`text-[9px] font-label font-bold ${item.progress === 0 ? "text-tertiary" : "text-primary"}`}>{item.progress}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Pinned Evidence Feed */}
            <div className="bg-surface-container-low p-6">
              <h3 className="font-headline text-xs font-bold uppercase tracking-widest mb-6 flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">push_pin</span> Prisegti_Įrodymai
              </h3>
              <div className="space-y-4">
                {evidenceCards.map((ev, i) => (
                  <div key={i} className="bg-surface-container-high p-4 border border-outline-variant/10 group cursor-pointer hover:bg-surface-bright transition-colors">
                    <div className="flex justify-between text-[9px] font-label text-on-surface-variant uppercase mb-2">
                      <span>Dok_Ref: {ev.ref}</span>
                      <span>{ev.time}</span>
                    </div>
                    {ev.type === "quote" ? (
                      <p className="text-[11px] leading-relaxed text-on-surface font-label italic border-l border-primary/40 pl-2">{ev.text}</p>
                    ) : (
                      <p className="text-[11px] leading-relaxed text-on-surface font-label mb-3">{ev.text}</p>
                    )}
                    {ev.type === "audio" && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="material-symbols-outlined text-xs text-primary">audio_file</span>
                        <span className="text-[9px] font-bold uppercase text-primary">{ev.label}</span>
                      </div>
                    )}
                    {ev.type === "quote" && (
                      <div className="mt-2 text-[9px] font-bold uppercase text-on-surface-variant/40">{ev.label}</div>
                    )}
                    {ev.type === "image" && (
                      <div className="w-full h-24 mt-2" style={{ background: "linear-gradient(135deg, #1a1c1f 0%, #0b0f11 100%)" }}>
                        <div className="w-full h-full flex items-center justify-center">
                          <span className="material-symbols-outlined text-2xl text-on-surface-variant/15">image</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Status Bar */}
      <footer className="p-8 max-w-7xl mx-auto flex justify-between items-center text-[10px] font-label uppercase tracking-widest text-on-surface-variant/40 border-t border-outline-variant/10 mt-12">
        <div className="flex gap-6">
          <span>Sistemos_Veikimas: 432:12:09</span>
          <span>Signalo_Stiprumas: Šifruotas</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-primary animate-pulse" />
          <span>Sistema_Gyvas_Srautas_Aktyvus</span>
        </div>
      </footer>
    </AppLayout>
  );
}
