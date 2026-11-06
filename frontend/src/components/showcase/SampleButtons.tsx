import React from 'react';
import { Sparkles, AlertCircle, FileSpreadsheet } from 'lucide-react';

interface SampleButtonsProps {
  onLoadSample: (sampleType: 'clean' | 'contested' | 'sales') => Promise<void> | void;
  isLoading?: boolean;
}

export const SampleButtons: React.FC<SampleButtonsProps> = ({ onLoadSample, isLoading }) => {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3 mt-4" aria-label="One-click research samples">
      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
        Quick Experiments:
      </span>
      <button
        type="button"
        disabled={isLoading}
        onClick={() => onLoadSample('clean')}
        className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 transition shadow-xs disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
      >
        <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
        Try a clean file (Auto-Approve d=0)
      </button>

      <button
        type="button"
        disabled={isLoading}
        onClick={() => onLoadSample('contested')}
        className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/30 transition shadow-xs disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500"
      >
        <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
        Try a contested file (Triggers Gate d&gt;0)
      </button>

      <button
        type="button"
        disabled={isLoading}
        onClick={() => onLoadSample('sales')}
        className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-sky-500/10 hover:bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-sky-500/30 transition shadow-xs disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
      >
        <FileSpreadsheet className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
        Try Sales Data 3 (Clean 822 rows)
      </button>
    </div>
  );
};
