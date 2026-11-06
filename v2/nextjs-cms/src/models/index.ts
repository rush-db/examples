import { Model } from '@rushdb/javascript-sdk'

export const PostModel = new Model('Post', {
  title: { type: 'string', required: true },
  content: { type: 'string' },
  excerpt: { type: 'string' },
  slug: { type: 'string', required: true, uniq: true },
  draft: { type: 'boolean', default: true },
  featured: { type: 'boolean', default: false },
  publishedAt: { type: 'datetime' },
  createdAt: { type: 'datetime', default: () => new Date().toISOString() },
  updatedAt: { type: 'datetime', default: () => new Date().toISOString() },
  author: { type: 'string' },
  tags: { type: 'string', multiple: true },
  category: { type: 'string' },
  readTime: { type: 'number' },
  views: { type: 'number', default: 0 },
})

// Helper PostInstance type inferred from the model that represents a single post Record
export type PostInstance = (typeof PostModel)['recordInstance']

// Helper PostDraft type inferred from the model that represents a draft post Record
export type PostDraft = (typeof PostModel)['draft']

export const PageModel = new Model('Page', {
  title: { type: 'string', required: true },
  content: { type: 'string' },
  slug: { type: 'string', required: true, uniq: true },
  draft: { type: 'boolean', default: true },
  template: { type: 'string', default: 'default' },
  metaTitle: { type: 'string' },
  metaDescription: { type: 'string' },
  createdAt: { type: 'datetime', default: () => new Date().toISOString() },
  updatedAt: { type: 'datetime', default: () => new Date().toISOString() },
})

// Helper PageInstance type inferred from the model that represents a single page Record
export type PageInstance = (typeof PageModel)['recordInstance']

// Helper PageDraft type inferred from the model that represents a draft page Record
export type PageDraft = (typeof PageModel)['draft']

// Combined type for TypeScript module declaration
export type CMSModels = {
  Post: typeof PostModel.schema
  Page: typeof PageModel.schema
}
