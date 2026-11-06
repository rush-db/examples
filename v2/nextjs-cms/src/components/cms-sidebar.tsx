'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from '@/components/ui/sidebar'
import {
  Database,
  FileText,
  Layout,
  Image,
  Settings,
  BarChart3,
} from 'lucide-react'
import { ThemeToggle } from '@/components/theme-toggle'

const navigation = [
  {
    title: 'Dashboard',
    url: '/',
    icon: BarChart3,
  },
  {
    title: 'Posts',
    url: '/posts',
    icon: FileText,
  },
  {
    title: 'Pages',
    url: '/pages',
    icon: Layout,
  },
  {
    title: 'Media',
    url: '/media',
    icon: Image,
  },
  {
    title: 'API',
    url: '/api-explorer',
    icon: Database,
  },
  {
    title: 'Settings',
    url: '/settings',
    icon: Settings,
  },
]

export function CMSSidebar() {
  const router = useRouter()

  return (
    <Sidebar variant="inset">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Database className="h-4 w-4" />
          </div>
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-semibold">RushDB CMS</span>
            <span className="truncate text-xs text-muted-foreground">
              Content Management
            </span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => {
                const isActive =
                  router.pathname === item.url ||
                  (item.url !== '/' && router.pathname.startsWith(item.url))

                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild isActive={isActive}>
                      <Link href={item.url}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarSeparator />
        <div className="flex items-center justify-between px-2 py-1">
          <div className="text-xs text-muted-foreground">Theme</div>
          <ThemeToggle />
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
