/**
 * RunViewModel and Adapter for ConsensusProbe 2.0
 * 
 * Enforces Rule R1 (Core Freeze), R2 (Truthful UI), and R3 (Real Agent State).
 * Any telemetry field omitted by the backend API is strictly typed as UnavailableField.
 */

export interface UnavailableField {
  readonly available: false;
  readonly reason: string;
}

export interface AvailableField<T> {
  readonly available: true;
  readonly value: T;
}

export type TelemetryField<T> = AvailableField<T> | UnavailableField;

export function unavailable(reason: string): UnavailableField {
  return { available: false, reason };
}

export function available<T>(value: T): AvailableField<T> {
  return { available: true, value };
}

export interface ClarificationOption {
  optionId: number;
  description: string;
  affectedRowsCount: number;
  exampleRids: number[];
}

export interface ClarificationQuestion {
  questionText: string;
  parameterName: string;
  options: ClarificationOption[];
}

export interface PatchSummary {
  deletedRows: number;
  editedCells: number;
  flaggedRows: number;
}

export type GateDecisionStatus = 'auto_approved' | 'needs_human_clarification' | 'no_changes';

export interface CandidatePlanSummary {
  planIndex: number;
  confidence: number;
  description?: string;
}

export interface RunViewModel {
  datasetId: string;
  filename: string;
  rowCount: number;
  colCount: number;

  // Consensus & Gate Metrics (Available from Engine)
  meanDisagreement: number; // mean d
  tauD: number; // threshold tau_d
  gateDecision: GateDecisionStatus;

  // Resolution & Patch Data
  clarification: ClarificationQuestion | null;
  patchSummary: PatchSummary | null;

  // Pipeline Telemetry Fields (Audited in docs/DATA_AVAILABILITY.md)
  candidatePlans: TelemetryField<{
    planCount: number;
    plans: CandidatePlanSummary[];
  }>;
  pairwiseDisagreements: TelemetryField<number[][]>;
  canaryResults: TelemetryField<{
    planted: number;
    caught: number;
    integrityVerified: boolean;
  }>;
  proposerModel: TelemetryField<{ modelId: string; provider: string }>;
  auditorModel: TelemetryField<{ modelId: string; provider: string }>;
  isLiveLLM: TelemetryField<boolean>;
  executionLatencyMs: TelemetryField<number>;
  tokenUsage: TelemetryField<{ promptTokens: number; completionTokens: number; totalTokens: number }>;

  timestamp: string;
}

export interface RawApiDataset {
  id: string;
  filename: string;
  rows: number;
  cols: number;
}

export interface RawApiCleanResponse {
  status: 'needs_clarification' | 'applied' | 'no_changes';
  consensus_score: number;
  question?: {
    question_text?: string;
    parameter_name?: string;
    options?: Array<{
      option_id: number;
      description: string;
      affected_rows_count: number;
      example_rids: number[];
    }>;
  } | null;
  patch_summary?: {
    deleted_rows?: number;
    edited_cells?: number;
    flagged_rows?: number;
  } | null;
}

export function adaptApiResponseToRunViewModel(
  dataset: RawApiDataset,
  response: RawApiCleanResponse,
  tauD: number = 0.0
): RunViewModel {
  const meanDisagreement = typeof response.consensus_score === 'number' ? response.consensus_score : 0.0;
  
  let gateDecision: GateDecisionStatus;
  if (response.status === 'needs_clarification') {
    gateDecision = 'needs_human_clarification';
  } else if (response.status === 'no_changes') {
    gateDecision = 'no_changes';
  } else {
    gateDecision = 'auto_approved';
  }

  const clarification: ClarificationQuestion | null = response.question
    ? {
        questionText: response.question.question_text || 'Select resolution strategy',
        parameterName: response.question.parameter_name || 'strategy',
        options: (response.question.options || []).map((opt) => ({
          optionId: opt.option_id,
          description: opt.description,
          affectedRowsCount: opt.affected_rows_count,
          exampleRids: opt.example_rids || [],
        })),
      }
    : null;

  const patchSummary: PatchSummary | null = response.patch_summary
    ? {
        deletedRows: response.patch_summary.deleted_rows || 0,
        editedCells: response.patch_summary.edited_cells || 0,
        flaggedRows: response.patch_summary.flagged_rows || 0,
      }
    : null;

  return {
    datasetId: dataset.id,
    filename: dataset.filename,
    rowCount: dataset.rows,
    colCount: dataset.cols,
    meanDisagreement,
    tauD,
    gateDecision,
    clarification,
    patchSummary,
    candidatePlans: unavailable('Candidate plan proposals and per-cell operations are internal to server and omitted from API response'),
    pairwiseDisagreements: unavailable('Pairwise disagreement matrix is internal to engine and omitted from API response'),
    canaryResults: unavailable('Backend API does not support runtime canary injection or telemetry'),
    proposerModel: unavailable('Model identifiers not reported by the backend API (Deterministic research mock)'),
    auditorModel: unavailable('Model identifiers not reported by the backend API (Deterministic research mock)'),
    isLiveLLM: available(false),
    executionLatencyMs: unavailable('Agent execution timings not reported by API'),
    tokenUsage: unavailable('Token usage not reported by API'),
    timestamp: new Date().toISOString(),
  };
}
