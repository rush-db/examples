import { defineEventHandler, readBody } from 'h3';
import crypto from 'node:crypto';
import { useDb } from '~/composables/useDb';
import { UserModel } from '~/shared/models';

export default defineEventHandler(async (event) => {
  const { authSecret } = useRuntimeConfig(event);
  const db = useDb(event);

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

  const exists = await UserModel.find({
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
    await UserModel.create({
      username,
      passwordHash,
    });

    return { success: true };
  } catch (err: any) {
    return sendError(
      event,
      createError({ statusCode: 500, statusMessage: err.message })
    );
  }
});
