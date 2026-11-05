import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS } from '../IngestionDropzone';

describe('Ingestion Dropzone Constraints', () => {
  it('enforces 50 MB upload boundary', () => {
    expect(MAX_FILE_SIZE_BYTES).toBe(50 * 1024 * 1024);
  });

  it('allows CSV and XLSX extensions', () => {
    expect(ALLOWED_EXTENSIONS).toContain('.csv');
    expect(ALLOWED_EXTENSIONS).toContain('.xlsx');
    expect(ALLOWED_EXTENSIONS).not.toContain('.exe');
  });
});

describe('Sample Datasets and Ground Truth Integrity', () => {
  const samplesDir = path.resolve(__dirname, '../../../../public/samples');

  it('verifies retail_clean.csv exists and has clean headers', () => {
    const csvPath = path.join(samplesDir, 'retail_clean.csv');
    expect(fs.existsSync(csvPath)).toBe(true);

    const content = fs.readFileSync(csvPath, 'utf-8');
    const lines = content.trim().split(/\r?\n/);
    expect(lines.length).toBeGreaterThan(40);
    expect(lines[0]).toBe('transaction_id,product_name,category,price,quantity,sale_date');
  });

  it('verifies customers_contested.csv exists and contains injected ambiguities', () => {
    const csvPath = path.join(samplesDir, 'customers_contested.csv');
    expect(fs.existsSync(csvPath)).toBe(true);

    const content = fs.readFileSync(csvPath, 'utf-8');
    const lines = content.trim().split(/\r?\n/);
    expect(lines.length).toBeGreaterThan(45);
    expect(lines[0]).toBe('customer_id,customer_name,email,total_spend,support_tickets,signup_date');

    // Confirm injected ambiguity (null spend exists)
    const hasNullSpend = lines.some((l) => l.includes(',,'));
    expect(hasNullSpend).toBe(true);
  });

  it('verifies companion ground-truth JSON files exist with valid schema', () => {
    const cleanGtPath = path.join(samplesDir, 'retail_clean_ground_truth.json');
    const contestedGtPath = path.join(samplesDir, 'customers_contested_ground_truth.json');

    expect(fs.existsSync(cleanGtPath)).toBe(true);
    expect(fs.existsSync(contestedGtPath)).toBe(true);

    const cleanGt = JSON.parse(fs.readFileSync(cleanGtPath, 'utf-8'));
    const contestedGt = JSON.parse(fs.readFileSync(contestedGtPath, 'utf-8'));

    expect(cleanGt.expected_gate_decision).toBe('auto_approved');
    expect(contestedGt.expected_gate_decision).toBe('needs_human_clarification');
    expect(contestedGt.cell_ground_truth.length).toBeGreaterThan(0);
  });
});
