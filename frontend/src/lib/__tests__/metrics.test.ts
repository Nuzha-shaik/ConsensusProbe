import { describe, it, expect } from 'vitest';
import {
  calculateHealthScore,
  computeRunDiff,
  computeNumericHistogram,
  computeCategoricalFrequencies,
  DEFAULT_HEALTH_WEIGHTS,
} from '../metrics';

describe('Health Score Metric (Rule R2 truthfulness)', () => {
  const perfectDataset = [
    { id: 1, name: 'Alpha', price: 100 },
    { id: 2, name: 'Beta', price: 200 },
    { id: 3, name: 'Gamma', price: 300 },
  ];

  it('computes 100 for clean complete dataset', () => {
    const res = calculateHealthScore(perfectDataset);
    expect(res.score).toBe(100);
    expect(res.completeness).toBe(1.0);
    expect(res.uniqueness).toBe(1.0);
    expect(res.nullCells).toBe(0);
    expect(res.duplicateRows).toBe(0);
  });

  it('mutation test: mutating nulls or duplicates alters the score', () => {
    const mutatedWithNulls = [
      { id: 1, name: 'Alpha', price: null },
      { id: 2, name: null, price: 200 },
      { id: 3, name: 'Gamma', price: 300 },
    ];
    const res1 = calculateHealthScore(perfectDataset);
    const res2 = calculateHealthScore(mutatedWithNulls);

    expect(res2.score).toBeLessThan(res1.score);
    expect(res2.nullCells).toBe(2);
    expect(res2.completeness).toBeLessThan(1.0);
  });

  it('detects duplicate row penalties on uniqueness', () => {
    const withDuplicates = [
      { id: 1, name: 'Alpha', price: 100 },
      { id: 1, name: 'Alpha', price: 100 },
      { id: 2, name: 'Beta', price: 200 },
    ];
    const res = calculateHealthScore(withDuplicates);
    expect(res.duplicateRows).toBe(1);
    expect(res.uniqueness).toBeCloseTo(2 / 3, 2);
    expect(res.score).toBeLessThan(100);
  });
});

describe('Run Diffing', () => {
  it('correctly categorizes edited, imputed, and dropped rows', () => {
    const orig = [
      { id: 1, category: 'Electronics', price: null },
      { id: 2, category: 'Apparel', price: 50 },
      { id: 3, category: 'Books', price: 20 },
    ];
    const cleaned = [
      { id: 1, category: 'Electronics', price: 35 }, // imputed price
      { id: 2, category: 'Apparel & Clothing', price: 50 }, // edited category
      // row 3 dropped
    ];

    const diff = computeRunDiff(orig, cleaned);
    expect(diff.totalRowsOriginal).toBe(3);
    expect(diff.totalRowsCleaned).toBe(2);
    expect(diff.droppedRowCount).toBe(1);
    expect(diff.imputedCellCount).toBe(1);
    expect(diff.editedCellCount).toBe(1);
  });
});

describe('Histograms and Distributions', () => {
  it('computes numeric bins correctly', () => {
    const values = [10, 20, 30, 40, 50];
    const bins = computeNumericHistogram(values, 2);
    expect(bins.length).toBe(2);
    expect(bins[0].count + bins[1].count).toBe(5);
  });

  it('computes categorical frequencies', () => {
    const items = ['A', 'B', 'A', 'C', 'A', 'B'];
    const freqs = computeCategoricalFrequencies(items);
    expect(freqs[0].value).toBe('A');
    expect(freqs[0].count).toBe(3);
    expect(freqs[0].percentage).toBe(50);
  });
});
