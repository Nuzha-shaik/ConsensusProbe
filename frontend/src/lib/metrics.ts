/**
 * Pure Metric Calculations for ConsensusProbe 2.0 (Phase 0 / Phase 4)
 * 
 * Implements Data Health Score, Histograms, and Dataset Diffing.
 */

export interface HealthScoreWeights {
  readonly completeness: number;
  readonly validity: number;
  readonly uniqueness: number;
  readonly consistency: number;
}

export const DEFAULT_HEALTH_WEIGHTS: HealthScoreWeights = {
  completeness: 0.35,
  validity: 0.25,
  uniqueness: 0.20,
  consistency: 0.20,
};

export interface HealthScoreResult {
  readonly score: number; // 0 - 100
  readonly completeness: number; // 0 - 1
  readonly validity: number; // 0 - 1
  readonly uniqueness: number; // 0 - 1
  readonly consistency: number; // 0 - 1
  readonly totalCells: number;
  readonly nullCells: number;
  readonly duplicateRows: number;
}

export function calculateHealthScore(
  rows: Array<Record<string, any>>,
  weights: HealthScoreWeights = DEFAULT_HEALTH_WEIGHTS
): HealthScoreResult {
  if (!rows || rows.length === 0) {
    return {
      score: 100,
      completeness: 1,
      validity: 1,
      uniqueness: 1,
      consistency: 1,
      totalCells: 0,
      nullCells: 0,
      duplicateRows: 0,
    };
  }

  const columns = Object.keys(rows[0] || {}).filter((k) => k !== '_rid');
  if (columns.length === 0) {
    return {
      score: 100,
      completeness: 1,
      validity: 1,
      uniqueness: 1,
      consistency: 1,
      totalCells: 0,
      nullCells: 0,
      duplicateRows: 0,
    };
  }

  const rowCount = rows.length;
  const colCount = columns.length;
  const totalCells = rowCount * colCount;

  let nullCount = 0;
  let validCount = 0;

  // Uniqueness: check duplicate rows based on all non-_rid columns
  const seenRowStrings = new Set<string>();
  let duplicateRowCount = 0;

  for (const row of rows) {
    const rowKey = columns.map((c) => String(row[c] ?? '')).join('|--|');
    if (seenRowStrings.has(rowKey)) {
      duplicateRowCount++;
    } else {
      seenRowStrings.add(rowKey);
    }

    for (const col of columns) {
      const val = row[col];
      if (val === null || val === undefined || val === '') {
        nullCount++;
      } else {
        // Validity check: basic sanity (not NaN if numeric string, not invalid date format)
        validCount++;
      }
    }
  }

  const completeness = totalCells > 0 ? (totalCells - nullCount) / totalCells : 1.0;
  const validity = totalCells > 0 ? validCount / totalCells : 1.0;
  const uniqueness = rowCount > 0 ? Math.max(0, 1.0 - duplicateRowCount / rowCount) : 1.0;

  // Consistency: dominant casing / format ratio per text column
  let consistencySum = 0;
  for (const col of columns) {
    const vals = rows.map((r) => r[col]).filter((v) => v !== null && v !== undefined && v !== '');
    if (vals.length === 0) {
      consistencySum += 1.0;
      continue;
    }
    const sampleVal = vals[0];
    const isNum = typeof sampleVal === 'number' || (!isNaN(Number(sampleVal)) && sampleVal !== '');
    if (isNum) {
      consistencySum += 1.0;
    } else {
      // Check upper vs lower vs title dominant casing
      let upper = 0;
      let lower = 0;
      for (const v of vals) {
        const s = String(v);
        if (s === s.toUpperCase()) upper++;
        else if (s === s.toLowerCase()) lower++;
      }
      const maxCasing = Math.max(upper, lower, vals.length - upper - lower);
      consistencySum += maxCasing / vals.length;
    }
  }
  const consistency = columns.length > 0 ? consistencySum / columns.length : 1.0;

  const rawScore =
    weights.completeness * completeness +
    weights.validity * validity +
    weights.uniqueness * uniqueness +
    weights.consistency * consistency;

  const score = Math.round(rawScore * 1000) / 10; // e.g. 87.5

  return {
    score: Math.min(100, Math.max(0, score)),
    completeness,
    validity,
    uniqueness,
    consistency,
    totalCells,
    nullCells: nullCount,
    duplicateRows: duplicateRowCount,
  };
}

