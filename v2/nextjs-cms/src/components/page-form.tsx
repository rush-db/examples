'use client'

import React, { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/router'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { MarkdownEditor } from '@/components/markdown-editor'
import { FormLayout } from '@/components/form-layout'
import { Save, Trash2 } from 'lucide-react'
import { toast } from '@/hooks/use-toast'
import { PageDraft, PageInstance, PageModel } from '@/models'

export interface PageFormProps {
  isEdit: boolean
  initialData?: PageInstance
  isLoading?: boolean
}

export function PageForm({ isEdit, initialData, isLoading }: PageFormProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { id } = router.query

  const [formData, setFormData] = useState<PageDraft>({
    title: '',
    content: '',
    slug: '',
    draft: true,
    template: 'default',
    metaTitle: '',
    updatedAt: '',
    createdAt: '',
    metaDescription: '',
    ...initialData?.data,
  })

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

  const createMutation = useMutation({
    mutationFn: async (data: PageDraft) => {
      const payload: PageDraft = {
        ...data,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
      return await PageModel.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pages'] })
      toast({ title: 'Page created successfully!' })
      router.push('/pages')
    },
    onError: (error: any) => {
      toast({
        title: `Failed to create page: ${error.message}`,
        variant: 'destructive',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (data: Partial<PageDraft>) => {
      if (!id || typeof id !== 'string') {
        throw new Error('Invalid page ID')
      }

      const updateData = {
        ...data,
        updatedAt: new Date().toISOString(),
      }
      return await PageModel.update(id, updateData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pages'] })
      queryClient.invalidateQueries({ queryKey: ['page', id] })
      toast({ title: 'Page updated successfully!' })
    },
    onError: (error: any) => {
      toast({
        title: `Failed to update page: ${error.message}`,
        variant: 'destructive',
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!id || typeof id !== 'string') {
        throw new Error('Invalid page ID')
      }
      await PageModel.deleteById(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pages'] })
      toast({ title: 'Page deleted successfully!' })
      router.push('/pages')
    },
    onError: (error: any) => {
      toast({
        title: `Failed to delete page: ${error.message}`,
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

    if (!formData.slug?.trim()) {
      toast({
        title: 'Slug is required',
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

  const handleDelete = () => {
    if (
      confirm(
        'Are you sure you want to delete this page? This action cannot be undone.'
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
        onClick={() => router.push('/pages')}
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
            ? 'Update Page'
            : 'Create Page'}
      </Button>
    </>
  )

  return (
    <FormLayout
      title={isEdit ? 'Edit Page' : 'Create New Page'}
      backUrl="/pages"
      backLabel="Back to Pages"
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
                  placeholder="Enter page title"
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
                  placeholder="page-slug"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="template">Template</Label>
              <Select
                value={formData.template}
                onValueChange={(value) =>
                  setFormData({ ...formData, template: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">Default</SelectItem>
                  <SelectItem value="landing">Landing Page</SelectItem>
                  <SelectItem value="full-width">Full Width</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Content Editor */}
        <MarkdownEditor
          value={formData.content}
          onChange={(content) => setFormData({ ...formData, content })}
          placeholder="Write your page content here..."
        />

        {/* SEO Settings */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>SEO Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="metaTitle">Meta Title</Label>
              <Input
                id="metaTitle"
                value={formData.metaTitle}
                onChange={(e) =>
                  setFormData({ ...formData, metaTitle: e.target.value })
                }
                placeholder="SEO title for search engines"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="metaDescription">Meta Description</Label>
              <Textarea
                id="metaDescription"
                value={formData.metaDescription}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    metaDescription: e.target.value,
                  })
                }
                placeholder="SEO description for search engines"
                rows={3}
              />
            </div>
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
          </CardContent>
        </Card>
      </form>
    </FormLayout>
  )
}
