import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { JsonViewer } from '@/components/ui/json-viewer'

interface Product {
  id: number
  name: string
  description: string
  price: number
  category: string
}

interface ProductModalProps {
  product: Product
  isOpen: boolean
  onClose: () => void
}

export function ProductModal({ product, isOpen, onClose }: ProductModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{product.__label}</DialogTitle>
          <DialogDescription>{product.__id}</DialogDescription>
        </DialogHeader>
        <div className={'max-w-full overflow-auto'}>
          <JsonViewer data={product} />
        </div>
      </DialogContent>
    </Dialog>
  )
}
