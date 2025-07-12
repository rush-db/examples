import { defineEventHandler, getCookie, createError } from 'h3';
import jwt from 'jsonwebtoken';
import { useDb } from '~/composables/useDb';
import { UserModel } from '~/shared/models';

export default defineEventHandler(async (event) => {
  const { authSecret } = useRuntimeConfig(event);
  const db = useDb(event);

  const token = getCookie(event, 'auth_token');
  if (!token)
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' });

  let payload: any;
  try {
    payload = jwt.verify(token, authSecret as string);
  } catch {
    throw createError({ statusCode: 401, statusMessage: 'Invalid token' });
  }

  const res = await UserModel.find({});

  const users = res.data.map((r) => r.data.username);

  return {
    users,
    current: payload.username,
  };
});
