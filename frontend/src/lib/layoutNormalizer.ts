/**
 * Deterministic Layout Normalizer for Multi-Level Cross-Tabs (Fix Ladder Rung 2, Rule R3).
 *
 * Automatically detects and unpivots two-level stacked cross-tab structures
 * before feeding the tidy dataset into the K=3 ensemble.
 */

export interface NormalizedResult {
  isCrosstab: boolean;
  headers: string[];
  records: string[][];
  droppedSummaryCount: number;
}

export function isSummaryLabel(label: string): boolean {
  const lower = label.trim().toLowerCase();
  return (
    lower.includes('total') ||
    lower.includes('grand total') ||
    lower.includes('summary') ||
    lower.includes('subtotal') ||
    lower.includes('average')
  );
}

/**
 * Detects if a dataset has a two-level cross-tab header structure.
 */
export function isTwoLevelCrosstab(rows: string[][]): boolean {
  if (!rows || rows.length < 4) return false;
  const row0 = rows[0] || [];
  const row1 = rows[1] || [];

  // Check if row 0 has repeated or sparse headers with empty gaps
  let emptyGaps = 0;
  for (let c = 2; c < row0.length; c++) {
    if (!row0[c] || row0[c].trim() === '') emptyGaps++;
  }

  // Row 1 should have subcategory values
  const hasSubHeaders = row1.slice(2).filter((c) => c && c.trim() !== '').length >= 3;
  return emptyGaps >= 2 && hasSubHeaders;
}

/**
 * Normalizes two-level cross-tab rows into a tidy tabular record format.
 */
export function normalizeCrosstab(rows: string[][]): NormalizedResult {
  if (!isTwoLevelCrosstab(rows)) {
    return {
      isCrosstab: false,
      headers: rows[0] || [],
      records: rows.slice(1),
      droppedSummaryCount: 0,
    };
  }

  const row0 = rows[0] || [];
  const row1 = rows[1] || [];
  const row2 = rows[2] || [];

  const topCategoryName = (row0[1] || '').trim() || 'Group';
  const subCategoryName = (row1[1] || '').trim() || 'Category';
  const key0Name = (row2[0] || '').trim() || 'ID';
  const key1Name = (row2[1] || '').trim() || 'Date';
  const measureName = 'Sales';

  // Forward fill row 0
  const topHeaders: string[] = [];
  let currentTop = '';
  for (let c = 0; c < row0.length; c++) {
    const val = (row0[c] || '').trim();
    if (c >= 2 && val) {
      currentTop = val;
    }
    topHeaders.push(currentTop);
  }

  // Identify active value columns
  const valueColumns: Array<{ colIndex: number; topVal: string; subVal: string }> = [];
  for (let c = 2; c < Math.min(row0.length, row1.length); c++) {
    const tVal = topHeaders[c];
    const sVal = (row1[c] || '').trim();
    if (tVal && sVal) {
      valueColumns.push({ colIndex: c, topVal: tVal, subVal: sVal });
    }
  }

  const outputHeaders = [topCategoryName, subCategoryName, key0Name, key1Name, measureName];
  const records: string[][] = [];
  let droppedSummaryCount = 0;

  for (let r = 3; r < rows.length; r++) {
    const row = rows[r] || [];
    if (!row.some((cell) => cell && cell.trim() !== '')) continue;

    const key0 = (row[0] || '').trim();
    if (isSummaryLabel(key0)) {
      droppedSummaryCount++;
      continue;
    }

    const key1 = (row[1] || '').trim();

    for (const { colIndex, topVal, subVal } of valueColumns) {
      if (colIndex < row.length) {
        const cell = (row[colIndex] || '').trim();
        if (cell) {
          records.push([topVal, subVal, key0, key1, cell]);
        }
      }
    }
  }

  // Deterministic sort: top, sub, key0
  records.sort((a, b) => {
    if (a[0] !== b[0]) return a[0].localeCompare(b[0]);
    if (a[1] !== b[1]) return a[1].localeCompare(b[1]);
    return a[2].localeCompare(b[2]);
  });

  return {
    isCrosstab: true,
    headers: outputHeaders,
    records,
    droppedSummaryCount,
  };
}
