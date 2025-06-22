import RushDB from '@rushdb/javascript-sdk'

export const db = new RushDB(process.env.NEXT_PUBLIC_RUSHDB_API_TOKEN)
