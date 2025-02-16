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
import { RecordModal } from '@/components/record-modal'
import { db } from '@/db'
import { useRecords } from '@/hooks/use-records'
import { Loader } from 'lucide-react'
import { DBRecord } from '@rushdb/javascript-sdk'

export default function RecordsGrid() {
  const [currentRecord, setCurrentRecord] = useState<DBRecord | undefined>()

  const { data: records, isLoading, isFetching } = useRecords()

  if (isLoading || isFetching) {
    return (
      <div className="flex-1 p-6 pl-80">
        <div className="pl-4 items-center grid w-full h-full animate-pulse text-center justify-center">
          <Loader className="animate-spin" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-6 pl-80">
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pl-4">
        {records?.data?.map((record) => (
          <Card key={record.__id} className="flex flex-col shadow-none">
            <CardHeader>
              <CardTitle>{record.__label}</CardTitle>
              <CardDescription>{record.__id}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow">
              <p className="">{db.toInstance(record).date.toISOString()}</p>
            </CardContent>
            <CardFooter>
              <Button
                onClick={() => setCurrentRecord(record)}
                className="w-full"
                variant="outline"
              >
                Details
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
      {currentRecord && (
        <RecordModal
          record={currentRecord}
          isOpen={!!currentRecord}
          onClose={() => setCurrentRecord(undefined)}
        />
      )}
    </div>
  )
}
