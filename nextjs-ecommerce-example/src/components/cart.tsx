'use client'

import React from 'react'
import { useCart } from '@/context/cart-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useRouter } from 'next/router'
import { TrashIcon } from 'lucide-react'

export function Cart() {
  const { items, updateQty, removeItem, total } = useCart()
  const router = useRouter()

  return (
    <div className="space-y-4">
      <div className="text-lg font-semibold">Cart</div>

      {items.length === 0 ? (
        <div className="text-sm text-muted-foreground">Your cart is empty.</div>
      ) : (
        <div className="space-y-2">
          {items.map((i) => (
            <div
              key={i.id}
              className="flex items-center justify-between gap-2 border rounded-md p-2"
            >
              <div className="flex-1">
                <div className="font-medium">{i.name}</div>
                <div className="text-xs text-muted-foreground">
                  ${i.price.toFixed(2)} each
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  className="w-20"
                  type="number"
                  min={1}
                  value={i.qty}
                  onChange={(e) => {
                    const v = parseInt(e.target.value, 10)
                    updateQty(i.id, Math.max(1, Number.isNaN(v) ? 1 : v))
                  }}
                />
                <Button variant="ghost" onClick={() => removeItem(i.id)}>
                  <TrashIcon className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between py-4">
            <div className="font-medium">Total</div>
            <div className="font-semibold">${total.toFixed(2)}</div>
          </div>
          <div className="flex gap-2">
            <Button
              className="flex-1"
              onClick={() => router.push('/checkout')}
              disabled={items.length === 0}
            >
              Proceed to checkout
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
