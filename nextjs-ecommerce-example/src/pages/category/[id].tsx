import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { Layout } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { useCart } from '@/context/cart-context'
import {
  SearchQueryContextProvider,
  useSearchQuery,
} from '@/context/search-query-context'
import { useCategoryItems } from '@/hooks/use-category-items'
import { ShoppingCart } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

type Order = 'price-asc' | 'price-desc'

function CategoryInner() {
  const router = useRouter()
  const { addItem } = useCart()
  const idParam = router.query.id
  const categoryId = Array.isArray(idParam) ? idParam[0] : idParam
  const { data, isLoading, error } = useCategoryItems(categoryId as string)
  const category = data?.category
  const items = data?.items ?? []
  const { orderBy, setOrderBy } = useSearchQuery()

  const order: Order = React.useMemo(() => {
    if (orderBy?.price === 'asc') return 'price-asc'
    if (orderBy?.price === 'desc') return 'price-desc'
    return 'price-asc'
  }, [orderBy])

  if (!router.isReady || isLoading) {
    return <div className="p-4">Loading category…</div>
  }

  if (error || !category) {
    return <div className="p-4">Category not found.</div>
  }

  return (
    <Layout title={category.name} showFilters>
      <div className="space-y-4 min-h-0">
        <div className="flex items-center justify-end gap-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Order by</span>
            <Select
              value={order}
              onValueChange={(v) =>
                setOrderBy(
                  (v as Order) === 'price-asc'
                    ? { price: 'asc' }
                    : { price: 'desc' }
                )
              }
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Select order" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="price-asc">Price (low → high)</SelectItem>
                <SelectItem value="price-desc">Price (high → low)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          {items.map((p: any) => (
            <div key={p.id} className="border rounded-md p-4 space-y-2">
              <Link
                href={`/item/${p.id}`}
                className="font-medium text-lg hover:underline"
              >
                {p.name}
              </Link>
              <div className="text-muted-foreground">${p.price.toFixed(2)}</div>
              <Button
                onClick={() =>
                  addItem({ id: p.id, name: p.name, price: p.price, qty: 1 })
                }
              >
                Add to cart <ShoppingCart className="w-4 h-4 ml-2" />
              </Button>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  )
}

export default function CategoryPage() {
  const router = useRouter()
  const idParam = router.query.id
  const categoryId = Array.isArray(idParam) ? idParam[0] : idParam
  return (
    <>
      {router.isReady && categoryId ? (
        <SearchQueryContextProvider
          initialWhere={{ CATEGORY: { $id: categoryId as string } }}
          initialLabels={['ITEM']}
        >
          <CategoryInner />
        </SearchQueryContextProvider>
      ) : (
        <div className="p-4">Loading…</div>
      )}
    </>
  )
}
