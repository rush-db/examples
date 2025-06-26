import 'dotenv/config';

export const config = {
  port: +(process.env.PORT ?? 3007),
  rushdbToken: process.env.RUSHDB_API_TOKEN!,
  rushdbBaseUrl: process.env.RUSHDB_BASE_URL!,
  defaultModel: process.env.EMBEDDING_MODEL ?? 'Xenova/all-MiniLM-L6-v2',
};
