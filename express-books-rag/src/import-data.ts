import path from 'path';
import fs from 'fs-extra';
import { RushDB } from '@rushdb/javascript-sdk';
import { config } from './config.js';
import { parse } from 'csv-parse/sync';

async function importData() {
  try {
    const db = new RushDB(config.rushdbToken, {
      url: config.rushdbBaseUrl,
    });

    const csvPath = path.resolve(process.cwd(), 'test_data', 'data.csv');
    const booksCsv = await fs.readFile(csvPath, { encoding: 'utf-8' });

    const records: any[] = parse(booksCsv, {
      columns: true,
      skip_empty_lines: true,
      trim: true,
    });

    console.log('✅ Parsed JSON:', records);

    await db.records.createMany({
      label: 'BOOK',
      data: records,
      options: { suggestTypes: true, convertNumericValuesToNumbers: true },
    });

    console.log('✅ Data imported successfully');
  } catch (e: any) {
    console.error('❌ Error importing data:', e.message);
    process.exit(1);
  }
}

if (import.meta.url.endsWith('/import-data.ts')) {
  importData().catch((err) => {
    console.error('❌ Error importing data:', err.message);
    process.exit(1);
  });
}