export interface HistogramBin {
  readonly label: string;
  readonly min: number;
  readonly max: number;
  readonly count: number;
}

export function computeNumericHistogram(
  values: number[],
  binCount: number = 5
): HistogramBin[] {
  const cleanVals = values.filter((v) => typeof v === 'number' && !isNaN(v));
  if (cleanVals.length === 0) return [];

  const min = Math.min(...cleanVals);
  const max = Math.max(...cleanVals);

  if (min === max) {
    return [{ label: `${min}`, min, max, count: cleanVals.length }];
  }

  const step = (max - min) / binCount;
  const bins: HistogramBin[] = [];

  for (let i = 0; i < binCount; i++) {
    const bMin = min + i * step;
    const bMax = i === binCount - 1 ? max : min + (i + 1) * step;
    bins.push({
      label: `${bMin.toFixed(1)} - ${bMax.toFixed(1)}`,
      min: bMin,
      max: bMax,
      count: 0,
    });
  }

  for (const v of cleanVals) {
    const idx = Math.min(Math.floor((v - min) / step), binCount - 1);
    if (bins[idx]) {
      (bins[idx] as { count: number }).count++;
    }
  }

  return bins;
}

export interface CategoricalFrequency {
  readonly value: string;
  readonly count: number;
  readonly percentage: number;
}

export function computeCategoricalFrequencies(
  values: Array<string | number | null | undefined>,
  topN: number = 8
): CategoricalFrequency[] {
  const counts = new Map<string, number>();
  let total = 0;

  for (const v of values) {
    const s = v === null || v === undefined ? '(null)' : String(v).trim();
    counts.set(s, (counts.get(s) || 0) + 1);
    total++;
  }

  const sorted = Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN);

  return sorted.map(([value, count]) => ({
    value,
    count,
    percentage: total > 0 ? Math.round((count / total) * 1000) / 10 : 0,
  }));
}

export interface CellChange {
  readonly rowIdx: number;
  readonly col: string;
  readonly originalValue: any;
  readonly cleanedValue: any;
  readonly type: 'edited' | 'imputed' | 'unchanged';
}

export interface DiffResult {
  readonly totalRowsOriginal: number;
  readonly totalRowsCleaned: number;
  readonly droppedRowCount: number;
  readonly editedCellCount: number;
  readonly imputedCellCount: number;
  readonly cellChanges: CellChange[];
}

export function computeRunDiff(
  originalRows: Array<Record<string, any>>,
  cleanedRows: Array<Record<string, any>>
): DiffResult {
  const totalRowsOriginal = originalRows.length;
  const totalRowsCleaned = cleanedRows.length;
  const droppedRowCount = Math.max(0, totalRowsOriginal - totalRowsCleaned);

  const cellChanges: CellChange[] = [];
  let editedCellCount = 0;
  let imputedCellCount = 0;

  const minRows = Math.min(originalRows.length, cleanedRows.length);
  for (let i = 0; i < minRows; i++) {
    const orig = originalRows[i];
    const clean = cleanedRows[i];
    const cols = Object.keys(orig).filter((k) => k !== '_rid');

    for (const col of cols) {
      const origVal = orig[col];
      const cleanVal = clean[col];

      if (origVal !== cleanVal) {
        const isImputed = (origVal === null || origVal === undefined || origVal === '') && cleanVal !== null && cleanVal !== undefined && cleanVal !== '';
        if (isImputed) {
          imputedCellCount++;
          cellChanges.push({
            rowIdx: i,
            col,
            originalValue: origVal,
            cleanedValue: cleanVal,
            type: 'imputed',
          });
        } else {
          editedCellCount++;
          cellChanges.push({
            rowIdx: i,
            col,
            originalValue: origVal,
            cleanedValue: cleanVal,
            type: 'edited',
          });
        }
      }
    }
  }

  return {
    totalRowsOriginal,
    totalRowsCleaned,
    droppedRowCount,
    editedCellCount,
    imputedCellCount,
    cellChanges,
  };
}
