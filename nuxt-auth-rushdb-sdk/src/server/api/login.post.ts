import {
  defineEventHandler,
  readBody,
  sendError,
  createError,
  setCookie,
} from 'h3';
import crypto from 'node:crypto';
import jwt from 'jsonwebtoken';
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

  const res = await UserModel.find({
    where: { username },
    limit: 1,
  });

  if (!res.data.length) {
    return sendError(
      event,
      createError({ statusCode: 401, statusMessage: 'Invalid credentials' })
    );
  }

  const user = res.data[0].data;
  const hash = crypto
    .createHmac('sha256', authSecret)
    .update(password)
    .digest('hex');

  if (hash !== user.passwordHash) {
    return sendError(
      event,
      createError({ statusCode: 401, statusMessage: 'Invalid credentials' })
    );
  }

  const token = jwt.sign({ username: user.username }, authSecret as string, {
    expiresIn: '1h',
  });

  setCookie(event, 'auth_token', token, {
    sameSite: 'lax',
    secure: true,
    path: '/',
    maxAge: 60 * 60,
  });

  return { success: true };
});
