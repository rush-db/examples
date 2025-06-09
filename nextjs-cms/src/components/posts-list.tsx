'use client'

import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Plus,
  ArrowLeft,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Star,
  StarOff,
  Filter,
  X,
  Search,
  FileText,
} from 'lucide-react'
import { toast } from '@/hooks/use-toast'
import { PostModel } from '@/models'

export interface PostFilters {
  draft?: boolean
  author?: string
  search?: string
  featured?: boolean
  tag?: string
}

export interface PostListProps {
  // No config needed - this component is specific to posts
}

export function PostsList() {
  const [filters, setFilters] = useState<PostFilters>({})
  const router = useRouter()
  const queryClient = useQueryClient()

  // Get unique authors and tags for filter options
  const { data: allPosts } = useQuery({
    queryKey: ['posts-all'],
    queryFn: async () => {
      const data = await PostModel.find({ limit: 1000 })
      return data.data ?? []
    },
  })

  const authors = Array.from(
    new Set(
      allPosts
        ?.map((post: any) => post.data.author)
        .filter((author: string) => Boolean(author))
    )
  )

  const tags = Array.from(
    new Set(
      allPosts
        ?.flatMap((post: any) => post.data.tags || [])
        .filter((tag: string) => Boolean(tag))
    )
  )

  // Fetch posts with filters
  const { data: posts, isLoading: postsLoading } = useQuery({
    queryKey: ['posts', filters],
    queryFn: async () => {
      const where: any = {}

      // Apply filters
      if (filters.draft !== undefined) {
        where.draft = filters.draft
      }
      if (filters.author) {
        where.author = { $contains: filters.author }
      }
      if (filters.search) {
        where.$or = [
          { title: { $contains: filters.search } },
          { content: { $contains: filters.search } },
          { excerpt: { $contains: filters.search } },
        ]
      }
      if (filters.featured !== undefined) {
        where.featured = filters.featured
      }
      if (filters.tag) {
        where.tags = { $contains: filters.tag }
      }

      const result = await PostModel.find({
        where: Object.keys(where).length > 0 ? where : undefined,
        orderBy: { createdAt: 'desc' },
        limit: 100,
      })

      return result.data || []
    },
  })

  // Mutation for deleting posts
  const deleteMutation = useMutation({
    mutationFn: async (page: (typeof PostModel)['recordInstance']) => {
      await page.delete()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      toast({ title: 'Post deleted!' })
    },
    onError: (error: any) => {
      toast({
        title: `Failed to delete post: ${error.message}`,
        variant: 'destructive',
      })
    },
  })

  const handleEdit = (post: (typeof PostModel)['recordInstance']) => {
    router.push(`/posts/${post.id()}`)
  }

  const handleDelete = async (post: (typeof PostModel)['recordInstance']) => {
    if (confirm('Are you sure you want to delete this post?')) {
      deleteMutation.mutate(post)
    }
  }

  const toggleDraft = async (post: (typeof PostModel)['recordInstance']) => {
    const updateData = {
      draft: !post.data.draft,
      ...(post.data.draft === true && {
        publishedAt: new Date().toISOString(),
      }),
    }

    await post.update(updateData)
    queryClient.invalidateQueries({ queryKey: ['posts'] })
    toast({
      title: post.data.draft ? 'Post published!' : 'Post moved to draft',
    })
  }

  const toggleFeatured = async (post: any) => {
    const updateData = {
      featured: !post.data.featured,
    }

    await post.update(updateData)
    queryClient.invalidateQueries({ queryKey: ['posts'] })
    toast({
      title: post.data.featured ? 'Removed from featured' : 'Added to featured',
    })
  }

  const clearFilters = () => {
    setFilters({})
  }

  const getFilterCount = () => {
    let count = 0
    if (filters.draft !== undefined) count++
    if (filters.author) count++
    if (filters.search) count++
    if (filters.featured !== undefined) count++
    if (filters.tag) count++
    return count
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatReadTime = (readTime?: number) => {
    if (!readTime) return null
    return `${readTime} min read`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Posts</h1>
          <p className="text-muted-foreground">Manage your blog posts</p>
        </div>
        <Link href="/posts/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create Post
          </Button>
        </Link>
      </div>

      {/* Advanced Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Filter className="h-4 w-4 mr-2" />
              Filters
              {getFilterCount() > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {getFilterCount()}
                </Badge>
              )}
            </CardTitle>
            {getFilterCount() > 0 && (
              <Button variant="outline" size="sm" onClick={clearFilters}>
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="space-y-2">
              <Label>Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search posts..."
                  value={filters.search || ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      search: e.target.value || undefined,
                    })
                  }
                  className="pl-10"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={
                  filters.draft === undefined
                    ? 'all'
                    : filters.draft
                      ? 'draft'
                      : 'published'
                }
                onValueChange={(value) =>
                  setFilters({
                    ...filters,
                    draft:
                      value === 'all'
                        ? undefined
                        : value === 'draft'
                          ? true
                          : false,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="draft">Drafts</SelectItem>
                  <SelectItem value="published">Published</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Author Filter */}
            <div className="space-y-2">
              <Label>Author</Label>
              <Select
                value={filters.author || 'all'}
                onValueChange={(value) =>
                  setFilters({
                    ...filters,
                    author: value === 'all' ? undefined : value,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Authors" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Authors</SelectItem>
                  {authors.map((author) => (
                    <SelectItem key={author} value={author}>
                      {author}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Featured Filter */}
            <div className="space-y-2">
              <Label>Featured</Label>
              <Select
                value={
                  filters.featured === undefined
                    ? 'all'
                    : filters.featured
                      ? 'featured'
                      : 'not-featured'
                }
                onValueChange={(value) =>
                  setFilters({
                    ...filters,
                    featured:
                      value === 'all'
                        ? undefined
                        : value === 'featured'
                          ? true
                          : false,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="featured">Featured</SelectItem>
                  <SelectItem value="not-featured">Not Featured</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Tag Filter */}
            <div className="space-y-2">
              <Label>Tag</Label>
              <Select
                value={filters.tag || 'all'}
                onValueChange={(value) =>
                  setFilters({
                    ...filters,
                    tag: value === 'all' ? undefined : value,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Tags" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Tags</SelectItem>
                  {tags.map((tag) => (
                    <SelectItem key={tag} value={tag}>
                      {tag}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Posts List */}
      <div className="space-y-4">
        {postsLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : posts && posts.length > 0 ? (
          posts.map((post: any) => (
            <Card key={post.id()} className="transition-shadow hover:shadow-md">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold">
                        {post.data.title}
                      </h3>
                      <Badge
                        variant={post.data.draft ? 'secondary' : 'default'}
                      >
                        {post.data.draft ? 'Draft' : 'Published'}
                      </Badge>
                      {post.data.featured && (
                        <Badge variant="outline">Featured</Badge>
                      )}
                    </div>

                    <div className="text-sm text-muted-foreground space-y-1">
                      <p>Slug: /{post.data.slug}</p>
                      {post.data.author && <p>Author: {post.data.author}</p>}
                      {post.data.createdAt && (
                        <p>Created: {formatDate(post.data.createdAt)}</p>
                      )}
                      {post.data.readTime && (
                        <p>Read Time: {formatReadTime(post.data.readTime)}</p>
                      )}
                      {post.data.views !== undefined && (
                        <p>Views: {post.data.views}</p>
                      )}
                    </div>

                    {post.data.excerpt && (
                      <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                        {post.data.excerpt}
                      </p>
                    )}

                    {post.data.tags && post.data.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {post.data.tags.map((tag: string) => (
                          <Badge
                            key={tag}
                            variant="outline"
                            className="text-xs"
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleDraft(post)}
                      className="h-8 w-8 p-0"
                    >
                      {post.data.draft ? (
                        <Eye className="h-4 w-4" />
                      ) : (
                        <EyeOff className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleFeatured(post)}
                      className="h-8 w-8 p-0"
                    >
                      {post.data.featured ? (
                        <Star className="h-4 w-4 text-yellow-500" />
                      ) : (
                        <StarOff className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(post)}
                      className="h-8 w-8 p-0"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(post)}
                      className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-xl font-semibold mb-2">No posts found</p>
              <p className="text-muted-foreground mb-4">
                Create your first post to get started
              </p>
              <Link href="/posts/new">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Post
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
