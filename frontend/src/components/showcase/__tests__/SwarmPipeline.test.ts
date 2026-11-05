import { describe, it, expect } from 'vitest';
import { resolveModelMetadata, areModelsIndependent } from '../../../config/modelRegistry';
import { evaluateGateDecision, isGateEngaged } from '../../../lib/gateDecision';

describe('Model Registry (Rule R4)', () => {
  it('identifies deterministic research mock without styling as LLM', () => {
    const meta = resolveModelMetadata(null);
    expect(meta.label).toBe('Deterministic research mock');
    expect(meta.isMock).toBe(true);

    const heuristicMeta = resolveModelMetadata('heuristic-rule-engine');
    expect(heuristicMeta.label).toBe('Deterministic research mock');
    expect(heuristicMeta.isMock).toBe(true);
  });

  it('maps known LLM provider families while retaining raw label', () => {
    const gpt = resolveModelMetadata('gpt-4o-2024-08-06');
    expect(gpt.provider).toBe('OpenAI');
    expect(gpt.label).toBe('gpt-4o-2024-08-06');

    const claude = resolveModelMetadata('claude-3-5-sonnet-20241022');
    expect(claude.provider).toBe('Anthropic');
    expect(claude.label).toBe('claude-3-5-sonnet-20241022');
  });

  it('correctly assesses model independence', () => {
    expect(areModelsIndependent('gpt-4o', 'claude-3-5-sonnet')).toBe(true);
    expect(areModelsIndependent('gpt-4o', 'gpt-4o')).toBe(false);
    expect(areModelsIndependent(null, 'claude-3-5-sonnet')).toBe(false);
  });
});

describe('Threshold Simulator Boundary Flips (Strict d > tau_d)', () => {
  const measuredD = 0.4286;

  it('gate is engaged when tau_d is below measured d', () => {
    expect(evaluateGateDecision(measuredD, 0.40)).toBe('needs_human_clarification');
    expect(isGateEngaged(measuredD, 0.40)).toBe(true);
  });

  it('gate flips to auto_approved when tau_d crosses above measured d', () => {
    expect(evaluateGateDecision(measuredD, 0.45)).toBe('auto_approved');
    expect(isGateEngaged(measuredD, 0.45)).toBe(false);
  });

  it('boundary check: at exact match d === tau_d, strict inequality does not trigger gate', () => {
    expect(evaluateGateDecision(measuredD, measuredD)).toBe('auto_approved');
    expect(isGateEngaged(measuredD, measuredD)).toBe(false);
  });
});
