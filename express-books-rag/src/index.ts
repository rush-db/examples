import dotenv from 'dotenv';
dotenv.config();

import express, { Request, Response } from 'express';
import { config } from './config.js';
import { createRagService } from './rag.service.js';
import { SearchQuery } from '@rushdb/javascript-sdk';

const app = express();
const port = config.port;

app.use(express.json());

const { setModelByDimension, indexRecords, search } = createRagService();

app.post('/index', async (req: Request, res: Response) => {
  const { field, vectorDimension, ...query } = req.body as {
    field?: string;
    vectorDimension?: number;
  } & SearchQuery;

  if (!field) {
    return res.status(400).json({ error: 'Missing "field"' });
  }

  if (vectorDimension !== undefined) {
    setModelByDimension(vectorDimension);
  }

  try {
    const { processed, errors, skipped } = await indexRecords(query, field);

    res.json({
      message: 'Indexing complete',
      processed,
      errors,
      skipped,
    });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/search', async (req: Request, res: Response) => {
  const { query, vectorDimension, ...rest } = req.body as {
    query?: string;
    vectorDimension?: number;
  } & SearchQuery;

  if (!query) {
    return res.status(400).json({ error: 'Missing "query"' });
  }

  if (vectorDimension !== undefined) {
    setModelByDimension(vectorDimension);
  }

  try {
    const results = await search(query, { ...rest });
    res.json(results);
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

app.listen(port, () => {
  console.log(`[Server]: Server is running at http://localhost:${port}`);
});
