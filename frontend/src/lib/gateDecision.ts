/**
 * Gate Decision Pure Function for ConsensusProbe 2.0
 * 
 * Boundary Contract (Section 4 & Section 9):
 * Gate triggers human intervention if and only if mean disagreement d STRICTLY exceeds tau_d.
 * When d <= tau_d, the pipeline auto-approves.
 */

export type GateOutcome = 'auto_approved' | 'needs_human_clarification';

export function evaluateGateDecision(meanDisagreement: number, tauD: number): GateOutcome {
  // Strict inequality boundary contract
  if (meanDisagreement > tauD) {
    return 'needs_human_clarification';
  }
  return 'auto_approved';
}

export function isGateEngaged(meanDisagreement: number, tauD: number): boolean {
  return meanDisagreement > tauD;
}
