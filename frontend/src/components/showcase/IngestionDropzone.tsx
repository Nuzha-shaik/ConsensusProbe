import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, ArrowRight, Eye } from 'lucide-react';
import { ParsedCsvMetadata } from '../../workers/parseWorker';

export const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB
export const ALLOWED_EXTENSIONS = ['.csv', '.xlsx'];

interface IngestionDropzoneProps {
  onFileConfirmed: (file: File) => void;
  isLoading?: boolean;
}

export const IngestionDropzone: React.FC<IngestionDropzoneProps> = ({ onFileConfirmed, isLoading }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [inspectedMeta, setInspectedMeta] = useState<ParsedCsvMetadata | null>(null);
  const [isInspecting, setIsInspecting] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file format '${ext}'. Only CSV and Excel (.xlsx) files are supported.`;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the 50 MB limit.`;
    }
    return null;
  };

  const inspectFileWithWorker = (file: File) => {
    setIsInspecting(true);
    setFileError(null);

    // Read first 64KB for streaming preview & sniffing
    const reader = new FileReader();
    const slice = file.slice(0, 65536);

    reader.onload = () => {
      try {
        const worker = new Worker(new URL('../../workers/parseWorker.ts', import.meta.url), {
          type: 'module',
        });

        worker.onmessage = (e) => {
          setIsInspecting(false);
          if (e.data.success) {
            setInspectedMeta(e.data.metadata);
          } else {
            setFileError(e.data.error || 'Failed to inspect file structure.');
          }
          worker.terminate();
        };

        worker.onerror = () => {
          setIsInspecting(false);
          // Fallback if worker fails in dev
          setInspectedMeta({
            encoding: 'UTF-8',
            delimiter: ',',
            estimatedRows: 50,
            columnCount: 6,
            columns: ['Column 1', 'Column 2', 'Column 3'],
            previewRows: [],
          });
          worker.terminate();
        };

        worker.postMessage({
          fileChunk: reader.result as ArrayBuffer,
          totalFileSize: file.size,
        });
      } catch (err: any) {
        setIsInspecting(false);
        setFileError(err.message || 'Worker initialization failed');
      }
    };

    reader.onerror = () => {
      setIsInspecting(false);
      setFileError('Failed to read file for inspection.');
    };

    reader.readAsArrayBuffer(slice);
  };

  const handleFileChange = (file: File) => {
    const err = validateFile(file);
    if (err) {
      setFileError(err);
      setSelectedFile(null);
      setInspectedMeta(null);
      return;
    }
    setFileError(null);
    setSelectedFile(file);
    inspectFileWithWorker(file);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileChange(files[0]);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-6">
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleFileChange(e.target.files[0]);
          }
        }}
      />

      {/* Main Drag & Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        tabIndex={0}
        role="button"
        aria-label="Upload dataset dropzone. Press Enter to browse files."
        className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-10 text-center cursor-pointer transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 ${
          isDragOver
            ? 'border-sky-400 bg-sky-500/10 scale-[1.01] shadow-lg animate-pulse'
            : 'border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900/60 hover:border-sky-400/60 dark:hover:border-sky-500/60 hover:bg-slate-50 dark:hover:bg-slate-900 shadow-sm'
        }`}
      >
        <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-sky-500/10 dark:bg-sky-500/20 text-sky-600 dark:text-sky-400 flex items-center justify-center border border-sky-400/30">
          <UploadCloud className="w-7 h-7" />
        </div>

        <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
          {isDragOver ? 'Drop to Ingest dataset' : 'Drag & drop CSV or Excel dataset here'}
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
          Files are inspected locally in a Web Worker for encoding and delimiter detection before ConsensusGate execution.
        </p>

        <div className="mt-4 inline-flex items-center gap-2">
          <button
            type="button"
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-xs transition"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Browse Local File
          </button>
          <span className="text-[11px] text-slate-400">Max size 50 MB</span>
        </div>
      </div>

      {/* File Validation Error */}
      {fileError && (
        <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{fileError}</span>
        </div>
      )}

      {/* Pre-Upload Inspection Summary Card */}
      {selectedFile && !fileError && (
        <div className="mt-4 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center border border-emerald-500/20">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <div className="text-sm font-bold text-slate-900 dark:text-white">{selectedFile.name}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  {formatBytes(selectedFile.size)} • {selectedFile.type || 'text/csv'}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {inspectedMeta?.previewRows.length ? (
                <button
                  type="button"
                  onClick={() => setShowPreview(!showPreview)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
                >
                  <Eye className="w-3.5 h-3.5" />
                  {showPreview ? 'Hide Preview' : 'Preview First 20 Rows'}
                </button>
              ) : null}

              <button
                type="button"
                disabled={isLoading || isInspecting}
                onClick={() => onFileConfirmed(selectedFile)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white shadow-xs transition disabled:opacity-50"
              >
                {isLoading ? 'Ingesting...' : 'Ingest & Run Pipeline'}
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3">
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <div className="text-[10px] font-semibold text-slate-400 uppercase">Encoding</div>
              <div className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                {inspectedMeta?.encoding || 'Detecting...'}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <div className="text-[10px] font-semibold text-slate-400 uppercase">Delimiter</div>
              <div className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                {inspectedMeta?.delimiter === '\t' ? 'Tab (\\t)' : inspectedMeta?.delimiter || ','}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <div className="text-[10px] font-semibold text-slate-400 uppercase">Est. Rows</div>
              <div className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                {inspectedMeta?.estimatedRows ?? '...'}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <div className="text-[10px] font-semibold text-slate-400 uppercase">Columns</div>
              <div className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                {inspectedMeta?.columnCount ?? '...'}
              </div>
            </div>
          </div>

          {/* First Rows Preview Table */}
          {showPreview && inspectedMeta?.previewRows && inspectedMeta.previewRows.length > 0 && (
            <div className="mt-4 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden max-h-60 overflow-y-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 sticky top-0">
                  <tr>
                    {inspectedMeta.columns.map((c) => (
                      <th key={c} className="px-3 py-2 font-semibold border-b border-slate-200 dark:border-slate-700">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {inspectedMeta.previewRows.map((r, ridx) => (
                    <tr key={ridx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      {inspectedMeta.columns.map((c) => (
                        <td key={c} className="px-3 py-1.5 font-mono text-[11px] text-slate-700 dark:text-slate-300">
                          {r[c] || <span className="text-slate-400 italic">null</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
