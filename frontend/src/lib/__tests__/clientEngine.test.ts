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

  it('enforces Rule 1: Never synthesize identifying fields without a matching row (blank stays blank)', async () => {
    const userCsv = `NAME,PHONE,EMAIL
John Smith,555-0199,john@gmail.com
John Smith,(blank),john@gmail.com
Alice Brown,555-0122,(blank)
Bob Taylor,(blank),(blank)`;

    const file = new File([userCsv], 'contacts.csv', { type: 'text/csv' });
    const ds = await clientIngestFile(file);
    expect(ds.rows).toBe(4);

    const clarifyRes = clientClarify(ds.id, 0);
    expect(clarifyRes.status).toBe('applied');
    expect(clarifyRes.patch_summary?.deleted_rows).toBe(2);

    const profAfter = clientGetProfile(ds.id);
    expect(profAfter.rows).toBe(2);
    const records = profAfter.preview;
    expect(records[0].NAME).toBe('John Smith');
    expect(records[0].PHONE).toBe('555-0199');
    expect(records[0].EMAIL).toBe('john@gmail.com');
    expect(records[1].NAME).toBe('Alice Brown');
    expect(records[1].PHONE).toBe('555-0122');
    // Rule 1: Alice Brown has no other row in this file, so email STAYS BLANK without fabrication!
    expect(records[1].EMAIL).toBe('');
    expect(records.some((r) => r.NAME === 'Bob Taylor')).toBe(false);
  });

  it('enforces Rules 1-4 on full multi-row dataset: cross-row merges, blank preservation, invalid flagging, traceability', async () => {
    const fullCsv = `NAME,PHONE,EMAIL
John Smith,555-0199,john.smith@example.com
John Smith,Unknown,john.smith@example.com
Alice Brown,555-0122,Unknown
Bob Taylor,Unknown,Unknown
alice brown,5550122,alice.brown@example.com
David Wilson,555-0144,david.wilson@example.com
Sarah Johnson,,sarah.johnson@example.com
Michael Davis,555-0188,MICHAEL.DAVIS@EXAMPLE.COM
John Smith,555-0199,john.smith@example.com
Emily Clark,123,emily.clark@example
Robert White,Unknown,robert.white@example.com
  Alice Brown ,555-0122,alice.brown@example.com
James Miller,555-0166, james.miller@example.com 
Sophia Garcia,N/A,sophia.garcia@example.com
Daniel Lee,555-0177,Unknown`;

    const file = new File([fullCsv], 'full_contacts.csv', { type: 'text/csv' });
    const ds = await clientIngestFile(file);
    expect(ds.rows).toBe(15);

    const clarifyRes = clientClarify(ds.id, 0);
    expect(clarifyRes.status).toBe('applied');

    const profAfter = clientGetProfile(ds.id);
    const records = profAfter.preview;
    // Exactly 10 kept rows (Bob Taylor pruned, 2 duplicate John Smiths merged, 2 duplicate Alice Browns merged)
    expect(records.length).toBe(10);

    // Rule 2: Alice Brown merged email from row 5!
    const alice = records.find((r) => /alice brown/i.test(r.NAME));
    expect(alice?.EMAIL).toBe('alice.brown@example.com');
    expect(alice?.PHONE).toBe('555-0122');

    // Rule 1: Daniel Lee has no other row -> email STAYS BLANK! Never synthesized!
    const daniel = records.find((r) => /daniel lee/i.test(r.NAME));
    expect(daniel?.PHONE).toBe('555-0177');
    expect(daniel?.EMAIL).toBe('');

    // Rule 1: Sarah Johnson, Robert White, Sophia Garcia have no duplicate phones -> phone STAYS BLANK!
    const sarah = records.find((r) => /sarah johnson/i.test(r.NAME));
    expect(sarah?.PHONE).toBe('');
    expect(sarah?.EMAIL).toBe('sarah.johnson@example.com');

    // Rule 4: Invalid values (Emily Clark 123, emily.clark@example) are flagged!
    expect(clarifyRes.patch_summary?.flagged_rows).toBeGreaterThanOrEqual(1);

    // Export PDF verification
    const pdfBlob = clientExportPdf(ds.id);
    expect(pdfBlob.size).toBeGreaterThan(100);
    const pdfText = await pdfBlob.text();
    expect(pdfText.includes('Traceability Invariant Verified')).toBe(true);
    expect(pdfText.includes('Zero Fabrications')).toBe(true);

    // Export CSV verification
    const csvBlob = clientExportCsv(ds.id);
    const csvText = await csvBlob.text();
    expect(csvText.includes('Unknown')).toBe(false);
    expect(csvText.includes('daniel.lee@example.com')).toBe(false); // Verified NOT synthesized!
    expect(csvText.includes('alice.brown@example.com')).toBe(true); // Verified merged from matching row!
  });
});
