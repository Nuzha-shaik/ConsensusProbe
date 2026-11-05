import React, { useState } from 'react';
import { Clock, Play, ChevronDown, ChevronUp, Cpu, Coins } from 'lucide-react';
import { RunViewModel } from '../../adapters/runViewModel';

interface AgentTraceTimelineProps {
  viewModel: RunViewModel;
}

export const AgentTraceTimeline: React.FC<AgentTraceTimelineProps> = ({ viewModel }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeStepIndex, setActiveStepIndex] = useState<number | null>(null);

  const steps = [
    {
      agent: 'Cleaner Agent Ensemble',
      action: 'Generated 3 candidate plans from column null/duplicate profiles',
      latency: viewModel.executionLatencyMs.available ? `${viewModel.executionLatencyMs.value} ms` : '—',
      tokens: viewModel.tokenUsage.available ? `${viewModel.tokenUsage.value.totalTokens}` : '—',
    },
    {
      agent: 'Supervisor Auditor',
      action: `Calculated pairwise semantic divergence d = ${viewModel.meanDisagreement.toFixed(4)} and checked canaries`,
      latency: '—',
      tokens: '—',
    },
    {
      agent: 'Gatekeeper Policy',
      action: viewModel.gateDecision === 'needs_human_clarification'
        ? 'Engaged interactive human clarification for ambiguous operations'
        : 'Auto-approved patch unification based on strict consensus',
      latency: '—',
      tokens: '—',
    },
  ];

  const handleReplay = () => {
    setActiveStepIndex(0);
    setTimeout(() => setActiveStepIndex(1), 500);
    setTimeout(() => setActiveStepIndex(2), 1000);
    setTimeout(() => setActiveStepIndex(null), 1600);
  };

  return (
    <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs mb-6">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-left focus:outline-none"
        >
          <div className="w-7 h-7 rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center">
            <Clock className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Agent Trace Timeline
            </h3>
            <span className="text-[10px] text-slate-400 dark:text-slate-500 italic block">
              Reconstructed from run summary (Rule R3 compliant)
            </span>
          </div>
        </button>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleReplay}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition"
          >
            <Play className="w-3 h-3 text-sky-500" />
            <span>Replay Trace</span>
          </button>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-3">
          {steps.map((st, idx) => {
            const isReplaying = activeStepIndex === idx;
            return (
              <div
                key={st.agent}
                className={`p-3 rounded-xl border transition-all ${
                  isReplaying
                    ? 'border-sky-400 bg-sky-50 dark:bg-sky-950/40 scale-[1.01]'
                    : 'border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">{st.agent}</span>
                  <div className="flex items-center gap-3 text-[10px] text-slate-400 font-mono">
                    <span title="Execution Latency">Latency: {st.latency}</span>
                    <span title="Token Consumption">Tokens: {st.tokens}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">{st.action}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
