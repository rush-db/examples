import { defineEventHandler, readBody } from 'h3';
import crypto from 'node:crypto';
import { RushDB } from '@rushdb/javascript-sdk';

export default defineEventHandler(async (event) => {
  const { rushdbToken, rushdbBaseUrl, authSecret } = useRuntimeConfig(event);
  const db = new RushDB(rushdbToken as string, {
    url: rushdbBaseUrl as string,
  });

  const { username, password } = await readBody<{
    username: string;
    password: string;
  }>(event);
  if (!username || !password) {
    return sendError(
      event,
      createError({
        statusCode: 400,
        statusMessage: 'Username & password required',
      })
    );
  }

  const exists = await db.records.find({
    labels: ['User'],
    where: { username },
    limit: 1,
  });

  if (exists.data.length) {
    return sendError(
      event,
      createError({ statusCode: 409, statusMessage: 'Username already exists' })
    );
  }

  const passwordHash = crypto
    .createHmac('sha256', authSecret)
    .update(password)
    .digest('hex');

  try {
    await db.records.create({
      label: 'User',
      data: { username, passwordHash },
    });

    return { success: true };
  } catch (err: any) {
    return sendError(
      event,
      createError({ statusCode: 500, statusMessage: err.message })
    );
  }
});
