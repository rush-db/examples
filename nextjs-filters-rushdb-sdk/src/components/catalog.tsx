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
import { db } from '@/db'
import { useRecords } from '@/hooks/use-records'
import { Loader } from 'lucide-react'

export default function Catalog() {
  const [currentRecord, setCurrentRecord] = useState()

  const { data: records, isLoading } = useRecords()

  if (isLoading) {
    return <Loader />
  }

  return (
    <div className="flex-1 p-6 pl-[272px] pt-[93px]">
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {records?.data?.map((product) => (
          <Card key={product.__id} className="flex flex-col shadow-none">
            <CardHeader>
              <CardTitle>{product.__label}</CardTitle>
              <CardDescription>{product.__id}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow">
              <p className="">{db.toInstance(product).date.toISOString()}</p>
            </CardContent>
            <CardFooter>
              <Button
                onClick={() => setCurrentRecord(product)}
                className="w-full"
              >
                Details
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
      {currentRecord && (
        <ProductModal
          product={currentRecord}
          isOpen={!!currentRecord}
          onClose={() => setCurrentRecord(null)}
        />
      )}
    </div>
  )
}
