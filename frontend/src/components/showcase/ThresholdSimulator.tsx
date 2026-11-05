import React from 'react';
import { Sliders, RotateCcw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { evaluateGateDecision } from '../../lib/gateDecision';

interface ThresholdSimulatorProps {
  meanDisagreement: number;
  simulatedTauD: number;
  onChangeTauD: (val: number) => void;
  onReset?: () => void;
}

export const ThresholdSimulator: React.FC<ThresholdSimulatorProps> = ({
  meanDisagreement,
  simulatedTauD,
  onChangeTauD,
  onReset,
}) => {
  const gateOutcome = evaluateGateDecision(meanDisagreement, simulatedTauD);
  const isEngaged = gateOutcome === 'needs_human_clarification';

  return (
    <div
      className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs mb-6"
      aria-label="Threshold Simulator"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center border border-sky-400/20">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Disagreement Threshold ($\tau_d$) Simulator
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Simulate policy boundary: gate triggers human review when $d &gt; \tau_d$
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold border ${
              isEngaged
                ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30'
                : 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30'
            }`}
          >
            {isEngaged ? <AlertCircle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
            <span>{isEngaged ? 'Human Clarification Engaged' : 'Auto-Approved'}</span>
          </div>

          {onReset && (
            <button
              type="button"
              onClick={onReset}
              title="Reset threshold to default (0.00)"
              className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-600 dark:text-slate-400">
            Current Disagreement: <strong className="text-slate-900 dark:text-white font-bold">{meanDisagreement.toFixed(4)}</strong>
          </span>
          <span className="text-slate-600 dark:text-slate-400">
            Simulation Threshold $\tau_d$: <strong className="text-sky-600 dark:text-sky-400 font-bold">{simulatedTauD.toFixed(2)}</strong>
          </span>
        </div>

        {/* Range Slider */}
        <div className="relative pt-1">
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={simulatedTauD}
            onChange={(e) => onChangeTauD(parseFloat(e.target.value))}
            aria-label="Simulation threshold tau_d slider"
            className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-500"
          />
          <div className="flex justify-between text-[10px] text-slate-400 dark:text-slate-500 font-mono mt-1">
            <span>0.00 (Strict: Clarify any conflict)</span>
            <span>0.50</span>
            <span>1.00 (Permissive: Auto-approve all)</span>
          </div>
        </div>

        <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between pt-1">
          <span>
            Flip Point: Threshold crosses at exactly $\tau_d = {meanDisagreement.toFixed(4)}$
          </span>
          <span className="font-mono text-[10px]">
            Strict rule: $d ({meanDisagreement.toFixed(4)}) &gt; \tau_d ({simulatedTauD.toFixed(2)})
          </span>
        </div>
      </div>
    </div>
  );
};
