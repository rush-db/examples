import { AuthModels } from './shared/models/index';

declare module '@rushdb/javascript-sdk' {
  export interface Models extends AuthModels {}
}
