import { CMSModels } from '@/models'

declare module '@rushdb/javascript-sdk' {
  export interface Models extends CMSModels {}
}
