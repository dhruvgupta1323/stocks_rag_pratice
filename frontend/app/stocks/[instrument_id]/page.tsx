"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Database,
  Building,
  BarChart2,
  Newspaper,
  FileText,
  Loader2,
  AlertCircle,
  ExternalLink,
  ShieldAlert,
  Percent,
} from "lucide-react";
import {
  getStockOverview,
  getHistoricalBars,
  getStockFinancials,
  getStockNews,
  StockOverview,
  HistoricalBarsResponse,
  CompanyFinancials,
  StockNewsResponse,
} from "@/lib/api";
import StockChart from "@/components/StockChart";
import ResearchChat from "@/components/ResearchChat";
import ResearchReportModal from "@/components/ResearchReportModal";

export default function StockDashboardPage() {
  const params = useParams();
  const symbol = (params.instrument_id as string)?.toUpperCase();

  const [overview, setOverview] = useState<StockOverview | null>(null);
  const [history, setHistory] = useState<HistoricalBarsResponse | null>(null);
  const [financials, setFinancials] = useState<CompanyFinancials | null>(null);
  const [news, setNews] = useState<StockNewsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "financials" | "news">("overview");
  const [isReportOpen, setIsReportOpen] = useState(false);

  useEffect(() => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    Promise.all([
      getStockOverview(symbol),
      getHistoricalBars(symbol, 90, "1d"),
      getStockFinancials(symbol).catch(() => null),
      getStockNews(symbol, 10).catch(() => null),
    ])
      .then(([ov, hist, fin, nw]) => {
        setOverview(ov);
        setHistory(hist);
        if (fin) setFinancials(fin);
        if (nw) setNews(nw);
      })
      .catch((err) => {
        setError(err.message || "Failed to load stock data");
      })
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3 text-slate-400">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
        <p className="text-sm">Retrieving real-time market quotes and financial metrics for {symbol}...</p>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="container mx-auto px-4 py-16 max-w-xl text-center">
        <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 text-slate-300">
          <AlertCircle className="h-10 w-10 text-amber-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-100 mb-1">Stock Not Found or Data Unavailable</h2>
          <p className="text-sm text-slate-400 mb-4">{error || `No equity data available for ${symbol}`}</p>
          <a
            href="/"
            className="inline-block rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
          >
            Return to Stock Search
          </a>
        </div>
      </div>
    );
  }

  const quote = overview.quote;
  const isPositive = quote.change >= 0;

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8">
      {/* Top Banner: Company & Price Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100">{overview.name}</h1>
            <span className="text-xs font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
              {overview.symbol} • {overview.exchange}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400">
            {overview.sector} • {overview.industry}
          </p>
        </div>

        {/* Live Price Block */}
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-2xl sm:text-3xl font-black text-slate-100">
              ₹{quote.last_price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div
              className={`flex items-center justify-end gap-1 text-sm font-bold ${
                isPositive ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
              <span>
                {isPositive ? "+" : ""}
                {quote.change.toFixed(2)} ({isPositive ? "+" : ""}
                {quote.change_percent}%)
              </span>
            </div>
          </div>

          <button
            onClick={() => setIsReportOpen(true)}
            className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 hover:opacity-90 transition-opacity flex items-center gap-1.5 shrink-0"
          >
            <FileText className="h-4 w-4" /> Generate Report
          </button>
        </div>
      </div>

      {/* Main Grid: Left Column (Data & Charts) + Right Column (AI Chat) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column - 7 Cols */}
        <div className="lg:col-span-7 space-y-6">
          {/* Key Metrics Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60">
              <span className="text-xs text-slate-400">Day Range</span>
              <div className="text-sm font-bold text-slate-100 mt-0.5">
                ₹{quote.low.toFixed(2)} - ₹{quote.high.toFixed(2)}
              </div>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60">
              <span className="text-xs text-slate-400">Volume</span>
              <div className="text-sm font-bold text-slate-100 mt-0.5">{quote.volume.toLocaleString()}</div>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60">
              <span className="text-xs text-slate-400">52W Range</span>
              <div className="text-sm font-bold text-slate-100 mt-0.5">
                ₹{overview.low_52w?.toFixed(2)} - ₹{overview.high_52w?.toFixed(2)}
              </div>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60">
              <span className="text-xs text-slate-400">P/E Ratio</span>
              <div className="text-sm font-bold text-slate-100 mt-0.5">{overview.pe_ratio ? `${overview.pe_ratio}x` : "N/A"}</div>
            </div>
          </div>

          {/* Interactive Chart */}
          {history && history.bars && (
            <StockChart
              bars={history.bars}
              symbol={overview.symbol}
              isPositive={isPositive}
              currency={quote.currency}
            />
          )}

          {/* Tabs: Financials & News */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
            <div className="flex border-b border-slate-800 pb-3 mb-4 gap-4">
              <button
                onClick={() => setActiveTab("overview")}
                className={`text-xs sm:text-sm font-bold pb-1 transition-colors ${
                  activeTab === "overview" ? "text-cyan-400 border-b-2 border-cyan-400" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Company Summary
              </button>
              <button
                onClick={() => setActiveTab("financials")}
                className={`text-xs sm:text-sm font-bold pb-1 transition-colors ${
                  activeTab === "financials" ? "text-cyan-400 border-b-2 border-cyan-400" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Reported Financials
              </button>
              <button
                onClick={() => setActiveTab("news")}
                className={`text-xs sm:text-sm font-bold pb-1 transition-colors ${
                  activeTab === "news" ? "text-cyan-400 border-b-2 border-cyan-400" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                News & Disclosures
              </button>
            </div>

            {activeTab === "overview" && (
              <div className="space-y-4 text-xs sm:text-sm leading-relaxed text-slate-300">
                <p>{overview.description}</p>
                <div className="flex items-center gap-4 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                  <span className="flex items-center gap-1">
                    <Database className="h-3.5 w-3.5 text-cyan-400" /> Source: {quote.provider.toUpperCase()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5 text-cyan-400" /> Last Updated:{" "}
                    {new Date(overview.last_updated).toLocaleTimeString()}
                  </span>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-cyan-400">
                    Status: {overview.data_status.toUpperCase()}
                  </span>
                </div>
              </div>
            )}

            {activeTab === "financials" && financials && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {financials.annual_metrics.map((m) => (
                    <div key={m.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[11px] text-slate-500 font-medium">{m.metric_name}</span>
                      <div className="text-sm font-bold text-slate-100 mt-0.5">
                        {m.value.toLocaleString()} <span className="text-xs font-normal text-slate-400">{m.unit}</span>
                      </div>
                      <span className="text-[10px] text-slate-500">{m.reporting_period}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === "news" && news && (
              <div className="space-y-3">
                {news.articles.length > 0 ? (
                  news.articles.map((art) => (
                    <div key={art.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="font-semibold text-cyan-400">{art.publisher}</span>
                        <span className="text-[11px] text-slate-500">
                          {new Date(art.published_at).toLocaleDateString()}
                        </span>
                      </div>
                      <h4 className="font-medium text-slate-200 line-clamp-2">{art.title}</h4>
                      {art.url && (
                        <a
                          href={art.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-cyan-400 mt-2"
                        >
                          Read Source Article <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500">No news articles indexed for this stock yet.</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column - 5 Cols (AI Research Chat) */}
        <div className="lg:col-span-5 sticky top-24">
          <ResearchChat
            symbol={overview.symbol}
            companyName={overview.name}
            instrumentId={overview.instrument_id}
          />
        </div>
      </div>

      {/* Research Report Modal */}
      <ResearchReportModal
        symbol={overview.symbol}
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
      />
    </div>
  );
}

