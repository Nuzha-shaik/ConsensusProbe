import React from 'react';
import { UploadCloud, Bot, ShieldCheck, Scale, CheckCircle2 } from 'lucide-react';

export type PipelineStepId = 'ingest' | 'propose' | 'audit' | 'gate' | 'result';

export interface PipelineStep {
  id: PipelineStepId;
  label: string;
  sublabel: string;
  icon: React.ElementType;
}

export const PIPELINE_STEPS: PipelineStep[] = [
  { id: 'ingest', label: '1. Ingest', sublabel: 'Stream & Sniff', icon: UploadCloud },
  { id: 'propose', label: '2. Propose', sublabel: 'K=3 Ensembles', icon: Bot },
  { id: 'audit', label: '3. Audit', sublabel: 'Disagreement d', icon: ShieldCheck },
  { id: 'gate', label: '4. Gate', sublabel: 'Human-in-Loop', icon: Scale },
  { id: 'result', label: '5. Result', sublabel: 'Cert & Export', icon: CheckCircle2 },
];

interface HeroStripProps {
  currentStep: PipelineStepId;
  onStepSelect?: (step: PipelineStepId) => void;
}

export const HeroStrip: React.FC<HeroStripProps> = ({ currentStep, onStepSelect }) => {
  const currentIndex = PIPELINE_STEPS.findIndex((s) => s.id === currentStep);

  return (
    <section className="w-full mb-8" aria-label="ConsensusProbe 2.0 Overview">
      {/* 10-Second Pitch */}
      <div className="text-center max-w-4xl mx-auto px-4 pt-2 pb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 dark:bg-sky-400/10 border border-sky-400/30 text-sky-700 dark:text-sky-300 text-xs font-semibold uppercase tracking-wider mb-3">
          Research Showcase • Multi-Agent Consensus
        </div>
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
          Three AI cleaners propose. A supervisor measures disagreement.{' '}
          <span className="text-sky-600 dark:text-sky-400">A human decides only when it matters.</span>
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          ConsensusProbe resolves tabular data ambiguity with an ensemble of independent cleaning agents,
          strict mathematical disagreement boundaries, and verifiable audit trails.
        </p>
      </div>

      {/* 5-Step Pipeline Strip */}
      <nav
        className="max-w-5xl mx-auto px-2"
        aria-label="Progress pipeline"
      >
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 p-1.5 rounded-2xl bg-slate-100/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 shadow-inner">
          {PIPELINE_STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isCompleted = idx < currentIndex;
            const isCurrent = idx === currentIndex;

            return (
              <button
                key={step.id}
                type="button"
                onClick={() => onStepSelect && onStepSelect(step.id)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 ${
                  isCurrent
                    ? 'bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 font-semibold shadow-xs border border-slate-200 dark:border-slate-700'
                    : isCompleted
                    ? 'text-emerald-700 dark:text-emerald-400 hover:bg-white/60 dark:hover:bg-slate-800/50'
                    : 'text-slate-500 dark:text-slate-400 hover:bg-white/40 dark:hover:bg-slate-800/30'
                }`}
                aria-current={isCurrent ? 'step' : undefined}
              >
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-sm font-bold ${
                    isCurrent
                      ? 'bg-sky-500/15 text-sky-600 dark:text-sky-400'
                      : isCompleted
                      ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                      : 'bg-slate-200 dark:bg-slate-800 text-slate-400'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold truncate leading-none mb-1 text-slate-900 dark:text-slate-100">
                    {step.label}
                  </div>
                  <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate leading-none">
                    {step.sublabel}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </nav>
    </section>
  );
};
