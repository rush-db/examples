import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { JsonViewer } from '@/components/ui/json-viewer'
import { DBRecord } from '@rushdb/javascript-sdk'

interface RecordModalProps {
  record: DBRecord
  isOpen: boolean
  onClose: () => void
}

export function RecordModal({ record, isOpen, onClose }: RecordModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{record.__label}</DialogTitle>
          <DialogDescription>{record.__id}</DialogDescription>
        </DialogHeader>
        <div className={'max-w-full overflow-auto'}>
          <JsonViewer data={record} />
        </div>
      </DialogContent>
    </Dialog>
  )
}
