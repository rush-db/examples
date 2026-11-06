import React from 'react'
import Link from 'next/link'
import type { GetServerSideProps } from 'next'
import { Layout } from '@/components/layout'

type Category = {
  id: string
  name: string
  description?: string
  itemsCount?: number
}

interface HomeProps {
  categories: Category[]
}

export const getServerSideProps: GetServerSideProps<HomeProps> = async (
  ctx
) => {
  const proto = (ctx.req.headers['x-forwarded-proto'] as string) || 'http'
  const host = ctx.req.headers.host
  const base = `${proto}://${host}`

  try {
    const res = await fetch(`${base}/api/categories`)
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }
    const json = await res.json()
    return { props: { categories: json.data ?? [] } }
  } catch (e) {
    return { props: { categories: [] } }
  }
}

export default function Home({ categories }: HomeProps) {
  return (
    <Layout title="Categories">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map((c) => (
          <Link
            key={c.id}
            href={`/category/${c.id}`}
            className="border rounded-md p-4 hover:bg-accent"
          >
            <div className="font-semibold">{c.name}</div>
            <div className="text-sm text-muted-foreground">{c.description}</div>
            {c.itemsCount && (
              <div className="text-sm text-muted-foreground border-t mt-2 pt-2">
                {c.itemsCount} items
              </div>
            )}
          </Link>
        ))}
      </div>
    </Layout>
  )
}
