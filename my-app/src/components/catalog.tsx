'use client'

import { useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ProductModal } from '@/components/product-modal'
import { SearchQuery } from '@rushdb/javascript-sdk'
import { useQuery } from '@tanstack/react-query'
import { db } from '@/db'

function useRecords(query: SearchQuery = {}) {
  return useQuery({
    queryKey: ['posts', query],
    queryFn: () => db.records.find(query),
    select: (data) => data.data,
  })
}

export default function Catalog() {
  const records = useRecords()

  return (
    <div className="flex-1 p-6 pl-[272px] pt-[93px]">
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {records.data?.map((product) => (
          <Card key={product.__id} className="flex flex-col shadow-none">
            <CardHeader>
              <CardTitle>{product.__label}</CardTitle>
              <CardDescription>{product.__id}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow">
              <p className="">{db.toInstance(product).date.toISOString()}</p>
            </CardContent>
            <CardFooter>
              {/*<Button*/}
              {/*  onClick={() => setSelectedProduct(product)}*/}
              {/*  className="w-full"*/}
              {/*>*/}
              {/*  Details*/}
              {/*</Button>*/}
            </CardFooter>
          </Card>
        ))}
      </div>
      {/*{selectedProduct && (*/}
      {/*  <ProductModal*/}
      {/*    product={selectedProduct}*/}
      {/*    isOpen={!!selectedProduct}*/}
      {/*    onClose={() => setSelectedProduct(null)}*/}
      {/*  />*/}
      {/*)}*/}
    </div>
  )
}
