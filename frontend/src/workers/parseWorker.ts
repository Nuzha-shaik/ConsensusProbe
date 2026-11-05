/**
 * Ingestion Parse Web Worker for ConsensusProbe 2.0
 * 
 * Performs streaming inspection, BOM/encoding sniffing, delimiter inference,
 * and first-20-rows preview extraction off the main thread.
 */

export interface ParsedCsvMetadata {
  encoding: string;
  delimiter: string;
  estimatedRows: number;
  columnCount: number;
  columns: string[];
  previewRows: Array<Record<string, string>>;
}

export interface ParseWorkerInput {
  fileChunk: ArrayBuffer;
  totalFileSize: number;
}

export type ParseWorkerOutput =
  | { success: true; metadata: ParsedCsvMetadata }
  | { success: false; error: string };

function detectEncodingAndText(buffer: ArrayBuffer): { encoding: string; text: string } {
  const bytes = new Uint8Array(buffer);

  // Check Byte Order Mark (BOM)
  if (bytes.length >= 3 && bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) {
    const decoder = new TextDecoder('utf-8');
    return { encoding: 'UTF-8 (with BOM)', text: decoder.decode(bytes.subarray(3)) };
  }
  if (bytes.length >= 2 && bytes[0] === 0xFE && bytes[1] === 0xFF) {
    const decoder = new TextDecoder('utf-16be');
    return { encoding: 'UTF-16BE', text: decoder.decode(bytes.subarray(2)) };
  }
  if (bytes.length >= 2 && bytes[0] === 0xFF && bytes[1] === 0xFE) {
    const decoder = new TextDecoder('utf-16le');
    return { encoding: 'UTF-16LE', text: decoder.decode(bytes.subarray(2)) };
  }

  // Fallback to UTF-8
  const decoder = new TextDecoder('utf-8', { fatal: false });
  return { encoding: 'UTF-8', text: decoder.decode(bytes) };
}

function sniffDelimiter(sampleLines: string[]): string {
  const candidates = [',', ';', '\t', '|'];
  if (sampleLines.length === 0) return ',';

  let bestDelimiter = ',';
  let bestScore = -1;

  for (const delim of candidates) {
    const counts = sampleLines.map((line) => line.split(delim).length - 1);
    const nonZero = counts.filter((c) => c > 0);
    if (nonZero.length === 0) continue;

    // Check consistency across lines
    const firstCount = counts[0];
    const isConsistent = counts.every((c) => c === firstCount);
    const score = (firstCount + 1) * (isConsistent ? 2 : 1);

    if (score > bestScore) {
      bestScore = score;
      bestDelimiter = delim;
    }
  }

  return bestDelimiter;
}

function parseCsvSimple(text: string, delimiter: string, maxPreview: number = 20) {
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length === 0) {
    return { columns: [], previewRows: [], estimatedRows: 0 };
  }

  const headerLine = lines[0];
  const columns = headerLine.split(delimiter).map((c) => c.replace(/^["']|["']$/g, '').trim());

  const previewRows: Array<Record<string, string>> = [];
  const limit = Math.min(lines.length, maxPreview + 1);

  for (let i = 1; i < limit; i++) {
    const parts = lines[i].split(delimiter);
    const row: Record<string, string> = {};
    for (let c = 0; c < columns.length; c++) {
      const colName = columns[c] || `col_${c}`;
      row[colName] = (parts[c] ?? '').replace(/^["']|["']$/g, '').trim();
    }
    previewRows.push(row);
  }

  return {
    columns,
    previewRows,
    estimatedRows: Math.max(0, lines.length - 1),
  };
}

self.onmessage = (e: MessageEvent<ParseWorkerInput>) => {
  try {
    const { fileChunk, totalFileSize } = e.data;
    const { encoding, text } = detectEncodingAndText(fileChunk);

    const lines = text.split(/\r?\n/).slice(0, 10);
    const delimiter = sniffDelimiter(lines);
    const parsed = parseCsvSimple(text, delimiter, 20);

    // Approximate total rows based on chunk ratio if chunk is partial
    let estimatedTotalRows = parsed.estimatedRows;
    if (fileChunk.byteLength < totalFileSize && fileChunk.byteLength > 0) {
      const ratio = totalFileSize / fileChunk.byteLength;
      estimatedTotalRows = Math.round(parsed.estimatedRows * ratio);
    }

    const metadata: ParsedCsvMetadata = {
      encoding,
      delimiter,
      estimatedRows: estimatedTotalRows,
      columnCount: parsed.columns.length,
      columns: parsed.columns,
      previewRows: parsed.previewRows,
    };

    self.postMessage({ success: true, metadata } satisfies ParseWorkerOutput);
  } catch (err: any) {
    self.postMessage({ success: false, error: err.message || 'Worker parse error' } satisfies ParseWorkerOutput);
  }
};
