'use client'

import React from 'react'
import { SidebarLayout } from '@/components/sidebar-layout'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'

export default function SettingsPage() {
  return (
    <SidebarLayout
      breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Settings' }]}
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">
            Manage your CMS configuration and preferences
          </p>
        </div>

        {/* Site Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Site Settings</CardTitle>
            <CardDescription>
              Basic configuration for your website
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="site-name">Site Name</Label>
                <Input
                  id="site-name"
                  placeholder="My Awesome Site"
                  defaultValue="RushDB CMS"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="site-url">Site URL</Label>
                <Input
                  id="site-url"
                  placeholder="https://example.com"
                  defaultValue="https://localhost:3000"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="site-description">Site Description</Label>
              <Textarea
                id="site-description"
                placeholder="A brief description of your website"
                defaultValue="A modern CMS built with Next.js and RushDB"
              />
            </div>
          </CardContent>
        </Card>

        {/* Content Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Content Settings</CardTitle>
            <CardDescription>
              Configure content display and behavior
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="auto-save">Auto-save drafts</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically save content as you type
                </p>
              </div>
              <Switch id="auto-save" defaultChecked />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="show-drafts">Show drafts in public</Label>
                <p className="text-sm text-muted-foreground">
                  Display draft content on the public site
                </p>
              </div>
              <Switch id="show-drafts" />
            </div>
            <Separator />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="posts-per-page">Posts per page</Label>
                <Input
                  id="posts-per-page"
                  type="number"
                  placeholder="10"
                  defaultValue="10"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="excerpt-length">Excerpt length</Label>
                <Input
                  id="excerpt-length"
                  type="number"
                  placeholder="150"
                  defaultValue="150"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* SEO Settings */}
        <Card>
          <CardHeader>
            <CardTitle>SEO Settings</CardTitle>
            <CardDescription>
              Search engine optimization configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="meta-title">Default Meta Title</Label>
              <Input
                id="meta-title"
                placeholder="Your Site Title"
                defaultValue="RushDB CMS - Modern Content Management"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="meta-description">Default Meta Description</Label>
              <Textarea
                id="meta-description"
                placeholder="A brief description for search engines"
                defaultValue="A powerful and modern content management system built with Next.js and RushDB for fast, scalable content creation."
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="enable-sitemap">Generate sitemap</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically generate XML sitemap
                </p>
              </div>
              <Switch id="enable-sitemap" defaultChecked />
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end space-x-2">
          <Button variant="outline">Reset to defaults</Button>
          <Button>Save changes</Button>
        </div>
      </div>
    </SidebarLayout>
  )
}
