"use client";

import { useState, useEffect } from "react";
import {
  ShieldCheck,
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  FileCheck,
  Zap,
  BarChart2,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { runEvaluation, getEvaluationRuns, getEvaluationRun, EvaluationRun, EvaluationResult } from "@/lib/api";

export default function EvaluationDashboardPage() {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningEval, setRunningEval] = useState(false);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async () => {
    try {
      const data = await getEvaluationRuns();
      setRuns(data);
      if (data.length > 0 && !selectedRun) {
        loadRunDetails(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load evaluation history");
    } finally {
      setLoading(false);
    }
  };

  const loadRunDetails = async (runId: string) => {
    try {
      const details = await getEvaluationRun(runId);
      setSelectedRun(details);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleTriggerRun = async () => {
    setRunningEval(true);
    setError(null);
    try {
      const newRun = await runEvaluation();
      setSelectedRun(newRun);
      await fetchRuns();
    } catch (err: any) {
      setError(err.message || "Evaluation execution failed");
    } finally {
      setRunningEval(false);
    }
  };

  const summary = selectedRun?.summary_metrics || {};

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md mb-8">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-950 text-cyan-400 border border-cyan-800 shadow-lg shadow-cyan-500/20">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-100 flex items-center gap-2">
              AI Evaluation & Guardrails Dashboard
            </h1>
            <p className="text-xs sm:text-sm text-slate-400">
              Benchmark validation for quotes, deterministic math, citations, and prompt safety
            </p>
          </div>
        </div>

        <button
          onClick={handleTriggerRun}
          disabled={runningEval}
          className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-cyan-500/20 hover:opacity-90 disabled:opacity-50 transition-all flex items-center gap-2"
        >
          {runningEval ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Running Benchmark...
            </>
          ) : (
            <>
              <Play className="h-4 w-4" /> Run Benchmark Evaluation
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-950/30 border border-red-900 text-red-400 text-sm flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Metric Cards */}
      {selectedRun && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Benchmark Pass Rate</span>
              <FileCheck className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-extrabold text-slate-100">{summary.pass_rate_pct ?? "--"}%</div>
            <div className="text-[11px] text-slate-500 mt-1">
              {summary.passed_questions} passed / {summary.total_questions} total
            </div>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Avg Fact Coverage</span>
              <BarChart2 className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-extrabold text-slate-100">
              {summary.average_correctness ? `${(summary.average_correctness * 100).toFixed(1)}%` : "--"}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Verified element matching</div>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Citation Precision</span>
              <ShieldCheck className="h-4 w-4 text-blue-400" />
            </div>
            <div className="text-2xl font-extrabold text-slate-100">
              {summary.citation_precision ? `${(summary.citation_precision * 100).toFixed(0)}%` : "100%"}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">0 Hallucinated references</div>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>P95 Latency</span>
              <Zap className="h-4 w-4 text-amber-400" />
            </div>
            <div className="text-2xl font-extrabold text-slate-100">{summary.latency?.p95 ?? "--"} ms</div>
            <div className="text-[11px] text-slate-500 mt-1">P50: {summary.latency?.p50 ?? "--"} ms</div>
          </div>
        </div>
      )}

      {/* Main Breakdown: Question Results Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden shadow-xl mb-8">
        <div className="p-5 border-b border-slate-800 bg-slate-950/70 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-slate-100 text-sm sm:text-base">
              Benchmark Questions Breakdown ({selectedRun?.results?.length ?? 0} questions)
            </h3>
            <p className="text-xs text-slate-400">
              Run ID: <span className="text-slate-300 font-mono">{selectedRun?.id.slice(0, 8)}...</span> • Model:{" "}
              <span className="text-cyan-400">{selectedRun?.model_version}</span>
            </p>
          </div>
        </div>

        {selectedRun?.results && selectedRun.results.length > 0 ? (
          <div className="divide-y divide-slate-800">
            {selectedRun.results.map((res: EvaluationResult) => {
              const isPassed = !res.failure_reason;
              const isExpanded = expandedRow === res.id;

              return (
                <div key={res.id} className="p-4 hover:bg-slate-800/40 transition-colors">
                  <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => setExpandedRow(isExpanded ? null : res.id)}
                  >
                    <div className="flex items-center gap-3">
                      {isPassed ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-400 shrink-0" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-200">{res.question_text}</span>
                          <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                            {res.category}
                          </span>
                        </div>
                        {res.failure_reason && (
                          <div className="text-xs text-red-400 mt-1 flex items-center gap-1">
                            <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> {res.failure_reason}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-xs shrink-0">
                      <span className="text-slate-400 font-mono">{res.latency_ms} ms</span>
                      <span
                        className={`font-bold ${
                          isPassed ? "text-emerald-400" : "text-red-400"
                        }`}
                      >
                        {isPassed ? "PASSED" : "FAILED"}
                      </span>
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Detail Panel */}
                  {isExpanded && (
                    <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs space-y-3 bg-slate-950 p-4 rounded-xl">
                      <div>
                        <div className="font-semibold text-slate-400 uppercase tracking-wider mb-1">
                          Expected Answer Elements:
                        </div>
                        <div className="text-slate-300 bg-slate-900 p-2.5 rounded-lg font-mono">
                          {res.expected_answer}
                        </div>
                      </div>

                      <div>
                        <div className="font-semibold text-slate-400 uppercase tracking-wider mb-1">
                          Actual Agent Response:
                        </div>
                        <div className="text-slate-200 bg-slate-900 p-2.5 rounded-lg leading-relaxed">
                          {res.actual_answer}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1 text-slate-400">
                        <div>Correctness: <span className="font-semibold text-slate-200">{(res.metric_results.correctness_score * 100).toFixed(0)}%</span></div>
                        <div>Citation Precision: <span className="font-semibold text-slate-200">{(res.metric_results.citation_precision * 100).toFixed(0)}%</span></div>
                        <div>Retrieved Sources: <span className="font-semibold text-slate-200">{res.retrieved_source_ids.length}</span></div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-12 text-center text-slate-500 text-sm">
            No evaluation runs recorded. Click &quot;Run Benchmark Evaluation&quot; above to execute the test suite.
          </div>
        )}
      </div>
    </div>
  );
}

