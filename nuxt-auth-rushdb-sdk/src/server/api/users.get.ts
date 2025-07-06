import { defineEventHandler, getCookie, createError } from 'h3';
import jwt from 'jsonwebtoken';
import { RushDB } from '@rushdb/javascript-sdk';

export default defineEventHandler(async (event) => {
  const { rushdbToken, rushdbBaseUrl, authSecret } = useRuntimeConfig(event);

  const token = getCookie(event, 'auth_token');
  if (!token)
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' });

  let payload: any;
  try {
    payload = jwt.verify(token, authSecret as string);
  } catch {
    throw createError({ statusCode: 401, statusMessage: 'Invalid token' });
  }

  const db = new RushDB(rushdbToken as string, {
    url: rushdbBaseUrl as string,
  });

  const res = await db.records.find({
    labels: ['User'],
  });

  const users = res.data.map((r) => (r.data as any).username);
  return {
    users,
    current: payload.username,
  };
});
