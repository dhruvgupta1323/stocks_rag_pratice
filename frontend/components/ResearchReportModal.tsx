"use client";

import { useState, useEffect } from "react";
import { FileText, Loader2, X, Download, ShieldCheck, AlertCircle, ExternalLink, Calendar } from "lucide-react";
import { getStockReport } from "@/lib/api";

interface ResearchReportModalProps {
  symbol: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function ResearchReportModal({ symbol, isOpen, onClose }: ResearchReportModalProps) {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && symbol) {
      setLoading(true);
      setError(null);
      getStockReport(symbol)
        .then((data) => setReport(data))
        .catch((err) => setError(err.message || "Failed to generate research report"))
        .finally(() => setLoading(false));
    }
  }, [isOpen, symbol]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-4xl rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950/80 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-100">
                Equity Intelligence Research Report
              </h2>
              <p className="text-xs text-slate-400">
                Automated synthesized analysis for <span className="text-cyan-400 font-semibold">{symbol}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => window.print()}
              className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-700 transition-colors flex items-center gap-1.5"
            >
              <Download className="h-3.5 w-3.5" /> Print / PDF
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 max-h-[75vh] overflow-y-auto space-y-6">
          {loading && (
            <div className="py-20 text-center flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
              <p className="text-sm">Generating comprehensive research report from verified financial evidence...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-950/30 border border-red-900 text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {report && !loading && (
            <div className="space-y-6 text-slate-300 text-sm">
              {/* Header Info */}
              <div className="flex flex-wrap items-center justify-between gap-2 p-4 rounded-xl bg-slate-950 border border-slate-800">
                <div>
                  <h1 className="text-xl font-bold text-slate-100">{report.title}</h1>
                  <p className="text-xs text-slate-400 mt-1">
                    Exchange: <span className="text-slate-200 font-semibold">{report.exchange}</span> • Sector:{" "}
                    <span className="text-slate-200">{report.company_overview.sector}</span>
                  </p>
                </div>
                <div className="text-right text-xs text-slate-500 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  Generated: {new Date(report.generation_timestamp).toLocaleString()}
                </div>
              </div>

              {/* Company Overview */}
              <div>
                <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2">1. Company Overview</h3>
                <p className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 leading-relaxed text-slate-300">
                  {report.company_overview.description}
                </p>
              </div>

              {/* Market Performance */}
              <div>
                <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2">2. Market Performance</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div>
                    <div className="text-xs text-slate-500">Last Price</div>
                    <div className="text-base font-bold text-slate-100">
                      ₹{report.market_performance.last_price?.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500">Change</div>
                    <div className={`text-base font-bold ${report.market_performance.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {report.market_performance.change >= 0 ? "+" : ""}{report.market_performance.change?.toFixed(2)} ({report.market_performance.change_percent}%)
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500">Day Range</div>
                    <div className="text-xs font-semibold text-slate-200 mt-1">
                      ₹{report.market_performance.day_low?.toFixed(2)} - ₹{report.market_performance.day_high?.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500">Data Status</div>
                    <div className="text-xs font-bold uppercase tracking-wider text-cyan-400 mt-1">
                      {report.market_performance.data_status}
                    </div>
                  </div>
                </div>
              </div>

              {/* Catalysts & Risks */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">
                    Key Positive Catalysts
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {report.catalysts?.map((c: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-emerald-400">✓</span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">
                    Relevant Risk Factors
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {report.risks?.map((r: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-amber-400">⚠</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Citations & Evidence */}
              {report.citations?.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2">Source Citations</h3>
                  <div className="space-y-2">
                    {report.citations.map((cit: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                        <div>
                          <div className="font-semibold text-slate-200">{cit.title}</div>
                          <div className="text-slate-500 text-[11px]">Publisher: {cit.publisher}</div>
                        </div>
                        {cit.url && (
                          <a href={cit.url} target="_blank" rel="noreferrer" className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 shrink-0 ml-3">
                            Source Link <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Legal Disclaimer & Limitations */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-xs text-slate-400 space-y-1">
                <div className="font-bold text-slate-300 flex items-center gap-1.5 mb-1">
                  <ShieldCheck className="h-4 w-4 text-cyan-400" /> Research Intelligence Disclosure
                </div>
                {report.data_limitations?.map((lim: string, idx: number) => (
                  <p key={idx}>• {lim}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

