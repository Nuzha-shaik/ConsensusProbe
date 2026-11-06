import React from 'react';
import { Bot, ShieldAlert, Scale, CheckCircle2, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';
import { RunViewModel } from '../../adapters/runViewModel';
import { resolveModelMetadata, areModelsIndependent } from '../../config/modelRegistry';

interface SwarmAgentCardsProps {
  viewModel: RunViewModel;
  simulatedTauD?: number;
  isRunning?: boolean;
  onOpenClarification?: () => void;
}

export const SwarmAgentCards: React.FC<SwarmAgentCardsProps> = ({
  viewModel,
  simulatedTauD,
  isRunning = false,
  onOpenClarification,
}) => {
  const effectiveTau = typeof simulatedTauD === 'number' ? simulatedTauD : viewModel.tauD;
  const isEngaged = viewModel.meanDisagreement > effectiveTau && viewModel.gateDecision === 'needs_human_clarification';

  const proposerMeta = resolveModelMetadata(
    viewModel.proposerModel.available ? viewModel.proposerModel.value.modelId : null
  );
  const auditorMeta = resolveModelMetadata(
    viewModel.auditorModel.available ? viewModel.auditorModel.value.modelId : null
  );
  const isIndependent = areModelsIndependent(
    viewModel.proposerModel.available ? viewModel.proposerModel.value.modelId : null,
    viewModel.auditorModel.available ? viewModel.auditorModel.value.modelId : null
  );

  return (
    <div className="w-full mb-6" aria-label="Visual Multi-Agent Command Swarm">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-sky-500 animate-ping"></span>
          <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            Consensus Multi-Agent Command Swarm
          </h2>
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
          K=3 Ensemble • $\tau_d = {effectiveTau.toFixed(2)}$
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Agent 1: Cleaner (Cyan) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-cyan-500/30 dark:border-cyan-500/20 shadow-xs relative overflow-hidden transition-all hover:border-cyan-500/50">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-9 h-9 rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 flex items-center justify-center border border-cyan-500/20 ${
                  isRunning ? 'animate-pulse ring-2 ring-cyan-400' : ''
                }`}
              >
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-wider block">
                  Agent 1 • Proposer
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Cleaner Ensemble</h3>
              </div>
            </div>

            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
              {proposerMeta.label}
            </span>
          </div>

          <div className="space-y-1.5 text-xs">
            <p className="text-slate-700 dark:text-slate-300 font-medium">
              Generated 3 candidate plans ($K=3$)
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Evaluated schema profiles for deduplication and missing value resolution across {viewModel.colCount} columns.
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-500">
            <span>State: {isRunning ? 'Synthesizing...' : 'Ensemble Ready'}</span>
            <span className="text-cyan-600 dark:text-cyan-400 font-semibold">3 Plans</span>
          </div>
        </div>

        {/* Agent 2: Supervisor (Indigo) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-indigo-500/30 dark:border-indigo-500/20 shadow-xs relative overflow-hidden transition-all hover:border-indigo-500/50">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center border border-indigo-500/20 ${
                  isRunning ? 'animate-pulse ring-2 ring-indigo-400' : ''
                }`}
              >
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider block">
                  Agent 2 • Auditor
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Supervisor Auditor</h3>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {isIndependent && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                  Independent Auditor
                </span>
              )}
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                {auditorMeta.label}
              </span>
            </div>
          </div>

          <div className="space-y-1.5 text-xs">
            <div className="flex items-baseline gap-2">
              <span className="text-slate-500 dark:text-slate-400">Pairwise Disagreement:</span>
              <span className="text-base font-bold font-mono text-indigo-600 dark:text-indigo-400">
                d = {viewModel.meanDisagreement.toFixed(4)}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Measured semantic divergence between candidate plan patches.
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-500">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              Canary Audit: Passed
            </span>
            <span>{viewModel.meanDisagreement > 0 ? 'Ambiguity Found' : 'Unanimous'}</span>
          </div>
        </div>

        {/* Agent 3: Gatekeeper (Emerald / Amber) */}
        <div
          className={`p-5 rounded-2xl bg-white dark:bg-slate-900 border shadow-xs relative overflow-hidden transition-all ${
            isEngaged
              ? 'border-amber-500/40 dark:border-amber-500/30 hover:border-amber-500/60'
              : 'border-emerald-500/40 dark:border-emerald-500/30 hover:border-emerald-500/60'
          }`}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center border ${
                  isEngaged
                    ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                }`}
              >
                {isEngaged ? <AlertTriangle className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5" />}
              </div>
              <div>
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider block ${
                    isEngaged ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'
                  }`}
                >
                  Agent 3 • Policy Decision
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Gatekeeper</h3>
              </div>
            </div>

            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                isEngaged
                  ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30'
                  : 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30'
              }`}
            >
              {isEngaged ? 'Human Clarification' : 'Auto-Approved'}
            </span>
          </div>

          <div className="space-y-1.5 text-xs">
            <p className="text-slate-700 dark:text-slate-300 font-medium">
              {isEngaged
                ? `Disagreement (${viewModel.meanDisagreement.toFixed(4)}) > Threshold (${effectiveTau.toFixed(2)})`
                : `Disagreement (${viewModel.meanDisagreement.toFixed(4)}) <= Threshold (${effectiveTau.toFixed(2)})`}
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {isEngaged
                ? 'Engaging human intervention to resolve conflicting candidate operations.'
                : 'Plan consensus achieved; patches unified and verified automatically.'}
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-500">
            <span>Gate Rule: d &gt; &tau;<sub>d</sub></span>
            <span
              className={`font-semibold ${
                isEngaged ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'
              }`}
            >
              {isEngaged ? 'Clarify Pending' : 'Direct Apply'}
            </span>
          </div>

          {isEngaged && onOpenClarification && (
            <button
              type="button"
              onClick={onOpenClarification}
              className="mt-3 w-full py-2 px-3 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold shadow-xs flex items-center justify-center gap-1.5 transition-all hover:scale-[1.01] cursor-pointer"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Review & Resolve Conflicts Now</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
