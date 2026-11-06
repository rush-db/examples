'use client'

import React, { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/router'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { MarkdownEditor } from '@/components/markdown-editor'
import { FormLayout } from '@/components/form-layout'
import { Save, Trash2, Plus, X } from 'lucide-react'
import { toast } from '@/hooks/use-toast'
import { PostDraft, PostInstance, PostModel } from '@/models'

export interface PostFormProps {
  isEdit: boolean
  initialData?: PostInstance
  isLoading?: boolean
}

export function PostForm({ isEdit, initialData, isLoading }: PostFormProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { id } = router.query

  const [formData, setFormData] = useState<PostDraft>({
    title: '',
    content: '',
    excerpt: '',
    slug: '',
    draft: true,
    featured: false,
    author: '',
    tags: [],
    category: '',
    publishedAt: '',
    updatedAt: '',
    createdAt: '',
    readTime: 0,
    views: 0,
    ...initialData?.data,
  })

  const [newTag, setNewTag] = useState('')

  // Update form data when initialData changes
  useEffect(() => {
    if (initialData) {
      setFormData({ ...formData, ...initialData.data })
    }
  }, [initialData])

  // Auto-generate slug from title
  const generateSlug = (title: string = '') => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '')
  }

  // Auto-calculate reading time
  const calculateReadTime = (content: string) => {
    const words = content.trim().split(/\s+/).length
    return Math.ceil(words / 200) // 200 words per minute
  }

  const createMutation = useMutation({
    mutationFn: async (data: (typeof PostModel)['draft']) => {
      const payload: (typeof PostModel)['draft'] = {
        ...data,
        readTime: data.content ? calculateReadTime(data.content) : 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      // Only set publishedAt if not draft
      if (!data.draft) {
        payload.publishedAt = new Date().toISOString()
      }

      return await PostModel.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      toast({ title: 'Post created successfully!' })
      router.push('/posts')
    },
    onError: (error: any) => {
      toast({
        title: `Failed to create post: ${error.message}`,
        variant: 'destructive',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (data: Partial<PostDraft>) => {
      if (!id || typeof id !== 'string') {
        throw new Error('Invalid post ID')
      }

      const updateData = {
        ...data,
        readTime: data.content ? calculateReadTime(data.content) : undefined,
        updatedAt: new Date().toISOString(),
        // Set publishedAt if publishing for the first time
        ...(initialData?.data.draft &&
          !data.draft && { publishedAt: new Date().toISOString() }),
      }
      return await PostModel.update(id, updateData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post', id] })
      toast({ title: 'Post updated successfully!' })
    },
    onError: (error: any) => {
      toast({
        title: `Failed to update post: ${error.message}`,
        variant: 'destructive',
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!id || typeof id !== 'string') {
        throw new Error('Invalid post ID')
      }
      await PostModel.deleteById(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      toast({ title: 'Post deleted successfully!' })
      router.push('/posts')
    },
    onError: (error: any) => {
      toast({
        title: `Failed to delete post: ${error.message}`,
        variant: 'destructive',
      })
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.title?.trim()) {
      toast({
        title: 'Title is required',
        variant: 'destructive',
      })
      return
    }

    if (!formData.content?.trim()) {
      toast({
        title: 'Content is required',
        variant: 'destructive',
      })
      return
    }

    if (isEdit) {
      updateMutation.mutate(formData)
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleTitleChange = (title: string) => {
    const currentSlug =
      isEdit && initialData?.data
        ? generateSlug(initialData.data.title)
        : generateSlug(formData.title)

    setFormData({
      ...formData,
      title,
      slug:
        formData.slug === currentSlug || !formData.slug
          ? generateSlug(title)
          : formData.slug,
    })
  }

  const addTag = () => {
    if (newTag.trim() && !formData.tags?.includes(newTag.trim())) {
      setFormData({
        ...formData,
        tags: [...(formData.tags || []), newTag.trim()],
      })
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags?.filter((tag) => tag !== tagToRemove) || [],
    })
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag()
    }
  }

  const handleDelete = () => {
    if (
      confirm(
        'Are you sure you want to delete this post? This action cannot be undone.'
      )
    ) {
      deleteMutation.mutate()
    }
  }

  const mutation = isEdit ? updateMutation : createMutation
  const isSubmitting = mutation.isPending

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  const actions = (
    <>
      {isEdit && (
        <Button
          type="button"
          variant="destructive"
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        </Button>
      )}
      <Button
        type="button"
        variant="outline"
        onClick={() => router.push('/posts')}
      >
        Cancel
      </Button>
      <Button onClick={handleSubmit} disabled={isSubmitting}>
        <Save className="h-4 w-4 mr-2" />
        {isSubmitting
          ? isEdit
            ? 'Updating...'
            : 'Creating...'
          : isEdit
            ? 'Update Post'
            : 'Create Post'}
      </Button>
    </>
  )

  return (
    <FormLayout
      title={isEdit ? 'Edit Post' : 'Create New Post'}
      backUrl="/posts"
      backLabel="Back to Posts"
      actions={actions}
    >
      <form onSubmit={handleSubmit}>
        {/* Basic Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => handleTitleChange(e.target.value)}
                  placeholder="Enter post title"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="slug">Slug</Label>
                <Input
                  id="slug"
                  value={formData.slug}
                  onChange={(e) =>
                    setFormData({ ...formData, slug: e.target.value })
                  }
                  placeholder="post-slug"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="excerpt">Excerpt</Label>
              <Input
                id="excerpt"
                value={formData.excerpt}
                onChange={(e) =>
                  setFormData({ ...formData, excerpt: e.target.value })
                }
                placeholder="Brief description of the post"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="author">Author</Label>
                <Input
                  id="author"
                  value={formData.author}
                  onChange={(e) =>
                    setFormData({ ...formData, author: e.target.value })
                  }
                  placeholder="Author name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Input
                  id="category"
                  value={formData.category}
                  onChange={(e) =>
                    setFormData({ ...formData, category: e.target.value })
                  }
                  placeholder="Post category"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Content Editor */}
        <MarkdownEditor
          value={formData.content}
          onChange={(content) => setFormData({ ...formData, content })}
          placeholder="Write your post content here..."
        />

        {/* Tags */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Tags</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <Input
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyUp={handleKeyPress}
                placeholder="Add a tag"
                className="flex-1"
              />
              <Button type="button" onClick={addTag} size="sm">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {formData.tags && formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.tags.map((tag) => (
                  <Badge
                    key={tag}
                    variant="secondary"
                    className="flex items-center gap-1"
                  >
                    {tag}
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeTag(tag)}
                      className="h-auto p-0 hover:bg-transparent"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Settings */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Draft Status</Label>
                <p className="text-sm text-muted-foreground">
                  Save as draft or publish immediately
                </p>
              </div>
              <Switch
                checked={formData.draft}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, draft: checked })
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Featured Post</Label>
                <p className="text-sm text-muted-foreground">
                  Mark this post as featured
                </p>
              </div>
              <Switch
                checked={formData.featured}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, featured: checked })
                }
              />
            </div>
          </CardContent>
        </Card>
      </form>
    </FormLayout>
  )
}
