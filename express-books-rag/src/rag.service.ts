import { RushDB, SearchQuery, DBRecordInstance } from '@rushdb/javascript-sdk';
import { vectorize } from './text-processor.js';
import { config } from './config.js';

export type IndexStats = { processed: number; errors: number; skipped: number };

export function createRagService() {
  const db = new RushDB(config.rushdbToken, { url: config.rushdbBaseUrl });
  let modelName = config.defaultModel;

  function setModelByDimension(dim: number) {
    if (dim === 384) {
      modelName = 'Xenova/all-MiniLM-L6-v2';
    } else if (dim === 768) {
      modelName = 'Xenova/all-mpnet-base-v2';
    } else {
      console.warn(`No matching model for ${dim}, using default`);
      modelName = config.defaultModel;
    }
  }

  async function* paginate(
    filters: SearchQuery,
    batchSize = 100
  ): AsyncGenerator<DBRecordInstance> {
    let skip = 0;
    while (true) {
      const res = await db.records.find({
        limit: batchSize,
        ...filters
      });
      if (!res?.data.length) break;
      yield* res.data;
      if (res.data.length < batchSize) break;
      skip += res.data.length;
    }
  }

  async function indexRecords(
    filters: SearchQuery,
    field: string
  ): Promise<IndexStats> {
    const stats: IndexStats = { processed: 0, errors: 0, skipped: 0 };

    for await (const rec of paginate(filters)) {
      const { __id: id, __label: label, [field]: content } = rec.data;
      if (typeof content !== 'string' || !content) {
        stats.skipped++;
        continue;
      }
      try {
        const vec = await vectorize(content, modelName);
        await db.records.update({
          target: id,
          label,
          data: { embedding: vec },
          options: { suggestTypes: true, castNumberArraysToVectors: true },
        });
        stats.processed++;
      } catch {
        stats.errors++;
      }
    }

    return stats;
  }

  async function search(queryText: string, searchQuery: SearchQuery) {
    const vectorQuery = await vectorize(queryText, modelName);

    const where = {
      ...searchQuery.where,
      embedding: {
        $vector: {
          fn: 'gds.similarity.cosine',
          query: vectorQuery,
          threshold: 0.5,
        },
      },
    };

    const result = await db.records.find({
      orderBy: { score: 'desc' },
      ...searchQuery,
      where,
      aggregate: {
        score: {
          alias: '$record',
          field: 'embedding',
          fn: 'gds.similarity.cosine',
          query: vectorQuery,
        },
      },
      limit: searchQuery.limit ?? 5,
    });

    return {
      success: true,
      total: result.total,
      data: result.data.map((r) => r.data),
    };
  }

  return {
    setModelByDimension,
    indexRecords,
    search,
  };
}
