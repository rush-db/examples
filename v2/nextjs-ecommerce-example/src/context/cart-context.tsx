'use client'

import React, { createContext, useCallback, useContext, useMemo } from 'react'

export type CartItem = {
  id: string
  name: string
  price: number
  qty: number
}

type CartState = {
  items: CartItem[]
}

type CartContextValue = CartState & {
  addItem: (item: CartItem) => void
  removeItem: (id: string) => void
  updateQty: (id: string, qty: number) => void
  clearCart: () => void
  total: number
}

const CartContext = createContext<CartContextValue | null>(null)

function useCartInternal(): CartContextValue {
  const [items, setItems] = React.useState<CartItem[]>(() => {
    if (typeof window === 'undefined') return []
    try {
      const raw = window.localStorage.getItem('cart:v1')
      return raw ? (JSON.parse(raw) as CartItem[]) : []
    } catch {
      return []
    }
  })

  const addItem = useCallback((item: CartItem) => {
    setItems((prev) => {
      const idx = prev.findIndex((i) => i.id === item.id)
      if (idx >= 0) {
        const copy = [...prev]
        copy[idx] = { ...copy[idx], qty: copy[idx].qty + item.qty }
        return copy
      }
      return [...prev, item]
    })
  }, [])

  const removeItem = useCallback((id: string) => {
    setItems((prev) => prev.filter((i) => i.id !== id))
  }, [])

  const updateQty = useCallback((id: string, qty: number) => {
    setItems((prev) => prev.map((i) => (i.id === id ? { ...i, qty } : i)))
  }, [])

  const clearCart = useCallback(() => setItems([]), [])

  const total = useMemo(
    () => items.reduce((sum, i) => sum + i.price * i.qty, 0),
    [items]
  )

  React.useEffect(() => {
    try {
      window.localStorage.setItem('cart:v1', JSON.stringify(items))
    } catch {}
  }, [items])

  return { items, addItem, removeItem, updateQty, clearCart, total }
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const value = useCartInternal()
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used within CartProvider')
  return ctx
}
