import { RushDB } from "@rushdb/javascript-sdk";

// Initialize RushDB
export const db = new RushDB(import.meta.env.VITE_RUSHDB_API_TOKEN, {
  url: import.meta.env.VITE_RUSHDB_URL,
});
