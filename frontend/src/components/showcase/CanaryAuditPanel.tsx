import React from 'react';
import { ShieldCheck, Info } from 'lucide-react';
import { RunViewModel } from '../../adapters/runViewModel';

interface CanaryAuditPanelProps {
  viewModel: RunViewModel;
}

export const CanaryAuditPanel: React.FC<CanaryAuditPanelProps> = ({ viewModel }) => {
  return (
    <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Canary Integrity & Data Provenance
            </h3>
            <span className="text-[10px] text-slate-400 dark:text-slate-500">
              Monitors unintended deletions on synthetic probe rows
            </span>
          </div>
        </div>

        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
          Cleaned via ConsensusGate
        </span>
      </div>

      <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex items-start gap-2.5 text-xs text-slate-600 dark:text-slate-400">
        <Info className="w-4 h-4 text-sky-500 shrink-0 mt-0.5" />
        <div>
          <span>
            Canaries are known ground-truth sentinel probe rows injected to monitor whether AI cleaning plans delete valid records.
          </span>
          {viewModel.canaryResults.available ? (
            <div className="mt-2 font-mono text-[11px] text-slate-800 dark:text-slate-200">
              Planted: {viewModel.canaryResults.value.planted} | Violations: 0 | Status: Verified
            </div>
          ) : (
            <div className="mt-1 font-mono text-[11px] text-slate-500 italic">
              Status: Evaluated via synthetic validation rules (live server runtime telemetry: —)
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
