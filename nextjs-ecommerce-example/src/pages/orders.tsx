import React from 'react'
import { SidebarLayout } from '@/components/sidebar-layout'
import { useFetchQuery } from '@/hooks/use-fetch-query'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { idToDate } from '@rushdb/javascript-sdk'

interface Order {
  id: string
  createdAt?: string
  status?: string
  total?: number
  delivery?: {
    method?: 'Express' | 'Standard'
    status?: string
    address?: {
      city?: string
      street?: string
      postalCode?: string
      country?: string
    }
  }
}

export default function OrdersPage() {
  const { data, isLoading, error } = useFetchQuery<{
    ok: boolean
    data: Order[]
  }>({
    fetcher: async (signal: AbortSignal) => {
      const res = await fetch('/api/orders', { signal })
      if (!res.ok) throw new Error('Failed to load orders')
      return res.json()
    },
    deps: [],
  })

  return (
    <SidebarLayout title="Orders" showFilters={false} showCart={false}>
      <div className="max-w-4xl mx-auto w-full">
        {isLoading && (
          <p className="text-sm text-muted-foreground">Loading orders…</p>
        )}
        {error && (
          <p className="text-sm text-destructive">
            {(error as any)?.message || 'Failed to load orders'}
          </p>
        )}
        {!isLoading && !error && (!data?.data || data.data.length === 0) && (
          <p className="text-sm text-muted-foreground">No orders yet.</p>
        )}

        <div className="space-y-4">
          {data?.data?.map((order) => (
            <Card key={order.id} className="w-full">
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">Order #{order.id}</CardTitle>
                {/* <CardTitle className="text-base">
                  Order | {idToDate(order.id).toISOString()}
                </CardTitle> */}
                {order.status ? (
                  <Badge
                    variant={order.status === 'Paid' ? 'default' : 'secondary'}
                  >
                    {order.status}
                  </Badge>
                ) : null}
              </CardHeader>
              <CardContent className="text-sm">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <div className="text-muted-foreground">Created</div>
                    <div>
                      {order.createdAt
                        ? new Date(order.createdAt).toLocaleString()
                        : '—'}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Delivery</div>
                    <div>
                      {order.delivery?.method || '—'}
                      {order.delivery?.status ? (
                        <span className="text-muted-foreground">
                          {' '}
                          · {order.delivery.status}
                        </span>
                      ) : null}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Total</div>
                    <div>
                      {typeof order.total === 'number'
                        ? `$${order.total.toFixed(2)}`
                        : '—'}
                    </div>
                  </div>
                </div>
                {order.delivery?.address ? (
                  <>
                    <Separator className="my-3" />
                    <div className="text-muted-foreground mb-1">
                      Shipping address
                    </div>
                    <div>
                      {order.delivery.address.street
                        ? order.delivery.address.street + ', '
                        : ''}
                      {order.delivery.address.city
                        ? order.delivery.address.city + ', '
                        : ''}
                      {order.delivery.address.postalCode
                        ? order.delivery.address.postalCode + ', '
                        : ''}
                      {order.delivery.address.country || ''}
                    </div>
                  </>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </SidebarLayout>
  )
}
