/**
 * Model Registry for ConsensusProbe 2.0 (Rule R4)
 * 
 * Config-driven model resolver. The label is ALWAYS the raw reported identifier.
 * Provider-family patterns determine icon and styling only.
 * Deterministic mocks are explicitly labelled "Deterministic research mock".
 */

export interface ModelMetadata {
  readonly id: string;
  readonly label: string;
  readonly provider: string;
  readonly isMock: boolean;
  readonly badgeColor: string; // Tailwind semantic color key
}

export function resolveModelMetadata(rawModelId?: string | null): ModelMetadata {
  if (!rawModelId || rawModelId.toLowerCase().includes('mock') || rawModelId.toLowerCase().includes('heuristic')) {
    return {
      id: rawModelId || 'deterministic-mock',
      label: 'Deterministic research mock',
      provider: 'ConsensusProbe Heuristics',
      isMock: true,
      badgeColor: 'slate',
    };
  }

  const lower = rawModelId.toLowerCase();

  if (lower.includes('gpt') || lower.includes('openai')) {
    return {
      id: rawModelId,
      label: rawModelId,
      provider: 'OpenAI',
      isMock: false,
      badgeColor: 'emerald',
    };
  }

  if (lower.includes('claude') || lower.includes('anthropic')) {
    return {
      id: rawModelId,
      label: rawModelId,
      provider: 'Anthropic',
      isMock: false,
      badgeColor: 'amber',
    };
  }

  if (lower.includes('gemini') || lower.includes('google')) {
    return {
      id: rawModelId,
      label: rawModelId,
      provider: 'Google',
      isMock: false,
      badgeColor: 'sky',
    };
  }

  // Unknown identifier: display raw string directly per R4
  return {
    id: rawModelId,
    label: rawModelId,
    provider: 'External Provider',
    isMock: false,
    badgeColor: 'indigo',
  };
}

export function areModelsIndependent(proposerId?: string | null, auditorId?: string | null): boolean {
  if (!proposerId || !auditorId) return false;
  return proposerId.trim().toLowerCase() !== auditorId.trim().toLowerCase();
}
