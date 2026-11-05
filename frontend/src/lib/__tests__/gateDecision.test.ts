import { describe, it, expect } from 'vitest';
import { evaluateGateDecision, isGateEngaged } from '../gateDecision';

describe('gateDecision strict boundary contract', () => {
  it('auto-approves when d is strictly less than tau_d', () => {
    expect(evaluateGateDecision(0.2, 0.4)).toBe('auto_approved');
    expect(isGateEngaged(0.2, 0.4)).toBe(false);
  });

  it('auto-approves at exact boundary d === tau_d (strict > requirement)', () => {
    expect(evaluateGateDecision(0.4, 0.4)).toBe('auto_approved');
    expect(isGateEngaged(0.4, 0.4)).toBe(false);
  });

  it('triggers human clarification when d strictly exceeds tau_d', () => {
    expect(evaluateGateDecision(0.4001, 0.4)).toBe('needs_human_clarification');
    expect(isGateEngaged(0.4001, 0.4)).toBe(true);
  });

  it('handles zero threshold tau_d = 0.0 correctly', () => {
    expect(evaluateGateDecision(0.0, 0.0)).toBe('auto_approved');
    expect(evaluateGateDecision(0.0001, 0.0)).toBe('needs_human_clarification');
  });
});
