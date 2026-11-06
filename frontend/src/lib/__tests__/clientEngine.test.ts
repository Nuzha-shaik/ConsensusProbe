import { describe, it, expect } from 'vitest';
import {
  parseCsvText,
  clientIngestFile,
  clientGetProfile,
  clientRunConsensus,
  clientClarify,
  clientExportCsv,
  clientExportPdf,
  clientExportXlsx,
} from '../clientEngine';

describe('clientEngine', () => {
  it('parses CSV text into rows properly', () => {
    const csv = 'colA,colB,colC\n1,hello,"quoted, comma"\n2,world,plain';
    const rows = parseCsvText(csv);
    expect(rows.length).toBe(3);
    expect(rows[0]).toEqual(['colA', 'colB', 'colC']);
    expect(rows[1][2]).toBe('quoted, comma');
  });

  it('profiles ingested dataset, runs consensus, clarifies, and exports PDF/XLSX', async () => {
    const sampleCsv = 'id,name,val\n1,Apple,10\n2,Banana,20\n3,,30';
    const file = new File([sampleCsv], 'sample.csv', { type: 'text/csv' });
    const ds = await clientIngestFile(file);
    expect(ds.rows).toBe(3);
    expect(ds.cols).toBe(3);

    const profile = clientGetProfile(ds.id);
    expect(profile.columns.length).toBe(3);
    const valCol = profile.columns.find((c) => c.name === 'val');
    expect(valCol?.dtype).toBe('float64');

    const cleanRes = clientRunConsensus(ds.id);
    expect(['needs_clarification', 'applied']).toContain(cleanRes.status);

    const clarifyRes = clientClarify(ds.id, 0);
    expect(clarifyRes.status).toBe('applied');
    expect(clarifyRes.consensus_score).toBe(0.0);

    // Test PDF export
    const pdfBlob = clientExportPdf(ds.id, {
      status: 'applied',
      consensusScore: 0.0,
      tauD: 0.0,
    });
    expect(pdfBlob.type).toBe('application/pdf');
    expect(pdfBlob.size).toBeGreaterThan(100);
    const pdfText = await pdfBlob.text();
    expect(pdfText.startsWith('%PDF-')).toBe(true);
    expect(pdfText.includes('CONSENSUSPROBE: DATA CLEANING AUDIT REPORT')).toBe(true);

    // Test XLSX export
    const xlsxBlob = clientExportXlsx(ds.id);
    expect(xlsxBlob.type).toContain('spreadsheetml');
    expect(xlsxBlob.size).toBeGreaterThan(10);

    // Test CSV export
    const csvBlob = clientExportCsv(ds.id);
    expect(csvBlob.type).toContain('text/csv');
  });

  it('correctly handles user table with duplicate John Smith and (blank) entries', async () => {
    const userCsv = `NAME,PHONE,EMAIL
John Smith,555-0199,john@gmail.com
John Smith,(blank),john@gmail.com
Alice Brown,555-0122,(blank)
Bob Taylor,(blank),(blank)`;

    const file = new File([userCsv], 'contacts.csv', { type: 'text/csv' });
    const ds = await clientIngestFile(file);
    expect(ds.rows).toBe(4);

    // Profile before cleaning should detect 4 missing/blank values
    const profBefore = clientGetProfile(ds.id);
    const phoneCol = profBefore.columns.find((c) => c.name === 'PHONE');
    const emailCol = profBefore.columns.find((c) => c.name === 'EMAIL');
    expect(phoneCol?.null_count).toBe(2);
    expect(emailCol?.null_count).toBe(2);

    // Running consensus must detect inter-plan ambiguity
    const consensusRes = clientRunConsensus(ds.id);
    expect(consensusRes.status).toBe('needs_clarification');
    expect(consensusRes.consensus_score).toBeGreaterThan(0.0);

    // Clarifying with Option 0 (merge duplicates & impute)
    const clarifyRes = clientClarify(ds.id, 0);
    expect(clarifyRes.status).toBe('applied');
    expect(clarifyRes.patch_summary?.deleted_rows).toBe(1);
    expect(clarifyRes.patch_summary?.edited_cells).toBeGreaterThanOrEqual(2);

    // Profile after cleaning: duplicate John Smith removed, rows=3, null_count=0
    const profAfter = clientGetProfile(ds.id);
    expect(profAfter.rows).toBe(3);
    const phoneAfter = profAfter.columns.find((c) => c.name === 'PHONE');
    const emailAfter = profAfter.columns.find((c) => c.name === 'EMAIL');
    expect(phoneAfter?.null_count).toBe(0);
    expect(emailAfter?.null_count).toBe(0);

    // Verified preview has non-blank values
    const records = profAfter.preview;
    expect(records.length).toBe(3);
    expect(records[0].NAME).toBe('John Smith');
    expect(records[0].PHONE).toBe('555-0199');
    expect(records[1].NAME).toBe('Alice Brown');
    expect(records[1].EMAIL).not.toBe('(blank)');
    expect(records[2].NAME).toBe('Bob Taylor');
    expect(records[2].PHONE).not.toBe('(blank)');
  });
});
