'use client'

import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/router'
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
import { Plus, Edit, Trash2, Eye, EyeOff, Filter } from 'lucide-react'

import { PageModel } from '@/models'

interface PageFilters {
  draft?: boolean
  search?: string
}

export function PagesList() {
  const [filters, setFilters] = useState<PageFilters>({})
  const router = useRouter()
  const queryClient = useQueryClient()

  // Fetch pages with filters
  const { data: pages, isLoading } = useQuery({
    queryKey: ['pages', filters],
    queryFn: async () => {
      const where: any = {}

      if (filters.draft !== undefined) {
        where.draft = filters.draft
      }
      if (filters.search) {
        where.title = { $contains: filters.search }
      }

      const result = await PageModel.find({
        where: Object.keys(where).length > 0 ? where : undefined,
        orderBy: { createdAt: 'desc' },
      })

      return result.data || []
    },
  })

  // Mutation for deleting pages
  const deleteMutation = useMutation({
    mutationFn: async (item: (typeof PageModel)['recordInstance']) => {
      await item.delete()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pages'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
    },
  })

  const handleCreate = () => {
    router.push('/pages/new')
  }

  const handleEdit = (item: (typeof PageModel)['recordInstance']) => {
    router.push(`/pages/${item.id()}`)
  }

  const handleDelete = async (item: (typeof PageModel)['recordInstance']) => {
    if (confirm('Are you sure you want to delete this page?')) {
      deleteMutation.mutate(item)
    }
  }

  const toggleDraft = async (item: (typeof PageModel)['recordInstance']) => {
    await item.update({ draft: !item.data.draft })
    queryClient.invalidateQueries({ queryKey: ['pages'] })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Pages</h1>
          <p className="text-muted-foreground">
            Manage your website pages and templates
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Create Page
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Search</Label>
              <Input
                placeholder="Search pages..."
                value={filters.search || ''}
                onChange={(e) =>
                  setFilters({ ...filters, search: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={filters.draft?.toString() || 'all'}
                onValueChange={(value) =>
                  setFilters({
                    ...filters,
                    draft: value === 'all' ? undefined : value === 'true',
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="true">Drafts</SelectItem>
                  <SelectItem value="false">Published</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pages List */}
      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <div className="grid gap-4">
          {pages?.map((page) => (
            <Card key={page.id()}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold">
                        {page.data.title}
                      </h3>
                      <Badge
                        variant={page.data.draft ? 'secondary' : 'default'}
                      >
                        {page.data.draft ? 'Draft' : 'Published'}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground space-y-1">
                      <p>Slug: /{page.data.slug}</p>
                      <p>Template: {page.data.template || 'default'}</p>
                      {page.data.createdAt && (
                        <p>
                          Created:{' '}
                          {new Date(page.data.createdAt).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    {page.data.content && (
                      <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                        {page.data.content}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleDraft(page)}
                      className="h-8 w-8 p-0"
                    >
                      {page.data.draft ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(page)}
                      className="h-8 w-8 p-0"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(page)}
                      className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )) || (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No pages found</p>
              <Button onClick={handleCreate} className="mt-2">
                Create your first page
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
