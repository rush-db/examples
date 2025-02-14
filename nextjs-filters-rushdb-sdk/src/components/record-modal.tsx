import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { JsonViewer } from '@/components/ui/json-viewer'
import { DBRecord } from '@rushdb/javascript-sdk'
import { useRecordRelations } from '@/hooks/use-record-relations'
import { Loader } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'

interface RecordModalProps {
  record: DBRecord
  isOpen: boolean
  onClose: () => void
}

export function RecordModal({ record, isOpen, onClose }: RecordModalProps) {
  const { data: relations, isLoading } = useRecordRelations(record.__id)

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{record.__label}</DialogTitle>
          <DialogDescription>{record.__id}</DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[75vh]">
          <h3 className="text-base my-4">Record Data:</h3>
          <div className={'max-w-full overflow-auto'}>
            <JsonViewer data={record} />
          </div>
          {isLoading ? (
            <div className={'w-full p-4'}>
              <Loader className="animate-spin" />
            </div>
          ) : (
            <>
              <h3 className="text-base my-4">Record Relationships:</h3>
              <JsonViewer data={relations} />
            </>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
