import React from 'react'
import Link from 'next/link'
import type { GetServerSideProps } from 'next'
import { Layout } from '@/components/layout'
import { SidebarLayout } from '@/components/sidebar-layout'
import { Button } from '@/components/ui/button'
import { useCart } from '@/context/cart-context'
import { Input } from '@/components/ui/input'
import { ShoppingCart } from 'lucide-react'

type Product = {
  id: string
  name: string
  price: number
  sku?: string
  description?: string
}

interface ItemPageProps {
  product: Product | null
}

export const getServerSideProps: GetServerSideProps<ItemPageProps> = async (
  ctx
) => {
  const { id } = ctx.params || {}
  const prodId = Array.isArray(id) ? id[0] : id
  const proto = (ctx.req.headers['x-forwarded-proto'] as string) || 'http'
  const host = ctx.req.headers.host
  const base = `${proto}://${host}`
  if (!prodId) return { notFound: true }
  try {
    const res = await fetch(`${base}/api/products/${prodId}`)
    if (!res.ok) return { notFound: true }
    const json = await res.json()
    return { props: { product: json.data ?? null } }
  } catch (e) {
    return { props: { product: null } }
  }
}

function ItemInner({ product }: ItemPageProps) {
  const { addItem } = useCart()
  const [qty, setQty] = React.useState(1)
  if (!product) return <div className="p-4">Item not found.</div>
  return (
    <SidebarLayout title={product.name}>
      <div className="flex-1 p-4 space-y-4">
        <div className="border rounded-md p-4 space-y-3 max-w-2xl">
          <div className="text-2xl font-semibold">{product.name}</div>
          {product.sku ? (
            <div className="text-muted-foreground">SKU: {product.sku}</div>
          ) : null}
          <div className="text-lg font-medium">${product.price.toFixed(2)}</div>
          {product.description ? (
            <p className="text-sm text-muted-foreground">
              {product.description}
            </p>
          ) : null}
          <div className="flex items-center gap-2">
            <Input
              className="w-24"
              type="number"
              min={1}
              value={qty}
              onChange={(e) =>
                setQty(Math.max(1, parseInt(e.target.value || '1', 10)))
              }
            />
            <Button
              onClick={() =>
                addItem({
                  id: product.id,
                  name: product.name,
                  price: product.price,
                  qty,
                })
              }
            >
              Add to cart <ShoppingCart className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    </SidebarLayout>
  )
}

export default function ItemPage(props: ItemPageProps) {
  return (
    <Layout>
      <ItemInner {...props} />
    </Layout>
  )
}
