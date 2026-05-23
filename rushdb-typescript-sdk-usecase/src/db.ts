/**
 * Shared RushDB instance for the application
 */
import RushDB from '@rushdb/javascript-sdk';
import { config } from 'dotenv';

config();

const db = new RushDB(process.env.RUSHDB_API_KEY!, {
  url: process.env.RUSHDB_URL,
});

export default db;
