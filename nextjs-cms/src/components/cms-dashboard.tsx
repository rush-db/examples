'use client'

import React from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useQuery } from '@tanstack/react-query'
import { Plus, FileText, Layout, Image } from 'lucide-react'
import Link from 'next/link'
import { PostModel, PageModel } from '@/models'

export function CMSDashboard() {
  // Fetch dashboard stats
  const { data: dashboardStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const [posts, pages] = await Promise.all([
        PostModel.find({ limit: 1000 }),
        PageModel.find({ limit: 1000 }),
      ])

      const postDrafts = posts.data?.filter((a) => a.data?.draft) || []
      const pageDrafts = pages.data?.filter((p) => p.data?.draft) || []

      return {
        posts: {
          total: posts.data?.length || 0,
          drafts: postDrafts.length,
          published: (posts.data?.length || 0) - postDrafts.length,
        },
        pages: {
          total: pages.data?.length || 0,
          drafts: pageDrafts.length,
          published: (pages.data?.length || 0) - pageDrafts.length,
        },
      }
    },
  })

  // Fetch recent content
  const { data: recentContent } = useQuery({
    queryKey: ['recent-content'],
    queryFn: async () => {
      const [posts, pages] = await Promise.all([
        PostModel.find({ limit: 5, orderBy: { createdAt: 'desc' } }),
        PageModel.find({ limit: 5, orderBy: { createdAt: 'desc' } }),
      ])

      const allContent = [
        ...(posts.data?.map((a) => ({
          ...a.data,
          __id: a.id(),
          type: 'post',
        })) || []),
        ...(pages.data?.map((p) => ({
          ...p.data,
          __id: p.id(),
          type: 'page',
        })) || []),
      ]

      return allContent
        .sort(
          (a, b) =>
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        )
        .slice(0, 5)
    },
  })

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Posts Stats */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Posts</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardStats?.posts.total || 0}
            </div>
            <div className="flex gap-2 mt-2">
              <Badge variant="outline">
                {dashboardStats?.posts.published || 0} published
              </Badge>
              <Badge variant="secondary">
                {dashboardStats?.posts.drafts || 0} drafts
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Pages Stats */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pages</CardTitle>
            <Layout className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardStats?.pages.total || 0}
            </div>
            <div className="flex gap-2 mt-2">
              <Badge variant="outline">
                {dashboardStats?.pages.published || 0} published
              </Badge>
              <Badge variant="secondary">
                {dashboardStats?.pages.drafts || 0} drafts
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Content */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Content</CardTitle>
          <CardDescription>Latest posts and pages created</CardDescription>
        </CardHeader>
        <CardContent>
          {recentContent && recentContent.length > 0 ? (
            <div className="space-y-3">
              {recentContent.map((item: any) => (
                <div
                  key={item.__id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{item.title}</h4>
                      <Badge variant="outline" className="text-xs">
                        {item.type}
                      </Badge>
                      {item.draft && (
                        <Badge variant="secondary" className="text-xs">
                          Draft
                        </Badge>
                      )}
                      {item.featured && (
                        <Badge variant="default" className="text-xs">
                          Featured
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Created {new Date(item.createdAt).toLocaleDateString()}
                      {item.author && ` by ${item.author}`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No content created yet</p>
              <Link href="/posts/new">
                <Button className="mt-2">Create your first post</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link href="/posts/new">
          <Button className="h-16 flex-col gap-2 w-full" variant="outline">
            <Plus className="h-5 w-5" />
            New Post
          </Button>
        </Link>
        <Link href="/pages/new">
          <Button className="h-16 flex-col gap-2 w-full" variant="outline">
            <Plus className="h-5 w-5" />
            New Page
          </Button>
        </Link>
        <Link href="/media">
          <Button className="h-16 flex-col gap-2 w-full" variant="outline">
            <Image className="h-5 w-5" />
            Upload Media
          </Button>
        </Link>
      </div>
    </div>
  )
}
