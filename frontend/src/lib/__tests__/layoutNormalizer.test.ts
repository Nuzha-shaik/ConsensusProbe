import { describe, it, expect } from 'vitest';
import { isTwoLevelCrosstab, normalizeCrosstab, isSummaryLabel } from '../layoutNormalizer';

describe('layoutNormalizer', () => {
  it('correctly identifies summary labels', () => {
    expect(isSummaryLabel('Grand Total')).toBe(true);
    expect(isSummaryLabel('Total')).toBe(true);
    expect(isSummaryLabel('Subtotal')).toBe(true);
    expect(isSummaryLabel('CA-2011-100293')).toBe(false);
  });

  it('detects a two-level crosstab and unpivots it cleanly', () => {
    const rawRows = [
      ['', 'Region', 'North', '', 'South', ''],
      ['', 'Channel', 'Retail', 'Online', 'Retail', 'Online'],
      ['OrderID', 'OrderDate', '', '', '', ''],
      ['ORD-1', '2023-01-01', '100', '', '', ''],
      ['ORD-2', '2023-01-02', '', '250', '', ''],
      ['ORD-3', '2023-01-03', '', '', '', '500'],
      ['Grand Total', '', '100', '250', '', '500'],
    ];

    expect(isTwoLevelCrosstab(rawRows)).toBe(true);

    const result = normalizeCrosstab(rawRows);
    expect(result.isCrosstab).toBe(true);
    expect(result.droppedSummaryCount).toBe(1);
    expect(result.headers).toEqual(['Region', 'Channel', 'OrderID', 'OrderDate', 'Sales']);
    expect(result.records.length).toBe(3);

    // Records should be sorted by Region, Channel, OrderID
    expect(result.records[0]).toEqual(['North', 'Online', 'ORD-2', '2023-01-02', '250']);
    expect(result.records[1]).toEqual(['North', 'Retail', 'ORD-1', '2023-01-01', '100']);
    expect(result.records[2]).toEqual(['South', 'Online', 'ORD-3', '2023-01-03', '500']);
  });

  it('leaves standard flat tables untouched', () => {
    const flatRows = [
      ['ID', 'Name', 'Score'],
      ['1', 'Alice', '95'],
      ['2', 'Bob', '88'],
    ];

    expect(isTwoLevelCrosstab(flatRows)).toBe(false);

    const result = normalizeCrosstab(flatRows);
    expect(result.isCrosstab).toBe(false);
    expect(result.headers).toEqual(['ID', 'Name', 'Score']);
    expect(result.records.length).toBe(2);
  });
});
