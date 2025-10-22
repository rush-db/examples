import React, { useEffect, useState } from 'react'
import { Layout } from '@/components/layout'
import { SidebarLayout } from '@/components/sidebar-layout'
import { useCart } from '@/context/cart-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAddresses, type Address } from '@/hooks/use-addresses'

type DeliveryType = 'standard' | 'express'

export default function CheckoutPage() {
  return (
    <Layout>
      <SidebarLayout title="Checkout" showCart={false}>
        <CheckoutInner />
      </SidebarLayout>
    </Layout>
  )
}

function CheckoutInner() {
  const { items, total, clearCart } = useCart()
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const [city, setCity] = useState('')
  const [zip, setZip] = useState('')
  const [country, setCountry] = useState('')
  const [delivery, setDelivery] = useState<DeliveryType>('standard')
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [addressMode, setAddressMode] = useState<'new' | 'existing'>('new')
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(
    null
  )
  const { data: addresses = [], isLoading: loadingAddresses } = useAddresses()

  const canSubmit =
    items.length > 0 &&
    name &&
    (addressMode === 'existing'
      ? Boolean(selectedAddressId)
      : Boolean(address && city && zip && country))

  // Prefill from last used address (localStorage) or a demo default on first visit
  useEffect(() => {
    try {
      const raw = localStorage.getItem('checkout:address')
      if (raw) {
        const saved = JSON.parse(raw) as {
          name?: string
          address?: string
          city?: string
          zip?: string
          country?: string
          delivery?: DeliveryType
        }
        if (saved.name) setName(saved.name)
        if (saved.address) setAddress(saved.address)
        if (saved.city) setCity(saved.city)
        if (saved.zip) setZip(saved.zip)
        if (saved.country) setCountry(saved.country)
        if (saved.delivery) setDelivery(saved.delivery)
        return
      }
      // Demo defaults if nothing saved yet
      setName('Jane Doe')
      setAddress('1600 Amphitheatre Parkway')
      setCity('Mountain View')
      setZip('94043')
      setCountry('USA')
    } catch {}
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setSubmitting(true)
    setMessage(null)
    try {
      const payload = {
        createdAt: new Date().toISOString(),
        status: 'NEW',
        delivery: {
          method: delivery === 'express' ? 'Express' : 'Standard',
          status: 'pending',
          ...(addressMode === 'existing'
            ? { addressId: selectedAddressId }
            : {
                address: {
                  city,
                  street: address,
                  postalCode: zip,
                  country,
                },
              }),
        },
        order_item: items.map((i) => ({
          id: i.id,
          name: i.name,
          price: i.price,
          qty: i.qty,
          subtotal: i.price * i.qty,
        })),
        total,
      }

      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const json = await res.json()
      if (!res.ok || !json.ok)
        throw new Error(json.message || 'Checkout failed')
      setMessage('Order placed successfully!')
      clearCart()
    } catch (err: any) {
      setMessage(err?.message || 'Failed to place order')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Shipping Address</h2>
        <Tabs
          value={addressMode}
          onValueChange={(v) => setAddressMode(v as 'new' | 'existing')}
          className="w-full mb-4"
        >
          <TabsList>
            <TabsTrigger value="new">New address</TabsTrigger>
            <TabsTrigger value="existing">My addresses</TabsTrigger>
          </TabsList>

          <TabsContent value="new">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm">Full Name</label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="md:col-span-2">
                <label className="text-sm">Address</label>
                <Input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm">City</label>
                <Input value={city} onChange={(e) => setCity(e.target.value)} />
              </div>
              <div>
                <label className="text-sm">ZIP / Postal Code</label>
                <Input value={zip} onChange={(e) => setZip(e.target.value)} />
              </div>
              <div className="md:col-span-2">
                <label className="text-sm">Country</label>
                <Input
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="existing">
            <div className="space-y-3">
              {loadingAddresses && (
                <div className="text-sm">Loading addresses…</div>
              )}
              {!loadingAddresses && addresses.length === 0 && (
                <div className="text-sm text-muted-foreground">
                  No saved addresses found.
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {addresses.map((a) => (
                  <label
                    key={a.id}
                    className={`border rounded p-3 flex gap-3 items-start cursor-pointer ${selectedAddressId === a.id ? 'border-primary ring-1 ring-primary' : ''}`}
                  >
                    <input
                      type="radio"
                      name="address"
                      checked={selectedAddressId === a.id}
                      onChange={() => setSelectedAddressId(a.id)}
                      className="mt-1"
                    />
                    <div className="text-sm">
                      <div className="font-medium">{a.street}</div>
                      <div className="text-muted-foreground">
                        {a.city}, {a.postalCode}, {a.country}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Delivery</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label
            className={`border rounded p-3 flex gap-3 items-start cursor-pointer ${delivery === 'standard' ? 'border-primary ring-1 ring-primary' : ''}`}
          >
            <input
              type="radio"
              name="delivery"
              value="standard"
              checked={delivery === 'standard'}
              onChange={() => setDelivery('standard')}
              className="mt-1"
            />
            <div className="text-sm">
              <div className="font-medium">Standard</div>
              <div className="text-muted-foreground">3-5 business days</div>
            </div>
          </label>
          <label
            className={`border rounded p-3 flex gap-3 items-start cursor-pointer ${delivery === 'express' ? 'border-primary ring-1 ring-primary' : ''}`}
          >
            <input
              type="radio"
              name="delivery"
              value="express"
              checked={delivery === 'express'}
              onChange={() => setDelivery('express')}
              className="mt-1"
            />
            <div className="text-sm">
              <div className="font-medium">Express</div>
              <div className="text-muted-foreground">1-2 business days</div>
            </div>
          </label>
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Order Summary</h2>
        <div className="text-sm text-muted-foreground">
          {items.length === 0 ? 'Your cart is empty.' : `${items.length} items`}
        </div>
        <div className="font-medium">Total: ${total.toFixed(2)}</div>
      </section>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={!canSubmit || submitting}>
          {submitting ? 'Placing order…' : 'Place order'}
        </Button>
        {message ? (
          <span className="text-sm text-muted-foreground">{message}</span>
        ) : null}
      </div>
    </form>
  )
}
