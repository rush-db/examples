import RushDB from '@rushdb/javascript-sdk';

export const db = new RushDB(process.env.RUSHDB_API_TOKEN || '', {
  url: process.env.RUSHDB_URL || '',
});
