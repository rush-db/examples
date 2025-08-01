import { Model } from '@rushdb/javascript-sdk';

export const UserModel = new Model('User', {
  username: { type: 'string', required: true, uniq: true },
  passwordHash: { type: 'string', required: true },
});

// Combined type for TypeScript module declaration
export type AuthModels = {
  User: typeof UserModel.schema;
};
