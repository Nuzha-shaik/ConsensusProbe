import { describe, it, expect } from 'vitest';
import { parseCsvText, clientIngestFile, clientGetProfile, clientRunConsensus, clientClarify } from '../clientEngine';

describe('clientEngine', () => {
  it('parses CSV text into rows properly', () => {
    const csv = 'colA,colB,colC\n1,hello,"quoted, comma"\n2,world,plain';
    const rows = parseCsvText(csv);
    expect(rows.length).toBe(3);
    expect(rows[0]).toEqual(['colA', 'colB', 'colC']);
    expect(rows[1][2]).toBe('quoted, comma');
  });

  it('profiles ingested dataset and runs consensus', async () => {
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
  });
});
