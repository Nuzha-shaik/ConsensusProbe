import { describe, it, expect } from 'vitest';
import fixtureData from '../__fixtures__/run_fixture.json';
import { adaptApiResponseToRunViewModel, RawApiDataset, RawApiCleanResponse } from '../runViewModel';

describe('RunViewModel Adapter', () => {
  it('correctly adapts raw API response and models unavailable fields', () => {
    const dataset: RawApiDataset = {
      id: fixtureData.dataset_id,
      filename: fixtureData.filename,
      rows: fixtureData.rows,
      cols: fixtureData.cols,
    };
    const cleanRes = fixtureData.clean_response as RawApiCleanResponse;

    const vm = adaptApiResponseToRunViewModel(dataset, cleanRes, 0.0);

    expect(vm.datasetId).toBe('test-dataset-contested-001');
    expect(vm.meanDisagreement).toBe(0.4286);
    expect(vm.gateDecision).toBe('needs_human_clarification');
    expect(vm.clarification).not.toBeNull();
    expect(vm.clarification?.options.length).toBe(2);

    // Rule R1 & R3: Unavailable fields are honestly marked
    expect(vm.candidatePlans.available).toBe(false);
    expect(vm.pairwiseDisagreements.available).toBe(false);
    expect(vm.canaryResults.available).toBe(false);
    expect(vm.proposerModel.available).toBe(false);
    expect(vm.tokenUsage.available).toBe(false);
  });

  it('mutation test: mutating API response consensus score alters RunViewModel metrics', () => {
    const dataset: RawApiDataset = {
      id: 'd1',
      filename: 'test.csv',
      rows: 50,
      cols: 4,
    };
    const cleanRes1: RawApiCleanResponse = {
      status: 'applied',
      consensus_score: 0.0,
      patch_summary: { deleted_rows: 0, edited_cells: 5, flagged_rows: 0 },
    };
    const cleanRes2: RawApiCleanResponse = {
      status: 'needs_clarification',
      consensus_score: 0.75,
      patch_summary: { deleted_rows: 2, edited_cells: 18, flagged_rows: 4 },
    };

    const vm1 = adaptApiResponseToRunViewModel(dataset, cleanRes1, 0.2);
    const vm2 = adaptApiResponseToRunViewModel(dataset, cleanRes2, 0.2);

    expect(vm1.meanDisagreement).not.toBe(vm2.meanDisagreement);
    expect(vm1.gateDecision).toBe('auto_approved');
    expect(vm2.gateDecision).toBe('needs_human_clarification');
    expect(vm1.patchSummary?.editedCells).toBe(5);
    expect(vm2.patchSummary?.editedCells).toBe(18);
  });
});
