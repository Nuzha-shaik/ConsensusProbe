import React, { useState, useEffect, useRef } from 'react';
import { HelpCircle, AlertTriangle, ArrowRight, Check, X } from 'lucide-react';
import { ClarificationQuestion } from '../../adapters/runViewModel';

export interface RecordedDecision {
  timestamp: string;
  parameterName: string;
  selectedOptionId: number;
  description: string;
  affectedRows: number;
  applyToSimilar: boolean;
}

interface ClarificationModalProps {
  question: ClarificationQuestion;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedOptionId: number, applyToSimilar: boolean) => void;
  onRecordDecision?: (decision: RecordedDecision) => void;
  isLoading?: boolean;
}

export const ClarificationModal: React.FC<ClarificationModalProps> = ({
  question,
  isOpen,
  onClose,
  onConfirm,
  onRecordDecision,
  isLoading = false,
}) => {
  const [selectedOptionId, setSelectedOptionId] = useState<number>(
    question.options[0]?.optionId ?? 0
  );
  const [applyToSimilar, setApplyToSimilar] = useState<boolean>(true);
  const modalRef = useRef<HTMLDivElement>(null);

  // Always reset to the primary cleaning strategy when modal opens or question updates
  useEffect(() => {
    if (isOpen && question?.options && question.options.length > 0) {
      setSelectedOptionId(question.options[0].optionId);
    }
  }, [isOpen, question]);

  // Keyboard navigation & number-key shortcuts (1, 2)
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
      if (e.key === '1' && question.options[0]) {
        setSelectedOptionId(question.options[0].optionId);
      }
      if (e.key === '2' && question.options[1]) {
        setSelectedOptionId(question.options[1].optionId);
      }
      if (e.key === '3' && question.options[2]) {
        setSelectedOptionId(question.options[2].optionId);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, question.options, onClose]);

  if (!isOpen) return null;

  const selectedOpt = question.options.find((o) => o.optionId === selectedOptionId);

  const handleConfirmAction = () => {
    if (selectedOpt && onRecordDecision) {
      onRecordDecision({
        timestamp: new Date().toISOString(),
        parameterName: question.parameterName,
        selectedOptionId,
        description: selectedOpt.description,
        affectedRows: selectedOpt.affectedRowsCount,
        applyToSimilar,
      });
    }
    onConfirm(selectedOptionId, applyToSimilar);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="clarification-title"
    >
      <div
        ref={modalRef}
        className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-amber-500/30 shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="p-6 bg-amber-500/10 border-b border-amber-500/20 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center border border-amber-500/30">
              <HelpCircle className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider block">
                Human Gate Intervention Required
              </span>
              <h2 id="clarification-title" className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
                Ambiguity Resolution
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
            aria-label="Close clarification dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block mb-1">
              Conflicting Candidate Operations:
            </span>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
              {question.questionText}
            </p>
          </div>

          <div className="space-y-3">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider block">
              Select Desired Resolution Strategy (Press 1, 2, or 3):
            </span>

            {question.options.map((opt, idx) => {
              const isSelected = selectedOptionId === opt.optionId;
              return (
                <button
                  key={opt.optionId}
                  type="button"
                  onClick={() => setSelectedOptionId(opt.optionId)}
                  className={`w-full text-left p-4 rounded-2xl border transition-all flex items-start gap-3.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 ${
                    isSelected
                      ? 'border-sky-500 bg-sky-500/10 shadow-xs ring-1 ring-sky-500'
                      : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900'
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold font-mono border ${
                      isSelected
                        ? 'bg-sky-500 text-white border-sky-600'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
                    }`}
                  >
                    {idx + 1}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="text-xs sm:text-sm font-semibold text-slate-900 dark:text-white">
                      {opt.description}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-2 font-mono">
                      <span>Impact: Changes <strong>{opt.affectedRowsCount}</strong> rows</span>
                      {opt.exampleRids.length > 0 && (
                        <span>(Sample row IDs: {opt.exampleRids.join(', ')})</span>
                      )}
                    </div>
                  </div>

                  {isSelected && (
                    <div className="text-sky-600 dark:text-sky-400 shrink-0">
                      <Check className="w-5 h-5" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Scope Toggle */}
          <div className="pt-2 flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={applyToSimilar}
                onChange={(e) => setApplyToSimilar(e.target.checked)}
                className="w-4 h-4 rounded text-sky-600 accent-sky-500"
              />
              <span>Apply this resolution strategy to similar cells in column <strong>{question.parameterName}</strong></span>
            </label>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 bg-slate-50 dark:bg-slate-900/80 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-mono">
            {selectedOpt ? `Will apply to ${selectedOpt.affectedRowsCount} rows` : ''}
          </span>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={isLoading}
              onClick={handleConfirmAction}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white shadow-xs transition disabled:opacity-50"
            >
              {isLoading ? 'Applying...' : 'Confirm Decision & Update Export'}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
